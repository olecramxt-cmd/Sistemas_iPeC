# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa autenticacao.py. Versão do Código: v.1.5.047
# Data de atualização: 26/07/2026 - 03:55
# Descrição das Alterações:
# - Isolamento seguro das funções de autenticação de usuários, perfis e credenciais.
# ==============================================================================

import streamlit as st
import gspread
from modules.utils import conectar_planilha, registrar_log_auditoria

def gerenciar_autenticacao(user_input, pass_input):
    """Verifica as credenciais do usuário na aba de credenciais da nuvem."""
    try:
        doc = conectar_planilha()
        try:
            aba_cred = doc.worksheet("credenciais_ipec")
        except Exception:
            aba_cred = doc.add_worksheet(title="credenciais_ipec", rows="100", cols="4")
            aba_cred.append_row(["Usuario", "Senha", "Perfil", "Foto"])
            aba_cred.append_row(["admin@ipec.com", "admin123", "Total", ""])
            aba_cred.append_row(["operador@ipec.com", "ipec123", "Parcial", ""])
        
        registros = aba_cred.get_all_records()
        for r in registros:
            if str(r["Usuario"]).strip() == user_input.strip() and str(r["Senha"]).strip() == pass_input.strip():
                return {
                    "Perfil": str(r["Perfil"]).strip(),
                    "Foto": str(r.get("Foto", "")).strip()
                }
    except Exception: pass
    return None
