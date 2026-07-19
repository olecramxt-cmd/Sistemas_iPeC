# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.15.01 - data: 19/07/26 - 10:56

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# CONFIGURAÇÃO ESTRITA DA PÁGINA
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

# ESTILIZAÇÃO ESTRUTURAL E FLUÍDICA CORRIGIDA (CONTRASTE DE TEXTO)
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2b5c 0%, #1e4b8f 50%, #f7c325 100%);
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }
        .user-card {
            text-align: center;
            background-color: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(247, 195, 37, 0.5);
            margin-bottom: 20px;
        }
        .user-img {
            border-radius: 50%;
            border: 3px solid #f7c325;
            width: 100px;
            height: 100px;
            object-fit: cover;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# [Funções utilitárias e de banco de dados mantidas]
def obter_horario_unai(): return datetime.utcnow() - timedelta(hours=3)

def conectar_planilha():
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=escopos)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_url(st.secrets["connections"]["sheets"]["public_gsheets_url"])

def gerenciar_autenticacao(user_input, pass_input):
    try:
        doc = conectar_planilha()
        aba_cred = doc.worksheet("credenciais_ipec")
        registros = aba_cred.get_all_records()
        for r in registros:
            if str(r["Usuario"]).strip() == user_input.strip() and str(r["Senha"]).strip() == pass_input.strip():
                return {"Perfil": str(r["Perfil"]).strip(), "Foto": str(r.get("Foto", "")).strip()}
    except: pass
    return None

# [LÓGICA DE LOGIN COM CONTRASTE]
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False})

if not st.session_state["autenticado"]:
    st.sidebar.title("🔐 Controle de Acesso")
    input_user = st.sidebar.text_input("Usuário:", key="u_in")
    input_pass = st.sidebar.text_input("Senha:", type="password", key="p_in")
    if st.sidebar.button("🚪 Efetuar Login"):
        dados_auth = gerenciar_autenticacao(input_user, input_pass)
        if dados_auth:
            st.session_state.update({"autenticado": True, "email_usuario": input_user, "perfil_usuario": dados_auth["Perfil"], "foto_usuario": dados_auth["Foto"]})
            st.rerun()
        else:
            st.sidebar.error("Credenciais incorretas.")
else:
    st.sidebar.markdown('<div class="user-card">', unsafe_allow_html=True)
    if st.session_state['foto_usuario']:
        st.sidebar.image(st.session_state['foto_usuario'], width=100)
    else:
        st.sidebar.markdown("<h1>👤</h1>", unsafe_allow_html=True)
    st.sidebar.markdown(f"### {st.session_state['email_usuario'].split('@')[0]}")
    st.sidebar.markdown(f"<span style='color:#f7c325;'>Perfil: {st.session_state['perfil_usuario']}</span>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state["autenticado"] = False
        st.rerun()
