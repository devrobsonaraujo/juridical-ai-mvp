import streamlit as st
import requests
import os

# Configuração inicial da página
st.set_page_config(
    page_title="Juridical AI - Análise Inteligente",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização limpa oculta elementos nativos
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.viewerBadge_container__1QSob {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CONFIGURAÇÃO INTELIGENTE DE URL (LOCAL vs NUVEM)
# ---------------------------------------------------------
# Você pode definir a variável de ambiente BACKEND_URL no Render,
# ou o sistema usará o Render por padrão se estiver em produção, 
# alternando para localhost caso esteja rodando na sua máquina.
DEFAULT_CLOUD_URL = "https://juridical-ai-mvp.onrender.com"
BACKEND_BASE_URL = os.getenv("BACKEND_URL", DEFAULT_CLOUD_URL)

# Se quiser forçar localmente para testes, basta descomentar a linha abaixo:
# BACKEND_BASE_URL = "http://127.0.0.1:8000"

BACKEND_AUDIO_URL = f"{BACKEND_BASE_URL}/api/v1/audio/transcribe"
BACKEND_HISTORY_URL = f"{BACKEND_BASE_URL}/api/v1/audio/history"
BACKEND_RAG_URL = f"{BACKEND_BASE_URL}/api/v1/rag/query"

# Controle de Sessão
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "transcription_result" not in st.session_state:
    st.session_state.transcription_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def render_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("## ⚖️ Juridical AI MVP")
        st.markdown("Acesso soberano à plataforma de inteligência probatória.")
        with st.form("login_form"):
            email_input = st.text_input("E-mail Corporativo ou OAB", placeholder="advogado@tribunal.jus.br")
            senha_input = st.text_input("Credencial de Segurança", type="password", placeholder="123456")
            if st.form_submit_button("Entrar no Sistema", use_container_width=True):
                if email_input.strip() != "" and senha_input == "123456":
                    st.session_state.authenticated = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Use qualquer e-mail e a senha: 123456")

if not st.session_state.authenticated:
    render_login_page()
    st.stop()

# Sidebar de Navegação
with st.sidebar:
    st.image("https://img.icons8.com/color/96/scales.png", width=70)
    st.markdown("### Juridical AI")
    st.caption("Enterprise MVP • Segurança OAB")
    st.markdown(f"🔗 **API Conectada:** `{BACKEND_BASE_URL}`")
    st.markdown("---")
    nav_opcao = st.radio("Selecione o Módulo", ["🎙️ Degravação & Busca", "📄 Extração & RAG Documental"], label_visibility="collapsed")
    st.markdown("---")
    if st.button("🔒 Sair do Sistema", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ------------------------------------------
# MÓDULO 1: DEGRAVAÇÃO & BUSCA DE VÍDEOS/ÁUDIOS
# ------------------------------------------
if nav_opcao == "🎙️ Degravação & Busca":
    st.markdown("# ⚖️ Gestão e Degravação de Audiências (Vídeo & Áudio)")
    st.markdown("Transcrição estenográfica automatizada com extração de áudio de vídeos, indexação vetorial e marcação temporal.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 1. Enviar Nova Gravação")
        uploaded_file = st.file_uploader(
            "Arraste o arquivo de vídeo ou áudio (MP4, MKV, AVI, MOV, MP3, WAV)", 
            type=["mp4", "mkv", "avi", "mov", "mp3", "wav", "m4a"]
        )
        
        if uploaded_file:
            file_name_lower = uploaded_file.name.lower()
            is_video = file_name_lower.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm"))
            
            st.info(f"Arquivo carregado: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
            
            if is_video:
                st.video(uploaded_file)
            else:
                st.audio(uploaded_file)

            if st.button("Processar Mídia e Transcrever", use_container_width=True):
                with st.spinner("Extraindo áudio (se vídeo), enviando para a IA e indexando no ChromaDB..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        # Timeout estendido para arquivos longos na nuvem
                        response = requests.post(BACKEND_AUDIO_URL, files=files, timeout=600)
                        if response.status_code == 200:
                            st.session_state.transcription_result = response.json()
                            st.success("Mídia processada e indexada com sucesso no disco!")
                        else:
                            st.error(f"Erro no servidor: {response.text}")
                    except Exception as e:
                        st.error(f"Falha de conexão com {BACKEND_AUDIO_URL}: {str(e)}")

        st.markdown("---")
        st.markdown("### 📚 Mídias Indexadas no Servidor")
        try:
            hist_res = requests.get(BACKEND_HISTORY_URL, timeout=5)
            if hist_res.status_code == 200:
                for item in hist_res.json().get("history", []):
                    st.info(f"📁 **{item['filename']}** ({item['chunks_count']} blocos vetoriais)")
        except Exception:
            st.caption("Histórico indisponível no momento.")

    with col_b:
        st.markdown("### 3. Transcrição Estruturada da Audiência")
        if st.session_state.transcription_result:
            data = st.session_state.transcription_result
            st.success(f"Total de segmentos processados: {data.get('segments_count', 0)}")
            with st.expander("📄 Ver Texto Completo da Degravação", expanded=True):
                st.write(data.get("full_text"))
        else:
            st.info("Faça o upload de uma gravação ao lado para visualizar a transcrição estenográfica estruturada.")

# ------------------------------------------
# MÓDULO 2: COPILOTO JURÍDICO & RAG
# ------------------------------------------
else:
    st.markdown("# 📄 Copiloto Jurídico & RAG Documental")
    st.markdown("Consulte peças processuais e gravações de audiências indexadas com recuperação semântica vetorial.")

    audio_options = ["Todas as Mídias"]
    try:
        hist_res = requests.get(BACKEND_HISTORY_URL, timeout=5)
        if hist_res.status_code == 200:
            for item in hist_res.json().get("history", []):
                audio_options.append(item["filename"])
    except Exception:
        pass

    selected_audio = st.selectbox("🎯 Filtrar consulta por gravação específica:", audio_options)

    st.markdown("---")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("Faça uma pergunta jurídica aos documentos ou gravações indexadas..."):
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Consultando base vetorial ChromaDB e gerando fundamentação..."):
                try:
                    payload = {
                        "question": user_query, 
                        "k": 8,
                        "audio_filter": None if selected_audio == "Todas as Mídias" else selected_audio
                    }
                    response = requests.post(BACKEND_RAG_URL, json=payload, timeout=60)
                    
                    if response.status_code == 200:
                        rag_data = response.json()
                        answer = rag_data.get("answer", "Sem resposta.")
                        sources = rag_data.get("sources", [])
                        
                        full_response = f"{answer}\n\n**🔍 Fontes e Timestamps Citados:**"
                        for src in sources:
                            start_sec = int(src.get("start", 0))
                            m, s = divmod(start_sec, 60)
                            audio_origin = src.get('audio_filename', 'Mídia')
                            full_response += f"\n- *[{m:02d}:{s:02d}] ({audio_origin})*: {src.get('text', '')[:100]}..."
                        
                        st.markdown(full_response)
                        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    else:
                        st.error(f"Erro na consulta RAG: {response.text}")
                except Exception as e:
                    st.error(f"Erro de conexão com o servidor RAG: {str(e)}")