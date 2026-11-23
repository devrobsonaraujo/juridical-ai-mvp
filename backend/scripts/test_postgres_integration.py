"""Teste de integração não destrutivo para PostgreSQL/pgvector.

Execute a partir da pasta backend:
  python scripts/test_postgres_integration.py

Requer TEST_OWNER_A e TEST_OWNER_B: UUIDs distintos de usuários existentes
no Supabase Auth. Não chama Groq nem carrega sentence-transformers.
"""
import os
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import postgres_vector_service as storage


def require_owner(name: str) -> str:
    raw = os.environ.get(name, '').strip()
    try:
        return str(uuid.UUID(raw))
    except (ValueError, AttributeError) as exc:
        raise RuntimeError(f'{name} deve ser UUID válido de um usuário do Supabase Auth.') from exc


class FakeEmbeddings:
    """Vetores determinísticos apenas para testar pgvector, não qualidade de IA."""
    @staticmethod
    def embed_documents(texts):
        result = []
        for text in texts:
            vector = [0.0] * 384
            vector[0 if 'portão' in text.lower() else 1] = 1.0
            result.append(vector)
        return result

    @staticmethod
    def embed_query(question):
        vector = [0.0] * 384
        vector[0 if 'portão' in question.lower() else 1] = 1.0
        return vector


def cleanup(created):
    errors = []
    for owner, media_id in created:
        try:
            with storage._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'DELETE FROM public.media_files WHERE id = %s::uuid AND owner_user_id = %s::uuid',
                        (media_id, owner),
                    )
        except Exception as exc:
            errors.append((media_id, str(exc)))
    return errors


def main():
    owner_a = require_owner('TEST_OWNER_A')
    owner_b = require_owner('TEST_OWNER_B')
    if owner_a == owner_b:
        raise RuntimeError('TEST_OWNER_A e TEST_OWNER_B devem ser diferentes.')
    if not storage.settings.DATABASE_URL:
        raise RuntimeError('DATABASE_URL não configurada no .env.')
    if storage.settings.EMBEDDING_DIMENSIONS != 384:
        raise RuntimeError('Este teste requer EMBEDDING_DIMENSIONS=384.')

    marker = uuid.uuid4().hex[:12]
    filename_a = f'__teste_integracao_{marker}_a.txt'
    filename_b = f'__teste_integracao_{marker}_b.txt'
    created = []
    success = False
    try:
        with patch.object(storage, 'get_embedding_service', return_value=FakeEmbeddings()):
            segments_a = [
                {'text': 'A testemunha declarou que não viu o acusado atravessar o portão.', 'start': 5.0, 'end': 12.0},
                {'text': 'O advogado confirmou a data do depoimento fictício.', 'start': 13.0, 'end': 19.0},
            ]
            segments_b = [
                {'text': 'Outra testemunha falou sobre um contrato fictício.', 'start': 2.0, 'end': 8.0},
            ]
            result_a = storage.index_transcript_segments(filename_a, segments_a, owner_a)
            created.append((owner_a, result_a['media_id']))
            print('[OK] Inserção da mídia do usuário A')
            result_b = storage.index_transcript_segments(filename_b, segments_b, owner_b)
            created.append((owner_b, result_b['media_id']))
            print('[OK] Inserção da mídia do usuário B')

            # Cada chamada abre uma conexão nova, validando persistência após reconexão.
            history_a = storage.get_indexed_audio_history(owner_a)
            history_b = storage.get_indexed_audio_history(owner_b)
            ids_a = {row['media_id'] for row in history_a}
            ids_b = {row['media_id'] for row in history_b}
            assert result_a['media_id'] in ids_a
            assert result_b['media_id'] in ids_b
            assert result_b['media_id'] not in ids_a
            assert result_a['media_id'] not in ids_b
            print('[OK] Histórico persistido em novas conexões e isolado por usuário')

            matches_a = storage.search_audio_context('O que aconteceu no portão?', 4, filename_a, owner_a)
            assert matches_a, 'Busca de A não retornou trechos.'
            assert all(m['media_id'] == result_a['media_id'] for m in matches_a)
            assert all(isinstance(m['start'], float) and isinstance(m['end'], float) for m in matches_a)
            assert all(m['start'] <= m['end'] for m in matches_a)
            print('[OK] Busca vetorial pgvector e timestamps')

            forbidden_a = storage.search_audio_context('contrato fictício', 4, filename_b, owner_a)
            forbidden_b = storage.search_audio_context('portão', 4, filename_a, owner_b)
            assert forbidden_a == [] and forbidden_b == [], 'Falha no isolamento de busca.'
            print('[OK] Nenhum usuário recupera mídia do outro')

            with storage._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(*) AS total FROM public.transcript_chunks WHERE media_id = %s::uuid AND owner_user_id = %s::uuid',
                        (result_a['media_id'], owner_a),
                    )
                    assert cursor.fetchone()['total'] == result_a['chunks_count']
            print('[OK] Chunks persistidos no PostgreSQL')
            success = True
    finally:
        errors = cleanup(created)
        if errors:
            print('[ERRO] Não foi possível limpar todos os registros. IDs:', [item[0] for item in errors])
            raise RuntimeError('Limpeza incompleta; remova manualmente somente os IDs indicados.')
        print('[OK] Dados fictícios de teste removidos')
    if success:
        print('\nSUCESSO: integração PostgreSQL validada com vetores sintéticos.')
        print('PENDENTE: validar embeddings reais, qualidade semântica e fluxo React.')


if __name__ == '__main__':
    main()
