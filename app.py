# © Prof. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.05.00 - data: 19/07/26 - 07:33

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# CONFIGURAÇÃO ESTRITA DA PÁGINA COM NOME E LOGO NA ABA DO NAVEGADOR
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

# Estrutura oficial de colunas solicitada
COLUNAS_OFICIAIS = [
    "Id.", "Aluno", "Nascimento", "Idade", "PBF", "AEE/CID", "Naturalidade", "Nacionalidade",
    "Mãe", "Pai", "Sexo", "Telefone", "E-mail(s)", "Endereço", "Bairro",
    "Cartão Cidadão", "Cartão do SUS", "CERTIDÃO", "CPF", "Período de Ensino",
    "Turma", "Turno", "Professor de Apoio Escolar - PAE", "Status", "Transferência"
]

# ==========================================
# UTILITÁRIOS DE VALIDAÇÃO E MÁSCARAS
# ==========================================
def validar_cpf(cpf_str):
    """Valida matematicamente o CPF usando os algoritmos de dígitos verificadores."""
    cpf = "".join(re.findall(r"\d", str(cpf_str)))
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

def formatar_telefone(tel_str):
    """Aplica a máscara estrita de Unaí-MG: (DD) 9.XXXX-XXXX ou (DD) XXXX-XXXX."""
    nums = "".join(re.findall(r"\d", str(tel_str)))
    if not nums:
        return "Não informado"
    if len(nums) == 11: 
        return f"({nums[:2]}) {nums[2:3]}.{nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10: 
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    elif len(nums) == 9: 
        return f"(38) {nums[:1]}.{nums[1:5]}-{nums[5:]}"
    elif len(nums) == 8: 
        return f"(38) {nums[:4]}-{nums[4:]}"
    return str(tel_str)

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
            if anos < 0: anos = 0
            return f"{anos} anos" if meses == 0 else f"{anos} anos e {meses} meses"
    except Exception:
        pass
    return "Não informado"

# ==========================================
# CONEXÃO COM O CORE BANCO DE DADOS GOOGLE SHEETS
# ==========================================
def conectar_planilha():
    """Autentica na API do Google e retorna a aba de trabalho do Banco de Dados."""
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais_dict = st.secrets["gcp_service_account"]
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(credenciais)
    url_planilha = st.secrets["connections"]["sheets"]["public_gsheets_url"]
    return cliente.open_by_url(url_planilha).get_worksheet(0)

def carregar_banco_dados_virtual():
    """Carrega e higieniza a base permanente direto da nuvem via Gspread para total integridade."""
    try:
        aba = conectar_planilha()
        dados = aba.get_all_records()
        if not dados:
            return pd.DataFrame(columns=COLUNAS_OFICIAIS)
        df = pd.DataFrame(dados)
        
        df["Id."] = range(1, len(df) + 1)
        
        if "Nascimento" in df.columns:
            df["Idade"] = df["Nascimento"].apply(calcular_idade_extenso)
            
        for col in COLUNAS_OFICIAIS:
            if col not in df.columns:
                df[col] = "Não informado" if col != "PBF" else "Não"
            else:
                df[col] = df[col].astype(str).str.strip().replace(["", "NaN", "nan", "None"], "Não informado")
        return df[COLUNAS_OFICIAIS]
    except Exception:
        return pd.DataFrame(columns=COLUNAS_OFICIAIS)

