# Juridical AI — Frontend React

## Execução

Requer Node.js 20.19+ ou 22.12+ (conforme Vite).

```bash
npm install
cp .env.example .env
npm run dev
```

No Windows PowerShell: `Copy-Item .env.example .env`.

Edite `VITE_API_BASE_URL` no `.env` para alternar entre Render e `http://127.0.0.1:8000`. Reinicie o Vite após editar o `.env`.

```bash
npm run build
npm run preview
```

Publique `dist/` como site estático (Render Static Site, Vercel ou Netlify). Configure `VITE_API_BASE_URL` no ambiente de build e execute `npm run build`. Em Render Static Site: Build Command `npm install && npm run build`; Publish Directory `dist`.

## CORS no FastAPI

O backend precisa permitir a origem exata do frontend, por exemplo:

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,
    allow_origins=['http://localhost:5173', 'https://SEU-FRONTEND.onrender.com'],
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)
```

Adapte o exemplo à instância `app` existente, sem duplicar middleware. CORS é uma configuração do backend; não pode ser corrigido no React.

## Segurança e limitações do MVP

- O login usa a senha demonstrativa `123456`, reproduzindo o Streamlit. Não protege a API. Substituir por autenticação real no backend antes de usar dados sensíveis.
- Estado de login e transcrição somente em memória; recarregar a página encerra a sessão. O chat permanece ao alternar módulos, mas é perdido no reload/logout.
- A API de transcrição tem timeout de 600 s, histórico de 5 s e RAG de 60 s. Proxies/plataformas podem encerrar conexões antes disso. Para produção, prefira jobs assíncronos com polling/SSE.
- O upload preserva o nome original do arquivo no multipart `file`. Não há limite de tamanho imposto pelo frontend; confira limites do backend e hospedagem.
- Os formatos MKV, AVI, MOV e M4A podem não ser reproduzidos em todos os navegadores, mesmo sendo aceitos para upload.
- Os contratos foram implementados conforme o app.py e a especificação; não foram validados contra a API real nem com arquivos de audiência.

## Checklist de validação

1. Login com credencial correta e incorreta; logout.
2. Upload de vídeo e áudio; preview, tamanho, processamento e cópia da transcrição.
3. Histórico carregado e atualizado após indexação.
4. RAG com todas as mídias e filtro individual, Markdown e fontes com timestamps.
5. Falhas de rede, HTTP 4xx/5xx e timeouts; teste em mobile.
6. Verificar CORS e limites de upload no domínio final.
