import os

# Definição da estrutura de pastas e arquivos
estrutura = {
    "juridical-ai-mvp": {
        "backend": {
            "app": {
                "__init__.py": "",
                "main.py": "# Inicializacao do FastAPI\n",
                "config.py": "# Configuracoes e Variaveis de Ambiente\n",
                "routers": {
                    "__init__.py": "",
                    "audio_router.py": "# Rotas de Audio\n",
                    "rag_router.py": "# Rotas de RAG/Chat\n",
                },
                "services": {
                    "__init__.py": "",
                    "transcription_service.py": "# Servico do Whisper\n",
                    "vector_service.py": "# Servico ChromaDB + LangChain\n",
                },
                "utils": {
                    "__init__.py": "",
                    "audio_splitter.py": "# Fatiador com pydub\n",
                },
            },
            "data": {
                "vector_db": {} # Pasta vazia para o ChromaDB
            },
            "temp": {}, # Pasta temporaria de audios
            "requirements.txt": (
                "fastapi==0.110.0\nuvicorn[standard]==0.28.0\npython-multipart==0.0.9\npydantic==2.6.4\npydantic-settings==2.2.1\nopenai==1.14.1\nlangchain==0.1.12\nlangchain-community==0.0.28\nchromadb==0.4.24\npydub==0.25.1\nstreamlit==1.32.2\nrequests==2.31.0\npython-dotenv==1.0.1\n"
            ),
        },
        "frontend": {
            "app.py": "# Interface Streamlit\n"
        },
        ".env": "OPENAI_API_KEY=sua_chave_aqui\n"
    }
}

def criar_estrutura(base_path, estrutura_dict):
    for nome, conteudo in estrutura_dict.items():
        caminho_atual = os.path.join(base_path, nome)
        if isinstance(conteudo, dict):
            os.makedirs(caminho_atual, exist_ok=True)
            criar_estrutura(caminho_atual, conteudo)
        else:
            os.makedirs(os.path.dirname(caminho_atual), exist_ok=True)
            with open(caminho_atual, "w", encoding="utf-8") as f:
                f.write(conteudo)

if __name__ == "__main__":
    print("Criando estrutura do projeto...")
    criar_estrutura(".", estrutura)
    print("Estrutura criada com sucesso!")