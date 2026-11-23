"""Valida contratos da API sem executar transcricao real por padrao.
Uso: python validar_api.py --base-url http://127.0.0.1:8000
Opcional: --file caminho/arquivo.mp3 para testar upload real (pode levar 10 min).
"""
import argparse
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


def call(url, method='GET', payload=None, headers=None, timeout=10):
    req = urllib.request.Request(url, data=payload, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode('utf-8', errors='replace')
        try:
            body = json.loads(body)
        except ValueError:
            pass
        return err.code, body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--file', type=Path, help='Arquivo de audio/video real para transcricao')
    parser.add_argument('--question', default='Quais informacoes existem nas midias indexadas?')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    failures = 0
    print('API:', base)
    try:
        status, data = call(base + '/api/v1/audio/history', timeout=15)
        valid = status == 200 and isinstance(data, dict) and isinstance(data.get('history'), list)
        print(f'[{'OK' if valid else 'FALHOU'}] GET /audio/history: HTTP {status}')
        if valid:
            print('  Midias:', len(data['history']))
            if data['history']:
                print('  Primeiro item:', str(data['history'][0])[:300])
        else:
            print('  Resposta:', str(data)[:500]); failures += 1
    except Exception as exc:
        print('[FALHOU] GET /audio/history:', exc); failures += 1

    payload = json.dumps({'question': args.question, 'k': 8, 'audio_filter': None}).encode()
    try:
        status, data = call(base + '/api/v1/rag/query', 'POST', payload, {'Content-Type': 'application/json'}, 75)
        valid = status == 200 and isinstance(data, dict) and isinstance(data.get('answer'), str) and isinstance(data.get('sources'), list)
        print(f'[{'OK' if valid else 'FALHOU'}] POST /rag/query: HTTP {status}')
        if valid:
            print('  Resposta:', data['answer'][:300]); print('  Fontes:', len(data['sources']))
        else:
            print('  Resposta:', str(data)[:500]); failures += 1
    except Exception as exc:
        print('[FALHOU] POST /rag/query:', exc); failures += 1

    if args.file:
        if not args.file.is_file():
            print('[FALHOU] Arquivo nao encontrado:', args.file); failures += 1
        else:
            import mimetypes
            boundary = 'juridical-ai-validation-boundary'
            mime = mimetypes.guess_type(args.file.name)[0] or 'application/octet-stream'
            head = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{args.file.name}"\r\nContent-Type: {mime}\r\n\r\n').encode()
            body = head + args.file.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
            print('Enviando midia real. Pode levar ate 10 minutos...')
            try:
                status, data = call(base + '/api/v1/audio/transcribe', 'POST', body, {'Content-Type': f'multipart/form-data; boundary={boundary}'}, 610)
                valid = status == 200 and isinstance(data, dict) and any(key in data for key in ('full_text', 'text', 'transcription', 'data', 'result'))
                print(f'[{'OK' if valid else 'FALHOU'}] POST /audio/transcribe: HTTP {status}')
                print('  Resposta:', str(data)[:500])
                if not valid: failures += 1
            except Exception as exc:
                print('[FALHOU] POST /audio/transcribe:', exc); failures += 1
    else:
        print('[NAO EXECUTADO] POST /audio/transcribe: informe --file para teste real.')
    print('\nResultado:', 'sem falhas nos testes executados' if failures == 0 else f'{failures} falha(s)')
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
