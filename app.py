# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.01.10 - data: 17/05/26

import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime

# CONFIGURAÇÃO ESTRITA DA PÁGINA
st.set_page_config(page_title="SISTEMAS iPeC - Gestão", layout="wide")

# Inicialização do controle de estado para mensagens primitivas
if "mensagem_sucesso" in st.session_state:
    st.success(st.session_state["mensagem_sucesso"])
    del st.session_state["mensagem_sucesso"]

# Estrutura oficial de colunas solicitada
COLUNAS_OFICIAIS = [
    "Id.", "Aluno", "Nascimento", "Idade", "PBF", "AEE/CID", "Naturalidade", "Nacionalidade",
    "Mãe", "Pai", "Sexo", "Telefone", "E-mail(s)", "Endereço", "Bairro",
    "Cartão Cidadão", "Cartão do SUS", "CERTIDÃO", "CPF", "Período de Ensino",
    "Turma", "Turno", "Professor de Apoio Escolar - PAE", "Status", "Transferência"
]

def calcular_idade_extenso(data_nasc_str):
    """Calcula a idade no formato: 'X anos e Y meses' ou 'X anos' se for o dia exato."""
    if not data_nasc_str or pd.isna(data_nasc_str) or str(data_nasc_str).strip() in ["Não informado", ""]:
        return "Não informado"
    try:
        match = re.search(r"(\d{2})/(\d{2})/(\d{4})", str(data_nasc_str))
        if match:
            dia, mes, ano = map(int, match.groups())
            data_nasc = datetime(ano, mes, dia).date()
            hoje = datetime.now().date()
            
            anos = hoje.year - data_nasc.year
            
            if hoje.month >= data_nasc.month:
                meses = hoje.month - data_nasc.month
            else:
                anos -= 1
                meses = 12 + (hoje.month - data_nasc.month)
                
            if hoje.day < data_nasc.day:
                if meses > 0:
                    meses -= 1
                else:
                    anos -= 1
                    meses = 11
                    
            if anos < 0:
                anos = 0
                
            if meses == 0:
                return f"{anos} anos"
            else:
                return f"{anos} anos e {meses} meses"
    except Exception:
        pass
    return "Não informado"

