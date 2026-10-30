import streamlit as st
import requests

# Configuração da Página
st.set_page_config(
    page_title="Juridical AI - Assistente Jurídico Inteligente",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para dar um tom mais profissional e corporativo
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        gap: 12px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: white !important;
        font-weight: bold;
    }
    div.stButton > button:first-child {
        background-color: #0f172a;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #1e293b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# URL base do Backend FastAPI
BACKEND_URL = "http://127.0.0.1:8000"

# --- SIDEBAR DE NAVEGAÇÃO / STATUS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/law.png", width=64)
    st.title("Juridical AI MVP")
    st.markdown("---")
    st.info("💡 **Dica:** Certifique-se de que o backend FastAPI está rodando na porta 8000.")
    
    # Status da Conexão com o Backend
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            st.success("🟢 Backend Conectado")
        else:
            st.warning("🟡 Backend instável")
    except:
        st.error("🔴 Backend Desconectado")
        
    st.markdown("---")
    st.markdown("### Configurações")
    selected_model = st.selectbox("Modelo LLM", ["gpt-4o-mini", "llama3-70b (Groq)"])

# --- CABEÇALHO PRINCIPAL ---
st.title("⚖️ Sistema Inteligente para Análise Jurídica")
st.markdown("Plataforma integrada para degravação de audiências com marcação temporal e extração estruturada de dados de documentos.")

# --- ABAS PRINCIPAIS ---
tab1, tab2 = st.tabs(["🎙️ Degravação & Busca em Audiências", "📄 Extração de Dados de Documentos"])

# ==========================================
# ABA 1: DEGRAVAÇÃO & BUSCA EM ÁUDIOS
# ==========================================
with tab1:
    st.header("Gestão e Consulta de Áudios de Audiências")
    st.markdown("Faça o upload da gravação da audiência para gerar a transcrição com timestamps e realizar buscas semânticas.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Enviar Nova Gravação")
        audio_file = st.file_uploader("Selecione o arquivo de áudio (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])
        
        if audio_file is not None:
            st.audio(audio_file)
            if st.button("🚀 Processar e Degravar Áudio"):
                with st.spinner("Enviando e processando áudio no Whisper... Isso pode levar alguns segundos."):
                    # Simulação de envio para o endpoint do FastAPI
                    # files = {"file": audio_file.getvalue()}
                    # res = requests.post(f"{BACKEND_URL}/audio/transcribe", files=files)
                    st.success("Áudio degravado com sucesso e indexado no ChromaDB!")

        st.markdown("---")
        st.subheader("2. Consultar Trechos (RAG com Timestamps)")
        query = st.text_input("O que você procura nesta audiência?", placeholder="Ex: O que o testigo de acusação falou sobre o horário?")
        if st.button("🔍 Pesquisar na Audiência"):
            if query:
                with st.spinner("Buscando trechos relevantes..."):
                    # Aqui chamaremos o endpoint do backend RAG
                    st.markdown("### Resultados Encontrados:")
                    st.info("⏱️ **[00:14:22]** - *Testemunha relata que chegou ao local por volta das 14h...*")
                    st.success("⏱️ **[00:22:50]** - *Juiz questiona o réu acerca da assinatura do contrato...*")
            else:
                st.warning("Digite uma pergunta para iniciar a busca.")

    with col2:
        st.subheader("3. Transcrição Completa da Audiência")
        st.markdown("*(A transcrição estruturada aparecerá aqui após o processamento)*")
        
        # Exemplo visual de como o timestamp será exibido de forma limpa
        transcription_container = st.container(height=450)
        with transcription_container:
            st.markdown("`[00:00:12]` **Juiz:** *Declaro aberta a presente audiência de instrução e julgamento...*")
            st.markdown("`[00:01:05]` **Promotor:** *Excelência, reiteramos os termos da denúncia...*")
            st.markdown("`[00:05:40]` **Defensor:** *MM. Juiz, a defesa tem preliminar a arguir...*")

# ==========================================
# ABA 2: EXTRAÇÃO DE DADOS DE DOCUMENTOS
# ==========================================
with tab2:
    st.header("Extração Automatizada de Documentos Jurídicos")
    st.markdown("Envie petições, contratos ou sentenças para extração estruturada de metadados e resumo executivo.")

    doc_file = st.file_uploader("Selecione o documento jurídico (PDF)", type=["pdf"])

    if doc_file is not None:
        st.success(f"Arquivo carregado: **{doc_file.name}**")
        if st.button("⚙️ Extrair Dados do Documento"):
            with st.spinner("Analisando documento e estruturando dados com IA..."):
                # Simulação da resposta estruturada do backend
                st.markdown("---")
                st.subheader("📊 Dados Extraídos com Sucesso")
                
                # Exibição em colunas / métricas simuladas
                m1, m2, m3 = st.columns(3)
                m1.metric("Número do Processo", "1002345-88.2026.8.26.0100")
                m2.metric("Classe Processual", "Ação de Indenização")
                m3.metric("Comarca / Vara", "TJSP - 1ª Vara Cível")

                st.markdown("### 📝 Partes Envolvidas")
                st.write("- **Autor:** João da Silva")
                st.write("- **Réu:** Banco S.A.")

                st.markdown("### 📌 Resumo dos Pedidos / Objeto")
                st.info("A parte autora alega cobrança indevida em conta corrente e requer tutela antecipada para suspensão dos descontos, além de danos morais no valor de R$ 10.000,00.")