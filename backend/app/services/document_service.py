import io
from pypdf import PdfReader
from openai import OpenAI
from app.config import settings
import json

client = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

def extract_pdf_data(file_bytes: bytes) -> dict:
    """Lê um PDF enviado e usa a Groq para extrair dados estruturados do processo."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
            
    truncated_text = text[:15000]

    prompt = f"""
    Analise o seguinte documento jurídico e extraia as informações em formato JSON estrito contendo exatamente estas chaves:
    - "numero_processo": string ou null
    - "classe_processual": string ou null
    - "comarca_vara": string ou null
    - "autor": string ou null
    - "reu": string ou null
    - "resumo_pedidos": string

    Texto do documento:
    {truncated_text}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Modelo rápido e potente da Groq
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices.message.content)