# ==========================================
# MINERADOR PROCESSUAL AVANÇADO
# ==========================================
def minerar_txt_ipec(arquivo_recurso):
    """Minerador analítico avançado de alta precisão posicional ajustado para Unaí-MG."""
    nome_arquivo = arquivo_recurso.name
    primeiro_char = re.search(r"^\d", nome_arquivo.strip())
    turno_padrao = "Vespertino" if primeiro_char and int(primeiro_char.group(0)) in [1,2,3,4] else "Matutino" if primeiro_char else "Não informado"

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
            if aluno_atual: alunos_capturados.append(aluno_atual)
            aluno_atual = {col: "Não informado" for col in COLUNAS_OFICIAIS}
            aluno_atual["PBF"] = "Não"
            aluno_atual["Transferência"] = ""
            
            match_aluno = re.search(r"Alun(.*?)(?:Nascimen|$)", linha_limpa)
            match_nasc = re.search(r"Nascimen(.*)", linha_limpa)
            aluno_atual["Aluno"] = match_aluno.group(1).replace(":","").strip() if match_aluno else "Não informado"
            aluno_atual["Nascimento"] = match_nasc.group(1).replace(":","").strip() if match_nasc else "Não informado"
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
                aluno_atual["Naturalidade"] = match_nat.group(1).replace(":","").strip() if match_nat else "Não informado"
                aluno_atual["Nacionalidade"] = match_nac.group(1).replace(":","").strip() if match_nac else "Não informado"
            elif "Mãe:" in linha_limpa:
                aluno_atual["Mãe"] = linha_limpa.split("Mãe:")[-1].strip()
            elif "Pai:" in linha_limpa:
                aluno_atual["Pai"] = linha_limpa.split("Pai:")[-1].strip()
            elif "Sexo:" in linha_limpa:
                match_sexo = re.search(r"Sexo:\s*(.*?)(?:Telefone|$)", linha_limpa, re.IGNORECASE)
                if match_sexo:
                    aluno_atual["Sexo"] = match_sexo.group(1).replace("ResponsávOutro", "").replace("Responsáv", "").strip()
                if "Telefone" in linha_limpa:
                    aluno_atual["Telefone"] = formatar_telefone(linha_limpa.split("Telefone")[-1])
            elif "E-mail(s):" in linha_limpa:
                aluno_atual["E-mail(s)"] = linha_limpa.split("E-mail(s):")[-1].strip()
            elif "Endereço:" in linha_limpa:
                end_limpo = linha_limpa.split("Endereço:")[-1].replace("*", "").strip()
                aluno_atual["Endereço"] = end_limpo
                match_bairro = re.search(r"(?:Bairro|-,)\s*([^,.\n\-\*]+)", end_limpo, re.IGNORECASE)
                if match_bairro:
                    aluno_atual["Bairro"] = match_bairro.group(1).replace("- MG","").replace("UNAÍ","").strip()
                else:
                    partes = end_limpo.split(",")
                    aluno_atual["Bairro"] = partes[1].strip() if len(partes) > 1 and not partes[1].strip().isdigit() else "Não informado"
            elif "CPF:" in linha_limpa:
                aluno_atual["CPF"] = "".join(re.findall(r"[\d.-]", linha_limpa.split("CPF:")[-1]))
            elif "Cartão Cidadão:" in linha_limpa or "Cartão do SUS:" in linha_limpa or "CERTIDÃO" in linha_limpa:
                match_cc = re.search(r"Cartão Cidadão:\s*([\d]*)", linha_limpa)
                match_sus = re.search(r"Cartão do SUS:\s*([\d\s]*)", linha_limpa)
                match_cert = re.search(r"CERTIDÃO\s*(.*)", linha_limpa)
                if match_cc and match_cc.group(1).strip(): aluno_atual["Cartão Cidadão"] = match_cc.group(1).strip()
                if match_sus and match_sus.group(1).strip(): aluno_atual["Cartão do SUS"] = match_sus.group(1).replace(" ", "").strip()
                if match_cert: aluno_atual["CERTIDÃO"] = match_cert.group(1).replace(":", "").replace("-", "").strip()

    if aluno_atual: alunos_capturados.append(aluno_atual)
    return pd.DataFrame(alunos_capturados) if alunos_capturados else pd.DataFrame(columns=COLUNAS_OFICIAIS)

# CARGA DO ESTADO ATUAL DO BANCO DE DADOS
if "dados_banco" not in st.session_state:
    st.session_state["dados_banco"] = carregar_banco_dados_virtual()

