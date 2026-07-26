# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa banco.py. Versão do Código: v.1.5.053
# Data de atualização: 26/07/2026 - 06:11
# Descrição das Alterações:
#   - Inclusão oficial da funcao carregar_dados_pbf para o modulo banco.py.
# ==============================================================================

import streamlit as st
import pandas as pd
from modules.utils import conectar_planilha

@st.cache_data(ttl=600)
def carregar_banco_dados_virtual():
    """Carrega a base oficial de alunos da nuvem (Google Planilhas)."""
    try:
        doc = conectar_planilha()
        aba = doc.get_worksheet(0)
        dados = aba.get_all_records()
        if dados:
            return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_dados_miguilim(ano_letivo):
    """Carrega os registros de triagem do Programa Miguilim da nuvem."""
    try:
        doc = conectar_planilha()
        aba = doc.worksheet("miguilim_ipec")
        dados = aba.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            if "Ano Letivo" in df.columns:
                return df[df["Ano Letivo"].astype(str).str.strip() == str(ano_letivo)].copy()
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_acervo_biblioteca():
    """Carrega o acervo de livros da biblioteca da nuvem."""
    try:
        doc = conectar_planilha()
        aba = doc.worksheet("biblioteca_acervo_ipec")
        dados = aba.get_all_records()
        if dados:
            return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_emprestimos_biblioteca():
    """Carrega o registro de empréstimos da biblioteca da nuvem."""
    try:
        doc = conectar_planilha()
        aba = doc.worksheet("biblioteca_emprestimos_ipec")
        dados = aba.get_all_records()
        if dados:
            return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def carregar_config_biblioteca():
    """Carrega as configurações de prazos da biblioteca da nuvem."""
    try:
        doc = conectar_planilha()
        aba = doc.worksheet("biblioteca_config_ipec")
        dados = aba.get_all_records()
        if dados:
            return {r["Chave"]: r["Valor"] for r in dados}
    except Exception:
        pass
    return {"PrazoLiterarioDias": 14, "DataFixaDidatico": "15/12/2026", "LimiteLiterario": 2}

@st.cache_data(ttl=300)
def carregar_dados_pbf(ano_letivo, periodo):
    """Carrega os dados importados do Bolsa Família para o ano e período especificados."""
    try:
        doc = conectar_planilha()
        nome_aba = f"pbf_{ano_letivo}_{periodo.replace('/', '_').replace('.', '').lower()}"
        aba = doc.worksheet(nome_aba)
        dados = aba.get_all_records()
        if dados:
            return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame()
