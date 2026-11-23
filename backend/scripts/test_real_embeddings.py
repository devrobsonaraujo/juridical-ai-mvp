"""Teste de integração real: embeddings E5 + PostgreSQL, sem Groq ou upload.

Execute a partir de backend/: python scripts/test_real_embeddings.py
Requer TEST_OWNER_A e TEST_OWNER_B com UUIDs existentes em auth.users.
"""
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.services import postgres_vector_service as storage
from app.services.embedding_service import get_embedding_service


def require_owner(name):
    value = os.getenv(name, '').strip()
    if not value:
        raise ValueError(f'{name} não definido. Configure no PowerShell.')
    return str(uuid.UUID(value))


def segment(text):
    return [{'start': 0.0, 'end': 18.0, 'text': text}]


def delete_test_media(media_ids):
    if not media_ids:
        return
    with storage._connection() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM public.media_files WHERE id = ANY(%s::uuid[]) RETURNING id', (media_ids,))
            removed = len(cur.fetchall())
    if removed != len(media_ids):
        raise RuntimeError(f'Limpeza incompleta: {removed}/{len(media_ids)} mídias removidas.')
    print(f'[OK] Limpeza: {removed} mídias de teste removidas')


def main():
    owner_a = require_owner('TEST_OWNER_A')
    owner_b = require_owner('TEST_OWNER_B')
    if owner_a == owner_b:
        raise ValueError('Os dois usuários de teste precisam ser diferentes.')
    if not settings.DATABASE_URL:
        raise ValueError('DATABASE_URL não configurada.')

    run_id = uuid.uuid4().hex[:12]
    prefix = f'__TESTE_E5_{run_id}_'
    created = []
    test_passed = False
    try:
        print('Carregando modelo local de embeddings; a primeira execução pode demorar...')
        model = get_embedding_service()
        sample = model.embed_query('Qual foi o horário informado pela testemunha?')
        assert len(sample) == settings.EMBEDDING_DIMENSIONS == 384
        print('[OK] Modelo E5 gerou embedding real com 384 dimensões')

        cases = [
            ('horario', 'A testemunha declarou que chegou ao estacionamento às oito horas e trinta minutos da manhã.'),
            ('veiculo', 'O automóvel observado era um carro vermelho, modelo hatch, com quatro portas.'),
            ('presenca', 'A testemunha afirmou que não viu o acusado entrar no estabelecimento.'),
        ]
        filenames = {}
        for topic, text in cases:
            filename = f'{prefix}{topic}.mp4'
            result = storage.index_transcript_segments(filename, segment(text), owner_a)
            created.append(result['media_id'])
            assert result['chunks_count'] >= 1
            filenames[topic] = filename
        private_filename = f'{prefix}privado_usuario_b.mp4'
        result_b = storage.index_transcript_segments(
            private_filename,
            segment('O depoimento privado do usuário B informa que o contrato foi assinado em janeiro.'),
            owner_b,
        )
        created.append(result_b['media_id'])
        print('[OK] Quatro transcrições fictícias indexadas com embeddings reais')

        history_a = storage.get_indexed_audio_history(owner_a)
        history_b = storage.get_indexed_audio_history(owner_b)
        assert all(name in [x['filename'] for x in history_a] for name in filenames.values())
        assert private_filename not in [x['filename'] for x in history_a]
        assert private_filename in [x['filename'] for x in history_b]
        assert not any(name in [x['filename'] for x in history_b] for name in filenames.values())
        print('[OK] Histórico isolado entre usuários')

        queries = [
            ('Qual foi o horário de chegada da testemunha?', 'horario'),
            ('Qual era a cor e o tipo do veículo?', 'veiculo'),
            ('A testemunha viu o acusado entrar no estabelecimento?', 'presenca'),
        ]
        matched = 0
        for question, expected in queries:
            results = storage.search_audio_context(question, n_results=3, owner_user_id=owner_a)
            assert results, f'Sem resultados para: {question}'
            assert all(item['audio_filename'] != private_filename for item in results)
            assert all(item['start'] >= 0 and item['end'] >= item['start'] for item in results)
            first = results[0]['audio_filename']
            correct = first == filenames[expected]
            matched += int(correct)
            print(f"[{'OK' if correct else 'ATENÇÃO'}] Pergunta: {question}\n    Primeiro resultado: {first} | Esperado: {filenames[expected]}")
        print(f'[RESULTADO] Relevância top-1: {matched}/{len(queries)} (avaliação exploratória, não garantia de qualidade)')

        filtered = storage.search_audio_context(
            'O que a testemunha declarou?', n_results=5,
            audio_filter=filenames['presenca'], owner_user_id=owner_a,
        )
        assert filtered and all(item['audio_filename'] == filenames['presenca'] for item in filtered)
        assert storage.search_audio_context('Qual é o contrato?', owner_user_id=owner_b,
                                            audio_filter=filenames['horario']) == []
        print('[OK] Filtro por arquivo e isolamento na busca')

        # O próprio serviço abre uma nova conexão para cada consulta.
        history_again = storage.get_indexed_audio_history(owner_a)
        assert any(x['filename'] == filenames['horario'] for x in history_again)
        print('[OK] Dados permanecem disponíveis em novas conexões')
        test_passed = True
    finally:
        try:
            delete_test_media(created)
        except Exception as exc:
            print(f'[ERRO] Não foi possível limpar todos os registros: {exc}')
            print('IDs para limpeza manual:', ', '.join(created))
            raise
    if test_passed:
        print('\nSUCESSO: embeddings reais, pgvector e isolamento validados tecnicamente.')
        print('PENDENTE: validar qualidade com conjunto maior e fluxo React com mídia real.')


if __name__ == '__main__':
    main()