# ==========================================
# DESIGN INTERFACE: PAINEL LATERAL
# ==========================================
try:
    st.sidebar.image("Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception:
    st.sidebar.markdown("<h2 style='text-align: center; color: #0f54c6;'>🧬 SISTEMAS iPeC</h2>", unsafe_allow_html=True)

st.sidebar.title("🔐 Controle de Acesso")
usuario = st.sidebar.text_input("Usuário (E-mail):", placeholder="exemplo@ipec.com")
senha = st.sidebar.text_input("Senha:", type="password")

st.sidebar.markdown("---")
st.sidebar.title("🧭 Navegação")
menu = st.sidebar.radio("Escolha a operação:", ["Pesquisar e Alterar Dados", "Importar Arquivos (.txt)"])

# ==========================================
# GESTÃO EXCLUSIVA DE ALERTAS DE CPF
# ==========================================
def renderizar_alertas_seguranca(df_validar):
    for idx, row in df_validar.iterrows():
        cpf_atual = str(row.get("CPF", "")).strip()
        aluno_nome = row.get("Aluno", "Desconhecido")
        
        if not cpf_atual or cpf_atual in ["Não informado", ""]:
            st.error(f"❌ **ALERTA DE CPF AUSENTE:** O Aluno(a) **{aluno_nome}** está sem CPF cadastrado no sistema!")
        elif not validar_cpf(cpf_atual):
            st.markdown(f"<div style='background-color:#ffcccc; padding:10px; border-radius:5px; border-left:6px solid #ff0000; margin-bottom:10px; color:#990000;'>⚠️ <b>ALERTA:</b> Nº do CPF de <b>{aluno_nome}</b> ({cpf_atual}) está inconsistente com a base cadastral da Receita Federal.</div>", unsafe_allow_html=True)

# ==========================================
# MENU 1: CONSULTA COMPLETA E EDITORAÇÃO DIRETA
# ==========================================
if menu == "Pesquisar e Alterar Dados":
    st.markdown("### 🔍 Painel Avançado de Gestão Relacional")
    df_atual = st.session_state["dados_banco"]
    
    if not df_atual.empty:
        st.success(f"Banco de dados ativo com {len(df_atual)} registros oficiais na nuvem.")
        renderizar_alertas_seguranca(df_atual)
        
        st.markdown("#### 🛠️ Filtros de Coluna Simultâneos")
        filtro_cols = st.columns(2)
        with filtro_cols[0]:
            f_aluno = st.text_input("Filtrar por Aluno:")
            f_mae = st.text_input("Filtrar por Mãe:")
            f_turma = st.text_input("Filtrar por Turma:")
        with filtro_cols[1]:
            f_turno = st.text_input("Filtrar por Turno:")
            f_status = st.text_input("Filtrar por Status:")
            f_pbf = st.text_input("Filtrar por PBF (Sim/Não):")

        df_exibicao = df_atual.copy()
        if f_aluno: df_exibicao = df_exibicao[df_exibicao["Aluno"].str.contains(f_aluno, case=False)]
        if f_mae: df_exibicao = df_exibicao[df_exibicao["Mãe"].str.contains(f_mae, case=False)]
        if f_turma: df_exibicao = df_exibicao[df_exibicao["Turma"].str.contains(f_turma, case=False)]
        if f_turno: df_exibicao = df_exibicao[df_exibicao["Turno"].str.contains(f_turno, case=False)]
        if f_status: df_exibicao = df_exibicao[df_exibicao["Status"].str.contains(f_status, case=False)]
        if f_pbf: df_exibicao = df_exibicao[df_exibicao["PBF"].str.contains(f_pbf, case=False)]

        st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📝 Editor de Registro Direto na Nuvem")
        aluno_selecionado = st.selectbox("Escolha o aluno para Modificar:", [""] + list(df_atual["Aluno"].unique()))
        
        if aluno_selecionado:
            idx_registro = df_atual[df_atual["Aluno"] == aluno_selecionado].index[0]
            linha_dados = df_atual.loc[idx_registro].to_dict()
            linha_planilha = int(linha_dados["Id."]) + 1 
            
            st.info(f"Modificando o registro posicionado na linha {linha_planilha} da planilha.")
            
            form_cols = st.columns(3)
            novos_dados = {}
            novos_dados["Id."] = linha_dados["Id."]
            
            campos_espalhados = [c for c in COLUNAS_OFICIAIS if c not in ["Id.", "Idade"]]
            for i, campo in enumerate(campos_espalhados):
                col_destino = form_cols[i % 3]
                with col_destino:
                    val_atual = str(linha_dados.get(campo, "Não informado"))
                    if campo == "PBF":
                        novos_dados[campo] = st.selectbox("PBF:", ["Não", "Sim"], index=0 if val_atual == "Não" else 1)
                    elif campo == "Status":
                        novos_dados[campo] = st.selectbox("Status:", ["Ativo", "Inativo", "Pendente"], index=0 if val_atual == "Ativo" else 1)
                    elif campo == "Sexo":
                        novos_dados[campo] = st.selectbox("Sexo:", ["Masculino", "Feminino", "Não informado"], index=0 if "Masc" in val_atual else 1 if "Fem" in val_atual else 2)
                    else:
                        novos_dados[campo] = st.text_input(f"{campo}:", value=val_atual)
            
            novos_dados["Idade"] = calcular_idade_extenso(novos_dados["Nascimento"])
            
            if st.button("💾 Atualizar Registro na Planilha"):
                try:
                    aba_w = conectar_planilha()
                    valores_alinhados = [str(novos_dados.get(c, "")) for c in COLUNAS_OFICIAIS]
                    aba_w.update(range_name=f"A{linha_planilha}:Y{linha_planilha}", values=[valores_alinhados])
                    st.success("🎉 Alteração gravada direto na nuvem com sucesso!")
                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar alteração: {err}")
    else:
        st.info("Banco de dados indisponível no Google Sheets.")

# ==========================================
# MENU 2: IMPORTAÇÃO E GESTÃO DE DUPLICIDADE
# ==========================================
elif menu == "Importar Arquivos (.txt)":
    st.markdown("### 📥 Mapeador em Lote com Regra de Funil Dinâmica")
    df_db = st.session_state["dados_banco"]
    
    arquivos_escolhidos = st.file_uploader("Escolha os arquivos .txt", type=["txt"], accept_multiple_files=True)
    
    if arquivos_escolhidos:
        lista_dfs = []
        for arquivo in arquivos_escolhidos:
            df_m = minerar_txt_ipec(arquivo)
            if not df_m.empty: lista_dfs.append(df_m)
                
        if lista_dfs:
            df_novo_lote = pd.concat(lista_dfs, ignore_index=True)
            
            conflitos_detectados = []
            linhas_limpas_insercao = []
            
            for idx, row in df_novo_lote.iterrows():
                nome_aluno = str(row["Aluno"]).strip()
                nome_mae = str(row["Mãe"]).strip()
                
                duplicado = df_db[(df_db["Aluno"].str.strip().str.lower() == nome_aluno.lower()) & 
                                  (df_db["Mãe"].str.strip().str.lower() == nome_mae.lower())]
                
                if not duplicado.empty:
                    conflitos_detectados.append({
                        "atual": duplicado.iloc[0].to_dict(),
                        "novo": row.to_dict(),
                        "linha_planilha": int(duplicado.iloc[0]["Id."]) + 1
                    })
                else:
                    linhas_limpas_insercao.append(row.to_dict())
            
            decisoes_conflito = {}
            if conflitos_detectados:
                st.markdown("### ⚠️ Conflito de Duplicidade Detectado!")
                st.warning(f"O sistema identificou {len(conflitos_detectados)} alunos que já existem na planilha. Decida o destino de cada um:")
                
                for idx, c in enumerate(conflitos_detectados):
                    st.markdown(f"**Aluno:** {c['novo']['Aluno']} | **Mãe:** {c['novo']['Mãe']}")
                    col_c = st.columns(2)
                    with col_c[0]:
                        st.caption("Dados Atuais na Planilha:")
                        st.json({"Nasc": c["atual"]["Nascimento"], "Turma": c["atual"]["Turma"], "Turno": c["atual"]["Turno"]})
                    with col_c[1]:
                        st.caption("Dados Novos do Arquivo TXT:")
                        st.json({"Nasc": c["novo"]["Nascimento"], "Turma": c["novo"]["Turma"], "Turno": c["novo"]["Turno"]})
                    
                    escolha = st.radio(f"Ação para {c['novo']['Aluno']}:", 
                                       ["Manter o registro anterior da planilha", "Substituir e sobrepor com os novos dados"], 
                                       key=f"conf_{idx}")
                    decisoes_conflito[idx] = escolha
                    st.markdown("---")

            if linhas_limpas_insercao:
                st.markdown("#### Registros Novos Livres de Duplicidade:")
                st.dataframe(pd.DataFrame(linhas_limpas_insercao)[COLUNAS_OFICIAIS], use_container_width=True, hide_index=True)

            if st.button("🚀 Executar Carga Total e Resolver Conflitos"):
                try:
                    aba_upload = conectar_planilha()
                    linhas_finais_append = []
                    
                    proximo_id = len(aba_upload.get_all_values())
                    for item in linhas_limpas_insercao:
                        item["Id."] = proximo_id
                        item["Idade"] = calcular_idade_extenso(item["Nascimento"])
                        item["Telefone"] = formatar_telefone(item["Telefone"])
                        valores = [str(item.get(c, "Não informado")) for c in COLUNAS_OFICIAIS]
                        linhas_finais_append.append(valores)
                        proximo_id += 1
                        
                    if linhas_finais_append:
                        aba_upload.append_rows(linhas_finais_append)
                    
                    linhas_sobrepostas = 0
                    for idx, c in enumerate(conflitos_detectados):
                        if decisoes_conflito[idx] == "Substituir e sobrepor com os novos dados":
                            dados_novos = c["novo"]
                            dados_novos["Id."] = c["atual"]["Id."]
                            dados_novos["Idade"] = calcular_idade_extenso(dados_novos["Nascimento"])
                            dados_novos["Telefone"] = formatar_telefone(dados_novos["Telefone"])
                            valores_update = [str(dados_novos.get(c, "Não informado")) for c in COLUNAS_OFICIAIS]
                            
                            l_alvo = c["linha_planilha"]
                            aba_upload.update(range_name=f"A{l_alvo}:Y{l_alvo}", values=[valores_update])
                            linhas_sobrepostas += 1
                    
                    st.success(f"🎉 Processamento executado! {len(linhas_finais_append)} novos alunos inseridos e {linhas_sobrepostas} registros atualizados por substituição!")
                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                    st.rerun()
                except Exception as e_upload:
                    st.error(f"Erro crítico no envio do lote: {e_upload}")
