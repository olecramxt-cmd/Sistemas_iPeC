# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa banco.py. Versão do Código: v.1.5.046
# Data de atualização: 26/07/2026 - 03:46
# Descrição das Alterações:
# - Isolamento seguro das funções de carregamento do banco de dados e planilhas de apoio.
# ==============================================================================

import streamlit as st
import pandas as pd
from modules.utils import conectar_planilha, calcular_idade_extenso, COLUNAS_OFICIAIS

@st.cache_data(ttl=600, show_spinner=False)
def carregar_banco_dados_virtual_cached():
    try:
        doc = conectar_planilha()
        aba = doc.get_worksheet(0)
        dados = aba.get_all_records()
        if not dados: return pd.DataFrame(columns=COLUNAS_OFICIAIS)
        df_bruto = pd.DataFrame(dados)
        
        colunas_encontradas = df_bruto.columns.tolist()
        coluna_ano_real = None
        for c in colunas_encontradas:
            if "ano" in str(c).lower():
                coluna_ano_real = c
                break
        
        if coluna_ano_real and coluna_ano_real != "Ano Letivo":
            df_bruto.rename(columns={coluna_ano_real: "Ano Letivo"}, inplace=True)

        if "Aluno" in df_bruto.columns:
            df_bruto = df_bruto[df_bruto["Aluno"].astype(str).str.strip() != ""]
        if df_bruto.empty: return pd.DataFrame(columns=COLUNAS_OFICIAIS)
        df_bruto["Id."] = range(1, len(df_bruto) + 1)
        
        if "Ano Letivo" not in df_bruto.columns:
            df_bruto["Ano Letivo"] = "2026"
        else:
            df_bruto["Ano Letivo"] = df_bruto["Ano Letivo"].astype(str).str.strip()
            df_bruto.loc[df_bruto["Ano Letivo"].isin(["", "nan", "NaN", "None", "Não informado"]), "Ano Letivo"] = "2026"

        if "Nascimento" in df_bruto.columns:
            df_bruto["Idade"] = df_bruto["Nascimento"].apply(calcular_idade_extenso)
        for col in COLUNAS_OFICIAIS:
            if col not in df_bruto.columns:
                df_bruto[col] = "Não informado" if col != "PBF" else "Não"
            else:
                df_bruto[col] = df_bruto[col].astype(str).str.strip().replace(["", "NaN", "nan", "None"], "Não informado")
        return df_bruto[COLUNAS_OFICIAIS]
    except Exception: return pd.DataFrame(columns=COLUNAS_OFICIAIS)

def carregar_banco_dados_virtual():
    return carregar_banco_dados_virtual_cached()

def carregar_dados_miguilim(ano_escolhido):
    try:
        doc = conectar_planilha()
        try:
            aba_mig = doc.worksheet("miguilim_ipec")
            registros = aba_mig.get_all_records()
            df_mig = pd.DataFrame(registros)
            if not df_mig.empty and "Ano Letivo" in df_mig.columns:
                return df_mig[df_mig["Ano Letivo"].astype(str).str.strip() == str(ano_escolhido)]
        except Exception: pass
    except Exception: pass
    return pd.DataFrame()

def carregar_acervo_biblioteca():
    try:
        doc = conectar_planilha()
        try:
            aba_bib = doc.worksheet("biblioteca_acervo_ipec")
        except Exception:
            aba_bib = doc.add_worksheet(title="biblioteca_acervo_ipec", rows="10000", cols="8")
            aba_bib.append_row(["Tombo", "Titulo", "Autor", "Categoria", "Disciplina", "Total", "Disponiveis", "Status"])
        registros = aba_bib.get_all_records()
        return pd.DataFrame(registros) if registros else pd.DataFrame(columns=["Tombo", "Titulo", "Autor", "Categoria", "Disciplina", "Total", "Disponiveis", "Status"])
    except Exception:
        return pd.DataFrame(columns=["Tombo", "Titulo", "Autor", "Categoria", "Disciplina", "Total", "Disponiveis", "Status"])

def carregar_emprestimos_biblioteca():
    try:
        doc = conectar_planilha()
        try:
            aba_emp = doc.worksheet("biblioteca_emprestimos_ipec")
        except Exception:
            aba_emp = doc.add_worksheet(title="biblioteca_emprestimos_ipec", rows="10000", cols="11")
            aba_emp.append_row(["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])
        registros = aba_emp.get_all_records()
        return pd.DataFrame(registros) if registros else pd.DataFrame(columns=["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])
    except Exception:
        return pd.DataFrame(columns=["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])

def carregar_config_biblioteca():
    try:
        doc = conectar_planilha()
        try:
            aba_cfg = doc.worksheet("biblioteca_config_ipec")
        except Exception:
            aba_cfg = doc.add_worksheet(title="biblioteca_config_ipec", rows="10", cols="3")
            aba_cfg.append_row(["Chave", "Valor"])
            aba_cfg.append_row(["PrazoLiterarioDias", 14])
            aba_cfg.append_row(["DataFixaDidatico", "15/12/2026"])
            aba_cfg.append_row(["LimiteLiterario", 2])
        registros = aba_cfg.get_all_records()
        cfg_dict = {"PrazoLiterarioDias": 14, "DataFixaDidatico": "15/12/2026", "LimiteLiterario": 2}
        for r in registros:
            chave = str(r.get("Chave", "")).strip()
            valor = r.get("Valor", "")
            if chave: cfg_dict[chave] = valor
        return cfg_dict
    except Exception:
        return {"PrazoLiterarioDias": 14, "DataFixaDidatico": "15/12/2026", "LimiteLiterario": 2}