def minerar_txt_ipec(arquivo_recurso):
    """Minerador analítico avançado de alta precisão posicional para o padrão de Unaí-MG."""
    nome_arquivo = arquivo_recurso.name
    
    primeiro_char = re.search(r"^\d", nome_arquivo.strip())
    turno_padrao = "Não informado"
    if primeiro_char:
        num = int(primeiro_char.group(0))
        if num in [1, 2, 3, 4]:
            turno_padrao = "Vespertino"
        elif num in [5, 6, 7, 8, 9]:
            turno_padrao = "Matutino"

    try:
        linhas = arquivo_recurso.read().decode("utf-8").splitlines()
    except UnicodeDecodeError:
        arquivo_recurso.seek(0)
        linhas = arquivo_recurso.read().decode("cp1252").splitlines()

    alunos_capturados = []
    aluno_atual = {}
    
    periodo_ensino_doc = "Não informado"
    turma_doc = "Não informado"
    
    for linha in linhas:
        linha_limpa = linha.strip()
        
        if "Período de" in linha_limpa:
            periodo_ensino_doc = linha_limpa.split("Período de")[-1].replace("Ensino", "").replace(":", "").strip()
            continue
        elif "Turma:" in linha_limpa:
            turma_doc = linha_limpa.split("Turma:")[-1].strip()
            continue
            
        if "Alun" in linha_limpa and "Nascimen" in linha_limpa:
            if aluno_atual:
                alunos_capturados.append(aluno_atual)
            
            aluno_atual = {col: "Não informado" for col in COLUNAS_OFICIAIS}
            aluno_atual["PBF"] = "Não"
            aluno_atual["Transferência"] = "" 
            
            match_aluno = re.search(r"Alun(.*?)(?:Nascimen|$)", linha_limpa)
            match_nasc = re.search(r"Nascimen(.*)", linha_limpa)
            
            aluno_atual["Aluno"] = match_aluno.group(1).strip() if match_aluno else "Não informado"
            aluno_atual["Nascimento"] = match_nasc.group(1).strip() if match_nasc else "Não informado"
            aluno_atual["Idade"] = calcular_idade_extenso(aluno_atual["Nascimento"])
            aluno_atual["Período de Ensino"] = periodo_ensino_doc
            aluno_atual["Turma"] = turma_doc
            aluno_atual["Turno"] = turno_padrao
            aluno_atual["Status"] = "Ativo"
            continue
            
        if aluno_atual:
            if "Naturalida" in linha_limpa:
                match_nat = re.search(r"Naturalida(.*?)(?:Nacionalid|$)", linha_limpa)
                match_nac = re.search(r"Nacionalid(.*)", linha_limpa)
                aluno_atual["Naturalidade"] = match_nat.group(1).strip() if match_nat else "Não informado"
                aluno_atual["Nacionalidade"] = match_nac.group(1).strip() if match_nac else "Não informado"
                
            elif "Mãe:" in linha_limpa:
                aluno_atual["Mãe"] = linha_limpa.split("Mãe:")[-1].strip()
                
            elif "Pai:" in linha_limpa:
                aluno_atual["Pai"] = linha_limpa.split("Pai:")[-1].strip()
                
            elif "Sexo:" in linha_limpa:
                match_sexo = re.search(r"Sexo:\s*(.*?)(?:Telefone|$)", linha_limpa, re.IGNORECASE)
                if match_sexo:
                    sex_text = match_sexo.group(1).replace("ResponsávOutro", "").replace("Responsáv", "").strip()
                    aluno_atual["Sexo"] = sex_text if sex_text != "" else "Não informado"
                
                if "Telefone" in linha_limpa:
                    tel_text = linha_limpa.split("Telefone")[-1].replace(":", "").replace("-", "").strip()
                    aluno_atual["Telefone"] = tel_text if tel_text != "" else "Não informado"
                    
            elif "E-mail(s):" in linha_limpa:
                em_text = inline_em = linha_limpa.split("E-mail(s):")[-1].strip()
                aluno_atual["E-mail(s)"] = em_text if em_text != "" else "Não informado"
                
            elif "Endereço:" in linha_limpa:
                end_limpo = linha_limpa.split("Endereço:")[-1].replace("*", "").strip()
                aluno_atual["Endereço"] = end_limpo
                partes_end = [p.strip() for p in end_limpo.split(",")]
                if len(partes_end) > 1:
                    aluno_atual["Bairro"] = partes_end[1].replace(" - MG", "").replace("UNAÍ", "").strip()
                else:
                    aluno_atual["Bairro"] = "Não informado"
                    
            elif "Cartão Cidadão:" in linha_limpa or "Cartão do SUS:" in linha_limpa or "CERTIDÃO" in inline_cert if 'inline_cert' in locals() else linha_limpa:
                match_cc = re.search(r"Cartão Cidadão:\s*([\d]*)", linha_limpa)
                match_sus = re.search(r"Cartão do SUS:\s*([\d\s]*)", linha_limpa)
                match_cert = re.search(r"CERTIDÃO\s*(.*)", linha_limpa)
                
                if match_cc and match_cc.group(1).strip() != "":
                    aluno_atual["Cartão Cidadão"] = match_cc.group(1).strip()
                if match_sus and match_sus.group(1).strip() != "":
                    aluno_atual["Cartão do SUS"] = match_sus.group(1).replace(" ", "").strip()
                if match_cert:
                    c_val = match_cert.group(1).replace(":", "").replace("-", "").strip()
                    aluno_atual["CERTIDÃO"] = c_val if c_val != "" else "Não informado"
                    
            elif "CPF:" in linha_limpa:
                cpf_text = linha_limpa.split("CPF:")[-1].strip()
                aluno_atual["CPF"] = cpf_text if cpf_text != "" else "Não informado"

    if aluno_atual:
        alunos_capturados.append(aluno_atual)
        
    if alunos_capturados:
        df_res = pd.DataFrame(alunos_capturados)
        for col in COLUNAS_OFICIAIS:
            if col not in df_res.columns:
                if col == "PBF":
                    df_res[col] = "Não"
                elif col == "Transferência":
                    df_res[col] = ""
                else:
                    df_res[col] = "Não informado"
            else:
                if col == "PBF":
                    df_res[col] = df_res[col].apply(lambda x: "Não" if str(x).strip() not in ["Sim", "Não"] else str(x).strip())
                elif col != "Transferência":
                    df_res[col] = df_res[col].apply(lambda x: "Não informado" if str(x).strip() in ["", "NaN", "nan", "None"] else str(x).strip())
                else:
                    df_res[col] = df_res[col].apply(lambda x: "" if str(x).strip() in ["", "NaN", "nan", "None"] else str(x).strip())
        return df_res[COLUNAS_OFICIAIS]
    return pd.DataFrame(columns=COLUNAS_OFICIAIS)

def carregar_banco_dados_virtual():
    """Carrega a base permanente direto do Google Sheets via extração CSV da URL pública."""
    try:
        url_original = st.secrets["connections"]["sheets"]["public_gsheets_url"]
        
        if "/edit" in url_original:
            url_csv = url_original.split("/edit")[0] + "/gviz/tq?tqx=out:csv"
        else:
            url_csv = url_original
            
        df = pd.read_csv(url_csv)
        df = df.fillna("")
        
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_OFICIAIS)
            
        if "Nascimento" in df.columns:
            df["Idade"] = df["Nascimento"].apply(calcular_idade_extenso)
        
        for col in COLUNAS_OFICIAIS:
            if col not in df.columns:
                if col == "PBF":
                    df[col] = "Não"
                elif col == "Transferência":
                    df[col] = ""
                else:
                    df[col] = "Não informado"
            else:
                if col == "PBF":
                    df[col] = df[col].apply(lambda x: "Não" if str(x).strip() not in ["Sim", "Não"] else str(x).strip())
                elif col != "Transferência":
                    df[col] = df[col].apply(lambda x: "Não informado" if str(x).strip() in ["", "NaN", "nan", "None"] else str(x).strip())
                else:
                    df[col] = df[col].apply(lambda x: "" if str(x).strip() in ["", "NaN", "nan", "None"] else str(x).strip())
        return df[COLUNAS_OFICIAIS]
    except Exception:
        return pd.DataFrame(columns=COLUNAS_OFICIAIS)

