# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa app.py. Versão do Código: v.1.0.000
# Data de atualização: 26/07/2026 - 03:00
# Descrição das Alterações:
# - Estruturação inicial do roteador principal com autenticação, cache do Sheets e seletor de Ano Letivo.
# ==============================================================================

import streamlit as st
import pandas as pd

# 1. Configuração Inicial da Página
st.set_page_config(
    page_title="SISTEMAS iPeC - Painel Principal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Aplicação de Estilos Globais (CSS Customizado)
def carregar_estilos():
    st.markdown("""
        <style>
            .main {
                background-color: #f8f9fa;
            }
            .stSidebar {
                background-color: #ffffff;
            }
            h1, h2, h3 {
                color: #1f2937;
            }
        </style>
    """, unsafe_allow_html=True)

carregar_estilos()

# 3. Função de Conexão Cacheada com o Google Sheets (Exemplo Base)
@st.cache_data(ttl=600)
def carregar_dados_sheets(url_planilha):
    """
    Realiza a conexão e o carregamento cacheado dos dados do Google Sheets.
    """
    try:
        # Substituir ou ajustar conforme o método de integração utilizado (gspread / pandas)
        df = pd.read_csv(url_planilha) 
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a base de dados: {e}")
        return pd.DataFrame()

# 4. Sistema Simples de Autenticação Global
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.subheader("🔐 Acesso Restrito - SISTEMAS iPeC")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Validação básica (ajustar credenciais conforme necessário)
            if usuario == "admin" and senha == "ipec2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        return False
    return True

# 5. Fluxo Principal da Aplicação
def main():
    if not verificar_autenticacao():
        return

    # Barra Lateral - Configurações Globais e Ano Letivo
    st.sidebar.image("https://via.placeholder.com/150", use_column_width=True) # Espaço para logo se houver
    st.sidebar.title("Painel de Controle")
    
    ano_letivo = st.sidebar.selectbox(
        "📅 Selecione o Ano Letivo",
        options=["2026", "2025", "2024"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"Ano Letivo Ativo: **{ano_letivo}**")

    if st.sidebar.button("Encerrar Sessão"):
        st.session_state.autenticado = False
        st.rerun()

    # Corpo Principal - Roteador (Preparado para receber os módulos da pasta src/)
    st.title("🌟 SISTEMAS iPeC - Ambiente Modular")
    st.write(f"Bem-vindo ao sistema principal. Ano Letivo selecionado: **{ano_letivo}**.")
    st.info("Base do `app.py` configurada com sucesso. Aguardando a integração do próximo módulo.")

if __name__ == "__main__":
    main()

# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
