"""Execute na raiz juridical-ai-mvp: python instalar_frontend.py.
Coloque juridical-ai-react-mvp.zip ao lado deste script.
"""
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'juridical-ai-react-mvp.zip'
TARGET = ROOT / 'frontend' / 'react-app'


def main():
    if not (ROOT / 'backend' / 'app').is_dir():
        sys.exit('ERRO: coloque este script na raiz juridical-ai-mvp (ao lado de backend).')
    if not ARCHIVE.is_file():
        sys.exit('ERRO: coloque juridical-ai-react-mvp.zip na mesma pasta deste script.')
    if TARGET.exists() and any(TARGET.iterdir()):
        sys.exit('ERRO: frontend/react-app ja existe e nao esta vazio. Nenhum arquivo foi sobrescrito.')
    with zipfile.ZipFile(ARCHIVE) as zf:
        entries = [info for info in zf.infolist() if not info.is_dir()]
        if not entries or any(not info.filename.startswith('juridical-ai-frontend/') for info in entries):
            sys.exit('ERRO: formato do ZIP inesperado.')
        for info in entries:
            relative = Path(info.filename).relative_to('juridical-ai-frontend')
            if relative.is_absolute() or '..' in relative.parts:
                sys.exit('ERRO: caminho inseguro dentro do ZIP.')
            dest = TARGET / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as source, dest.open('wb') as output:
                shutil.copyfileobj(source, output)
    env = TARGET / '.env'
    if not env.exists():
        env.write_text('VITE_API_BASE_URL=http://127.0.0.1:8000\n', encoding='utf-8')
    print(f'OK: React instalado em {TARGET}')
    print('OK: .env configurado para FastAPI local')
    print('Proximo passo: cd frontend\\react-app; npm install; npm run dev')

if __name__ == '__main__':
    main()
