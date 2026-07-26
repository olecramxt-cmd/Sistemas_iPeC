# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa utils.py. Versão do Código: v.1.5.045
# Data de atualização: 26/07/2026 - 03:22
# Descrição das Alterações:
#   - Isolamento seguro das funções de conexão, horário oficial e logs de auditoria.
# ==============================================================================

import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

def obter_horario_unai():
    """Retorna o horário oficial sincronizado com Unaí-MG (GMT-3)."""
    return datetime.utcnow() - timedelta(hours=3)

def calcular_idade_extenso(data_nasc_str):
    """Calcula a idade em anos e meses de forma precisa com base na data de nascimento."""
    if not data_nasc_str or pd.isna(data_nasc_str) or str(data_nasc_str).strip() in ["Não informado", ""]:
        return "Não informado"
    try:
        match = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(data_nasc_str))
        if match:
            dia, mes, ano = map(int, match.groups())
            data_nasc = datetime(ano, mes, dia).date()
            hoje = obter_horario_unai().date()
            anos = hoje.year - data_nasc.year
            meses = hoje.month - data_nasc.month
            if hoje.month < data_nasc.month or (hoje.month == data_nasc.month and hoje.day < data_nasc.day):
                anos -= 1
                meses = 12 + (hoje.month - data_nasc.month)
            if hoje.day < data_nasc.day and meses > 0:
                meses -= 1
            if anos < 0: anos = 0
            return f"{anos} anos" if meses == 0 else f"{anos} anos e {meses} meses"
    except Exception: pass
    return "Não informado"

def conectar_planilha():
    """Realiza a conexão segura com o Google Sheets utilizando os segredos do Streamlit."""
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais_dict = st.secrets["gcp_service_account"]
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(credenciais)
    url_planilha = st.secrets["connections"]["sheets"]["public_gsheets_url"]
    return cliente.open_by_url(url_planilha)

def registrar_log_auditoria(usuario, perfil, acao):
    """Registra as ações dos usuários na aba de auditoria com carimbo de data/hora de Unaí-MG."""
    try:
        doc = conectar_planilha()
        try:
            aba_log = doc.worksheet("log_auditoria_ipec")
        except gspread.WorksheetNotFound:
            aba_log = doc.add_worksheet(title="log_auditoria_ipec", rows="1000", cols="4")
            aba_log.append_row(["Data_Hora", "Usuario", "Perfil", "Acao"])
        
        data_hora_atual = obter_horario_unai().strftime("%d/%m/%Y, %H:%M")
        aba_log.append_row([data_hora_atual, usuario, perfil, acao])
    except Exception: pass
