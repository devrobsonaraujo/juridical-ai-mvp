# Juridical AI — Etapa 2

## Instalação (Windows / PowerShell)

1. Faça backup de `frontend/react-app` antes de substituir arquivos.
2. Extraia este ZIP e copie o conteúdo de `react-app/` sobre sua pasta existente.
3. Preserve seu `.env` local: `VITE_API_BASE_URL=http://127.0.0.1:8000`.
4. Na pasta `frontend/react-app`, execute `npm install`, `npm run build`, `npm run dev`.
5. Mantenha o FastAPI em execução em outro terminal.

## O que mudou

- Envio por seleção ou arrastar e soltar; preview local e tamanho do arquivo.
- Tempo decorrido durante a requisição de transcrição (não é progresso percentual real).
- Busca de gravações e botão para consultar diretamente a mídia no RAG.
- Transcrição com metadados de indexação, copiar texto e acesso ao assistente.
- Seleção de mídia compartilhada entre Audiências e Assistente.
- Arquivo `src/vite-env.d.ts` incluído.

## Validação manual

- Teste tema claro/escuro, desktop e mobile.
- Teste um MP3 pequeno e confirme histórico e transcrição.
- Clique em "Perguntar sobre esta gravação" e confira o filtro no assistente.
- Faça uma pergunta e confirme resposta e fontes.
- Teste erro de rede com o FastAPI desligado.

## Limitações

- A API de transcrição é síncrona; não há progresso real nem cancelamento de processamento no servidor.
- O histórico lista nomes e quantidade de trechos, mas o backend atual não fornece a transcrição completa de mídias antigas.
- Login demonstrativo não é autenticação segura para dados jurídicos reais.
- A compilação não foi executada neste ambiente por falta de dependências npm em cache; valide com `npm run build` localmente.
