from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import audio_router, rag_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API de IA para degravação e busca semântica em áudios de audiências judiciais."
)

# Configuração de CORS para permitir requisições do Frontend (Streamlit ou HTML)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das Rotas
app.include_router(audio_router.router)
app.include_router(rag_router.router)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    # Captura a porta da variável de ambiente do Render (padrão: 8000 se local)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)