# Ativação da carga do banco de dados
dados_tabela = carregar_banco_dados_virtual()

# ==========================================
# PAINEL LATERAL
# ==========================================
st.sidebar.title("🔐 Controle de Acesso")
usuario = st.sidebar.text_input("Usuário (E-mail):", placeholder="exemplo@ipec.com")
senha = st.sidebar.text_input("Senha:", type="password")

st.sidebar.markdown("---")
st.sidebar.title("🧭 Navegação")
menu = st.sidebar.radio("Escolha a operação:", ["Pesquisar e Alterar Dados", "Importar Arquivos (.txt)"])

# ==========================================
# MENU 1: CONSULTA COM MULTIFILTROS E EDIÇÃO
# ==========================================
if menu == "Pesquisar e Alterar Dados":
    st.markdown("### 🔍 Painel Avançado de Gestão Relacional")
    
    if not dados_tabela.empty:
        st.success(f"Banco de dados ativo com {len(dados_tabela)} registros.")
        
        st.markdown("#### 🛠️ Filtros de Coluna Simultâneos")
        filtro_cols = st.columns(2)
        with filtro_cols[0]:
            f_aluno = st.text_input("Filtrar por Aluno:")
            f_mae = st.text_input("Filtrar por Mãe:")
            f_cpf = st.text_input("Filtrar por CPF:")
            f_turma = st.text_input("Filtrar por Turma:")
        with filtro_cols[1]:
            f_turno = st.text_input("Filtrar por Turno:")
            f_cid = st.text_input("Filtrar por AEE/CID:")
            f_bairro = st.text_input("Filtrar por Bairro:")
            f_status = st.text_input("Filtrar por Status:")
            f_pbf = st.text_input("Filtrar por PBF (Sim/Não):")

        df_exibicao = dados_tabela.copy()
        if f_aluno: df_exibicao = df_exibicao[df_exibicao["Aluno"].astype(str).str.contains(f_aluno, case=False)]
        if f_mae: df_exibicao = df_exibicao[df_exibicao["Mãe"].astype(str).str.contains(f_mae, case=False)]
        if f_cpf: df_exibicao = df_exibicao[df_exibicao["CPF"].astype(str).str.contains(f_cpf, case=False)]
        if f_turma: df_exibicao = df_exibicao[df_exibicao["Turma"].astype(str).str.contains(f_turma, case=False)]
        if f_turno: df_exibicao = df_exibicao[df_exibicao["Turno"].astype(str).str.contains(f_turno, case=False)]
        if f_cid: df_exibicao = df_exibicao[df_exibicao["AEE/CID"].astype(str).str.contains(f_cid, case=False)]
        if f_bairro: df_exibicao = df_exibicao[df_exibicao["Bairro"].astype(str).str.contains(f_bairro, case=False)]
        if f_status: df_exibicao = df_exibicao[df_exibicao["Status"].astype(str).str.contains(f_status, case=False)]
        if f_pbf: df_exibicao = df_exibicao[df_exibicao["PBF"].astype(str).str.contains(f_pbf, case=False)]

        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
    else:
        st.info("O Banco de Dados Virtual está vazio no Google Sheets. Realize a importação em lote para alimentá-lo.")

# ==========================================
# MENU 2: IMPORTAÇÃO EM LOTE
# ==========================================
elif menu == "Importar Arquivos (.txt)":
    st.markdown("### 📥 Mapeador em Lote com Regra de Funil Dinâmica")
    
    arquivos_escolhidos = st.file_uploader("Escolha os arquivos .txt", type=["txt"], accept_multiple_files=True)
    
    if arquivos_escolhidos:
        lista_dfs = []
        for arquivo in arquivos_escolhidos:
            df_m = minerar_txt_ipec(arquivo)
            if not df_m.empty: lista_dfs.append(df_m)
                
        if lista_dfs:
            df_novo_lote = pd.concat(lista_dfs, ignore_index=True)
            st.markdown("#### Pré-visualização do Lote Processado:")
            st.dataframe(df_novo_lote, use_container_width=True, hide_index=True)
            
            if st.button("🚀 Executar Carga Total"):
                df_novo_lote["Id."] = range(1, len(df_novo_lote) + 1)
                st.success("🎉 Processamento de mineração concluído com sucesso!")
                st.dataframe(df_novo_lote[COLUNAS_OFICIAIS], use_container_width=True, hide_index=True)
                st.info("Pronto! Copie as linhas mineradas acima e alimente sua planilha do Drive para consolidação.")
