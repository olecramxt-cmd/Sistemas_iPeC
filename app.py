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

def carregar_banco_dados_virtual():
    """Carrega a base permanente direto do Google Sheets via extração CSV da URL pública."""
    try:
        # Puxa a URL configurada nos Secrets de forma limpa
        url_original = st.secrets["connections"]["sheets"]["public_gsheets_url"]
        
        # Converte a URL de visualização padrão do Google para o formato de exportação direta em CSV
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
    except Exception as e:
        # Se a planilha estiver vazia, retorna a estrutura oficial limpa
        return pd.DataFrame(columns=COLUNAS_OFICIAIS)

# Ativação da carga do banco de dados estável
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
        
        st.markdown("---")
        st.markdown("### 📝 Atualização de Ficha Individual (Pós-Importação)")
        st.warning("⚠️ Nota técnica: Para esta versão estável, utilize a aba de importação em lote para consolidar a base.")
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
                
                # Exibição do arquivo estruturado pronto para a planilha
                st.success("🎉 Processamento concluído com sucesso!")
                st.dataframe(df_novo_lote[COLUNAS_OFICIAIS], use_container_width=True, hide_index=True)
                st.info("Copie as linhas acima e cole na sua planilha do Drive para consolidar permanentemente.")
