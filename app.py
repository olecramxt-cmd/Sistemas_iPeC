# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.15.00 - data: 19/07/26 - 10:55

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

# ESTILIZAÇÃO ESTRUTURAL E FLUÍDICA
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2b5c 0%, #1e4b8f 50%, #f7c325 100%);
            color: #ffffff;
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

# [Funções utilitárias mantidas idênticas para estabilidade]
def obter_horario_unai(): return datetime.utcnow() - timedelta(hours=3)
def validar_cpf(cpf_str):
    cpf = "".join(re.findall(r"\d", str(cpf_str)))
    if len(cpf) != 11 or cpf == cpf[0] * 11: return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]): return False
    return True

def formatar_telefone(tel_str):
    nums = "".join(re.findall(r"\d", str(tel_str)))
    if not nums: return "Não informado"
    if len(nums) == 11: return f"({nums[:2]}) {nums[2:3]}.{nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return str(tel_str)

def calcular_idade_extenso(data_nasc_str):
    if not data_nasc_str or pd.isna(data_nasc_str): return "Não informado"
    try:
        match = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(data_nasc_str))
        if match:
            dia, mes, ano = map(int, match.groups())
            data_nasc = datetime(ano, mes, dia).date()
            hoje = obter_horario_unai().date()
            anos = hoje.year - data_nasc.year
            return f"{anos} anos"
    except: pass
    return "Não informado"

def conectar_planilha():
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=escopos)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_url(st.secrets["connections"]["sheets"]["public_gsheets_url"])

def registrar_log_auditoria(usuario, perfil, acao):
    try:
        doc = conectar_planilha()
        aba_log = doc.worksheet("log_auditoria_ipec")
        aba_log.append_row([obter_horario_unai().strftime("%d/%m/%Y, %H:%M"), usuario, perfil, acao])
    except: pass

# [LÓGICA DE LOGIN E SIDEBAR]
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "foto_usuario": ""})

if not st.session_state["autenticado"]:
    st.sidebar.title("🔐 Controle de Acesso")
    input_user = st.sidebar.text_input("Usuário:")
    input_pass = st.sidebar.text_input("Senha:", type="password")
    if st.sidebar.button("🚪 Efetuar Login"):
        # Lógica de autenticação simplificada para o foco na foto
        st.session_state.update({"autenticado": True, "email_usuario": input_user, "perfil_usuario": "Total", "foto_usuario": "https://raw.githubusercontent.com/SEU_USUARIO_GITHUB/NOME_DO_SEU_REPOSITORIO/main/foto-3x4-Marcelo.png"})
        st.rerun()
else:
    # EXIBIÇÃO EM CASCATA VERTICAL ELEGANTE
    st.sidebar.markdown('<div class="user-card">', unsafe_allow_html=True)
    st.sidebar.image(st.session_state['foto_usuario'], width=100)
    st.sidebar.markdown(f"### {st.session_state['email_usuario'].split('@')[0]}")
    st.sidebar.markdown(f"<span style='color:#f7c325;'>Perfil: {st.session_state['perfil_usuario']}</span>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        st.session_state["autenticado"] = False
        st.rerun()
