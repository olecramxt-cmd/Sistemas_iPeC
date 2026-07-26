# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa ui_elementos.py. Versão do Código: v.1.5.050
# Data de atualização: 26/07/2026 - 04:29
# Descrição das Alterações:
#   - Melhoria do contraste e legibilidade das opções de menu e rádio na barra lateral.
# ==============================================================================

import streamlit as st
import os
import base64

def aplicar_estilos_css():
    """Aplica o design corporativo e estilos CSS personalizados do ecossistema iPeC."""
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f2b5c 0%, #1e4b8f 50%, #f7c325 100%);
                color: #ffffff !important;
                padding-top: 0rem !important;
            }
            [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
                color: #ffffff !important;
            }
            [data-testid="stSidebar"] > div:first-child {
                margin-top: -35px !important;
            }
            .stRadio > div {
                background-color: rgba(15, 43, 92, 0.6);
                padding: 10px;
                border-radius: 8px;
                border: 1px solid rgba(247, 195, 37, 0.4);
            }
            .stRadio label {
                color: #ffffff !important;
                font-weight: 700 !important;
                font-size: 1.05em !important;
            }
            div.stButton > button:first-child {
                background-color: #1e4b8f;
                color: white;
                border-radius: 6px;
                border: 1px solid #f7c325;
                width: 100%;
                padding: 0.3rem;
            }
            div.stButton > button:first-child:hover {
                background-color: #f7c325;
                color: #0f2b5c;
            }
            .sidebar-logo-footer {
                text-align: center;
                font-size: 0.72em;
                color: #ffffff;
                margin-top: -35px;
                margin-bottom: 2px;
                padding-bottom: 2px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                line-height: 1.2;
            }
            .profile-wrapper {
                text-align: center;
                margin-top: -15px;
                margin-bottom: 5px;
            }
            .profile-img-container {
                width: 70px;
                height: 70px;
                border-radius: 50%;
                object-fit: cover;
                border: 3px solid #f7c325;
                margin: 0 auto 1px auto;
                display: block;
            }
            .header-container-centralizado {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                width: 100%;
                margin-top: 10px;
                margin-bottom: 15px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.6);
                border-radius: 10px;
                border: 1px solid rgba(30, 75, 143, 0.2);
            }
            .header-logo-img-cent {
                width: 75px;
                height: auto;
                border-radius: 6px;
                margin-bottom: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .titulo-central-proporcional {
                font-family: 'Segoe UI Black', Arial, sans-serif;
                font-size: 2.2vw;
                font-weight: 900;
                color: #0f2b5c;
                line-height: 1.2;
                margin: 0 0 5px 0;
            }
            .escola-titulo-proporcional {
                font-family: 'Segoe UI Black', Arial, sans-serif;
                font-size: 1.3vw;
                font-weight: 900;
                color: #1e4b8f;
                letter-spacing: 1px;
                margin: 0;
            }
            .sidebar-aviso-branco {
                color: #ffffff !important;
                font-size: 0.9em;
                background-color: rgba(255, 255, 255, 0.15);
                padding: 8px;
                border-radius: 6px;
                margin-bottom: 10px;
            }
            .tarja-verde-ipec {
                background-color: #2e7d32;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 1.1em;
                margin-bottom: 12px;
                text-align: center;
                border: 1px solid #81c784;
                display: block;
                width: 100%;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            @keyframes pulsar-alerta {
                0% { opacity: 1.0; transform: scale(1); }
                50% { opacity: 0.4; transform: scale(1.02); }
                100% { opacity: 1.0; transform: scale(1); }
            }
            .aviso-nao-encontrado-pulsante {
                color: #d32f2f;
                font-weight: 900;
                font-size: 1.2em;
                text-align: center;
                padding: 15px;
                background-color: rgba(211, 47, 47, 0.1);
                border: 2px dashed #d32f2f;
                border-radius: 8px;
                margin: 20px 0;
                animation: pulsar-alerta 1.5s infinite ease-in-out;
            }
        </style>
    """, unsafe_allow_html=True)

def renderizar_cabecalho_principal():
    """Renderiza o cabeçalho centralizado com o logotipo da escola."""
    logo_base64 = ""
    try:
        path_logo = "imagens/Logo da Escola.jpeg"
        if os.path.exists(path_logo):
            with open(path_logo, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception: pass

    html_cabecalho = f"""
    <div class="header-container-centralizado">
        <img src="data:image/jpeg;base64,{logo_base64}" class="header-logo-img-cent">
        <p class="titulo-central-proporcional">🏫 SISTEMAS iPeC - Central de Trabalhos</p>
        <p class="escola-titulo-proporcional">ESCOLA MUNICIPAL PROFª GLÓRIA MOREIRA</p>
    </div>
    """
    st.markdown(html_cabecalho, unsafe_allow_html=True)
