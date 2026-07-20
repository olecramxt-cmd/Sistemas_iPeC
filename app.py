# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.17.01 - data: 20/07/26 - 10:17

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# CONFIGURAÇÃO ESTRITA DA PÁGINA COM NOME E LOGO NA ABA DO NAVEGADOR
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

# COLORIZAÇÃO E ESTILIZAÇÃO CSS COM SUAS CORREÇÕES MANUAIS DEFINITIVAS
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
        /* PUXA TODO O CONJUNTO DA BARRA LATERAL PARA O TOPO ABSOLUTO */
        [data-testid="stSidebar"] > div:first-child {
            margin-top: -35px !important;
        }
        .stRadio > div {
            background-color: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 8px;
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
        /* VERSÃO E COPYRIGHT COLADOS RENTE À LOGO */
        .sidebar-logo-footer {
            text-align: center;
            font-size: 0.72em;
            color: #ffffff;
            margin-top: -40px;
            margin-bottom: 2px;
            padding-bottom: 2px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            line-height: 1.2;
        }
        /* BLOCO DE PERFIL FACIADO, COMPACTO E CENTRALIZADO */
        .profile-wrapper {
            text-align: center;
            margin-top: -5px;
            margin-bottom: 5px;
        }
        .profile-img-container {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #f7c325;
            margin: 0 auto 2px auto;
            display: block;
        }
    </style>
""", unsafe_allow_html=True)

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
def obter_horario_unai():
    return datetime.utcnow() - timedelta(hours=3)

def validar_cpf(cpf_str):
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
    nums = "".join(re.findall(r"\d", str(tel_str)))
    if not nums: return "Não informado"
    if len(nums) == 11: return f"({nums[:2]}) {nums[2:3]}.{nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10: return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    elif len(nums) == 9: return f"(38) {nums[:1]}.{nums[1:5]}-{nums[5:]}"
    elif len(nums) == 8: return f"(38) {nums[:4]}-{nums[4:]}"
    return str(tel_str)

def calcular_idade_extenso(data_nasc_str):
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

# ==========================================
# BANCO DE DADOS E INFRAESTRUTURA DE AUDITORIA
# ==========================================
def conectar_planilha():
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciais_dict = st.secrets["gcp_service_account"]
    credenciais = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    cliente = gspread.authorize(credenciais)
    url_planilha = st.secrets["connections"]["sheets"]["public_gsheets_url"]
    return cliente.open_by_url(url_planilha)

def carregar_banco_dados_virtual():
    try:
        doc = conectar_planilha()
        aba = doc.get_worksheet(0)
        dados = aba.get_all_records()
        if not dados: return pd.DataFrame(columns=COLUNAS_OFICIAIS)
        df_bruto = pd.DataFrame(dados)
        if "Aluno" in df_bruto.columns:
            df_bruto = df_bruto[df_bruto["Aluno"].astype(str).str.strip() != ""]
        if df_bruto.empty: return pd.DataFrame(columns=COLUNAS_OFICIAIS)
        df_bruto["Id."] = range(1, len(df_bruto) + 1)
        if "Nascimento" in df_bruto.columns:
            df_bruto["Idade"] = df_bruto["Nascimento"].apply(calcular_idade_extenso)
        for col in COLUNAS_OFICIAIS:
            if col not in df_bruto.columns:
                df_bruto[col] = "Não informado" if col != "PBF" else "Não"
            else:
                df_bruto[col] = df_bruto[col].astype(str).str.strip().replace(["", "NaN", "nan", "None"], "Não informado")
        return df_bruto[COLUNAS_OFICIAIS]
    except Exception: return pd.DataFrame(columns=COLUNAS_OFICIAIS)

def registrar_log_auditoria(usuario, perfil, acao):
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

def gerenciar_autenticacao(user_input, pass_input):
    try:
        doc = conectar_planilha()
        try:
            aba_cred = doc.worksheet("credenciais_ipec")
        except gspread.WorksheetNotFound:
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

# ==========================================
# MINERADOR PROCESSUAL DE LOTES
# ==========================================
def minerar_txt_ipec(arquivo_recurso):
    nome_arquivo = arquivo_recurso.name
    primeiro_char = re.search(r"^\d", nome_arquivo.strip())
    turno_padrao = "Vespertino" if primeiro_char and int(primeiro_char.group(0)) in [1,2,3,4] else "Matutino" if primeiro_char else "Não informado"
    try:
        linhas = arquivo_recurso.read().decode("utf-8").splitlines()
    except UnicodeDecodeError:
        arquivo_recurso.seek(0)
        linhas = arquivo_recurso.read().decode("cp1252").splitlines()

    alunos_capturados, aluno_atual = [], {}
    periodo_ensino_doc, turma_doc = "Não informado", "Não informado"
    
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
            elif "Mãe:" in linha_limpa: aluno_atual["Mãe"] = linha_limpa.split("Mãe:")[-1].strip()
            elif "Pai:" in linha_limpa: aluno_atual["Pai"] = linha_limpa.split("Pai:")[-1].strip()
            elif "Sexo:" in linha_limpa:
                match_sexo = re.search(r"Sexo:\s*(.*?)(?:Telefone|$)", linha_limpa, re.IGNORECASE)
                if match_sexo: aluno_atual["Sexo"] = match_sexo.group(1).replace("ResponsávOutro", "").replace("Responsáv", "").strip()
                if "Telefone" in linha_limpa: aluno_atual["Telefone"] = formatar_telefone(linha_limpa.split("Telefone")[-1])
            elif "E-mail(s):" in linha_limpa: aluno_atual["E-mail(s)"] = linha_limpa.split("E-mail(s):")[-1].strip()
            elif "Endereço:" in linha_limpa:
                end_limpo = linha_limpa.split("Endereço:")[-1].replace("*", "").strip()
                aluno_atual["Endereço"] = end_limpo
                match_bairro = re.search(r"(?:Bairro|-,)\s*([^,.\n\-\*]+)", end_limpo, re.IGNORECASE)
                if match_bairro: aluno_atual["Bairro"] = match_bairro.group(1).replace("- MG","").replace("UNAÍ","").strip()
            elif "CPF:" in linha_limpa: aluno_atual["CPF"] = "".join(re.findall(r"[\d.-]", linha_limpa.split("CPF:")[-1]))
            elif "Cartão Cidadão:" in linha_limpa or "Cartão do SUS:" in linha_limpa or "CERTIDÃO" in linha_limpa:
                match_cc = re.search(r"Cartão Cidadão:\s*([\d]*)", linha_limpa)
                match_sus = re.search(r"Cartão do SUS:\s*([\d\s]*)", linha_limpa)
                match_cert = re.search(r"CERTIDÃO\s*(.*)", linha_limpa)
                if match_cc and match_cc.group(1).strip(): aluno_atual["Cartão Cidadão"] = match_cc.group(1).strip()
                if match_sus and match_sus.group(1).strip(): aluno_atual["Cartão do SUS"] = match_sus.group(1).replace(" ", "").strip()
                if match_cert: aluno_atual["CERTIDÃO"] = match_cert.group(1).replace(":", "").replace("-", "").strip()
    if aluno_atual: alunos_capturados.append(aluno_atual)
    return pd.DataFrame(alunos_capturados) if alunos_capturados else pd.DataFrame(columns=COLUNAS_OFICIAIS)

# ==========================================
# CONTROLE DE SESSÃO E CARGA DE DADOS
# ==========================================
if "dados_banco" not in st.session_state:
    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["perfil_usuario"] = None
    st.session_state["email_usuario"] = ""
    st.session_state["foto_usuario"] = ""

# INTERFACE: SIDEBAR DE CONTROLE DE ACESSO
try:
    st.sidebar.image("Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception: pass

# VERSÃO E COPYRIGHT COLADOS DIRETAMENTE ABAIXO DA LOGO
st.sidebar.markdown("""
    <div class="sidebar-logo-footer">
        Versão: v.17.01 de 20/07/2026<br>
        © Prof. Colab. Marcelo Xavier Travassos
    </div>
""", unsafe_allow_html=True)

if not st.session_state["autenticado"]:
    st.sidebar.title("🔐 Controle de Acesso")
    input_user = st.sidebar.text_input("Usuário (E-mail):", placeholder="exemplo@ipec.com")
    input_pass = st.sidebar.text_input("Senha:", type="password")
    if st.sidebar.button("🚪 Efetuar Login"):
        dados_auth = gerenciar_autenticacao(input_user, input_pass)
        if dados_auth:
            st.session_state["autenticado"] = True
            st.session_state["perfil_usuario"] = dados_auth["Perfil"]
            st.session_state["email_usuario"] = input_user
            st.session_state["foto_usuario"] = dados_auth["Foto"] if dados_auth["Foto"] else ""
            registrar_log_auditoria(input_user, dados_auth["Perfil"], "Efetuou login com sucesso.")
            st.rerun()
        else:
            st.sidebar.error("Credenciais incorretas.")
else:
    # PERFIL CENTRALIZADO E FACIADO
    st.sidebar.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)
    
    url_foto = st.session_state['foto_usuario'].strip()
    if url_foto and "http" in url_foto:
        st.sidebar.markdown(f'<img src="{url_foto}" class="profile-img-container">', unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<h1 style='text-align:center; margin:0;'>👤</h1>", unsafe_allow_html=True)
        
    st.sidebar.markdown(f"<h3 style='text-align:center; margin:0; color: #ffffff;'>{st.session_state['email_usuario'].split('@')[0]}</h3>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<div style='text-align:center; color:#f7c325; font-size:0.9em; margin-top:0;'>Perfil: {st.session_state['perfil_usuario']}</div>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Efetuou logout do sistema.")
        st.session_state["autenticado"] = False
        st.session_state["perfil_usuario"] = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.title("🧭 Menu Corporativo")
    
    opcoes_menu = ["📊 Painel de Controle de Conformidade e Indicadores de Alunos"]
    if st.session_state["perfil_usuario"] == "Total":
        opcoes_menu.append("📥 Importação de Dados")
    
    opcoes_menu.extend(["📈 Relatórios", "👁️ Programa Miguilim", "📚 Programa Biblioteca"])
    if st.session_state["perfil_usuario"] == "Total":
        opcoes_menu.append("🛠️ Suporte")
        
    menu_principal = st.sidebar.selectbox("Selecione a Área:", opcoes_menu)

# ==========================================
# OPERAÇÃO DE CADA MÓDULO E SUB-MENUS
# ==========================================
if st.session_state["autenticado"]:
    df_db_global = st.session_state["dados_banco"]

    # 1. PAINEL DE CONFORMIDADE
    if menu_principal == "📊 Painel de Controle de Conformidade e Indicadores de Alunos":
        st.markdown("### 📊 Painel de Controle de Conformidade e Indicadores de Alunos")
        sub_conformidade = st.sidebar.radio("Sub-menu:", ["Cadastro dos alunos", "Atualização de Dados"])
        
        if "f_aluno" not in st.session_state: st.session_state.f_aluno = ""
        if "f_mae" not in st.session_state: st.session_state.f_mae = ""
        if "f_turma" not in st.session_state: st.session_state.f_turma = ""
        if "f_turno" not in st.session_state: st.session_state.f_turno = ""
        if "f_status" not in st.session_state: st.session_state.f_status = ""
        if "f_pbf" not in st.session_state: st.session_state.f_pbf = ""

        df_filtrado = df_db_global.copy()
        if st.session_state.f_aluno: df_filtrado = df_filtrado[df_filtrado["Aluno"].str.contains(st.session_state.f_aluno, case=False)]
        if st.session_state.f_mae: df_filtrado = df_filtrado[df_filtrado["Mãe"].str.contains(st.session_state.f_mae, case=False)]
        if st.session_state.f_turma: df_filtrado = df_filtrado[df_filtrado["Turma"].str.contains(st.session_state.f_turma, case=False)]
        if st.session_state.f_turno: df_filtrado = df_filtrado[df_filtrado["Turno"].str.contains(st.session_state.f_turno, case=False)]
        if st.session_state.f_status: df_filtrado = df_filtrado[df_filtrado["Status"].str.contains(st.session_state.f_status, case=False)]
        if st.session_state.f_pbf: df_filtrado = df_filtrado[df_filtrado["PBF"].str.contains(st.session_state.f_pbf, case=False)]

        if sub_conformidade == "Cadastro dos alunos":
            if not df_db_global.empty:
                st.success(f"Banco de dados ativo com {len(df_db_global)} registros oficiais na nuvem.")
                
                st.markdown("#### 🛠️ Filtros de Coluna Simultâneos")
                filtro_cols = st.columns(2)
                with filtro_cols[0]:
                    st.session_state.f_aluno = st.text_input("Filtrar por Aluno:", value=st.session_state.f_aluno)
                    st.session_state.f_mae = st.text_input("Filtrar por Mãe:", value=st.session_state.f_mae)
                    st.session_state.f_turma = st.text_input("Filtrar por Turma:", value=st.session_state.f_turma)
                with filtro_cols[1]:
                    st.session_state.f_turno = st.text_input("Filtrar por Turno:", value=st.session_state.f_turno)
                    st.session_state.f_status = st.text_input("Filtrar por Status:", value=st.session_state.f_status)
                    st.session_state.f_pbf = st.text_input("Filtrar por PBF (Sim/Não):", value=st.session_state.f_pbf)

                st.markdown("#### 📋 Tabela de Registros (Edição Direta em Tempo Real / Validação ao Salvar)")
                
                def destacar_cpf_inconsistente(val):
                    cpf_str = str(val).strip()
                    if not cpf_str or cpf_str in ["Não informado", ""] or not validar_cpf(cpf_str):
                        return 'background-color: #ffcccc; color: #990000; font-weight: bold;'
                    return ''

                df_editavel = st.data_editor(
                    df_filtrado.style.map(destacar_cpf_inconsistente, subset=['CPF']),
                    use_container_width=True, 
                    hide_index=True,
                    key="editor_dados_tabela"
                )

                if st.session_state["perfil_usuario"] == "Total":
                    if st.button("💾 Salvar Alterações da Tabela na Nuvem"):
                        try:
                            doc_w = conectar_planilha()
                            aba_w = doc_w.get_worksheet(0)
                            
                            for idx, row_edit in df_editavel.iterrows():
                                id_reg = row_edit["Id."]
                                linha_planilha = int(id_reg) + 1
                                row_edit["Idade"] = calcular_idade_extenso(row_edit["Nascimento"])
                                valores_alinhados = [str(row_edit.get(c, "")) for c in COLUNAS_OFICIAIS]
                                aba_w.update(range_name=f"A{linha_planilha}:Y{linha_planilha}", values=[valores_alinhados])
                            
                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Atualizou registros em lote via tabela interativa.")
                            st.success("🎉 Todas as alterações validadas e salvas direto na nuvem com sucesso!")
                            st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                            st.rerun()
                        except Exception as err:
                            st.error(f"Erro ao salvar alterações: {err}")
            else:
                st.info("Banco de dados vazio ou redefinido.")
                
        elif sub_conformidade == "Atualização de Dados":
            if st.session_state["perfil_usuario"] != "Total":
                st.warning("⚠️ Seu perfil possui apenas permissão de leitura. Atualização bloqueada.")
            else:
                lista_mapeada = [""] + [f"{int(r['Id.'])} - {r['Aluno']}" for _, r in df_filtrado.iterrows()]
                
                st.markdown("#### 📝 Modificar Registro Pós-Pesquisa")
                st.caption(f"Exibindo {len(lista_mapeada)-1} registros localizados na filtragem.")
                
                opcao_escolhida = st.selectbox("Escolha o aluno para Atualizar:", lista_mapeada)
                
                # CORREÇÃO DEFINITIVA DO FORMULÁRIO DE ATUALIZAÇÃO (GARANTINDO A EXIBIÇÃO IMEDIATA)
                if opcao_escolhida and opcao_escolhida.strip() != "":
                    id_selecionado = int(opcao_escolhida.split(" - ")[0])
                    match_busca = df_db_global[df_db_global["Id."] == id_selecionado]
                    if not match_busca.empty:
                        linha_dados = match_busca.iloc[0].to_dict()
                        linha_planilha = id_selecionado + 1 
                        
                        st.info(f"Modo de sobreposição estrito ativo para a linha {linha_planilha} da planilha.")
                        form_cols = st.columns(3)
                        novos_dados = {"Id.": id_selecionado}
                        
                        campos_espalhados = [c for c in COLUNAS_OFICIAIS if c not in ["Id.", "Idade"]]
                        for i, campo in enumerate(campos_espalhados):
                            with form_cols[i % 3]:
                                val_atual = str(linha_dados.get(campo, "Não informado"))
                                if campo == "PBF":
                                    novos_dados[campo] = st.selectbox("PBF:", ["Não", "Sim"], index=0 if val_atual == "Não" else 1)
                                elif campo == "Status":
                                    novos_dados[campo] = st.selectbox("Status:", ["Ativo", "Inativo", "Pendente"], index=0 if val_atual == "Ativo" else 1)
                                elif campo == "Sexo":
                                    novos_dados[campo] = st.selectbox("Sexo:", ["Masculino", "Feminino", "Não informado"], index=0 if "Masc" in val_atual else 1 if "Fem" in val_atual else 2)
                                else:
                                    novos_dados[campo] = st.text_input(f"{campo}:", value=val_atual, key=f"inp_{campo}")
                        
                        novos_dados["Idade"] = calcular_idade_extenso(novos_dados["Nascimento"])
                        
                        if st.button("💾 Salvar Alterações na Planilha"):
                            try:
                                doc_w = conectar_planilha()
                                aba_w = doc_w.get_worksheet(0)
                                valores_alinhados = [str(novos_dados.get(c, "")) for c in COLUNAS_OFICIAIS]
                                aba_w.update(range_name=f"A{linha_planilha}:Y{linha_planilha}", values=[valores_alinhados])
                                
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Atualizou cadastro do aluno ID {id_selecionado}.")
                                st.success("🎉 Registro sobreposto com sucesso direto na nuvem!")
                                st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                st.rerun()
                            except Exception as err:
                                st.error(f"Erro ao salvar: {err}")

    # 2. IMPORTAÇÃO DE DADOS (Acesso restrito ao perfil Total)
    elif menu_principal == "📥 Importação de Dados":
        st.markdown("### 📥 Importação de Dados")
        sub_lote = st.sidebar.radio("Sub-menu:", ["Importar Arquivo .TXT", "Visualizar Histórico de Envio"])
        
        if sub_lote == "Importar Arquivo .TXT":
            arquivos_escolhidos = st.file_uploader("Escolha os arquivos .txt", type=["txt"], accept_multiple_files=True)
            if arquivos_escolhidos:
                lista_dfs = []
                for arquivo in arquivos_escolhidos:
                    df_m = minerar_txt_ipec(arquivo)
                    if not df_m.empty: lista_dfs.append(df_m)
                        
                if lista_dfs:
                    df_novo_lote = pd.concat(lista_dfs, ignore_index=True)
                    conflitos_detectados, linhas_limpas_insercao = [], []
                    
                    for idx, row in df_novo_lote.iterrows():
                        nome_aluno = str(row["Aluno"]).strip()
                        nome_mae = str(row["Mãe"]).strip()
                        
                        if df_db_global.empty:
                            linhas_limpas_insercao.append(row.to_dict())
                            continue
                        
                        duplicado = df_db_global[(df_db_global["Aluno"].str.strip().str.lower() == nome_aluno.lower()) & 
                                                 (df_db_global["Mãe"].str.strip().str.lower() == nome_mae.lower())]
                        
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
                        st.warning(f"O sistema identificou {len(conflitos_detectados)} alunos que já existem na planilha.")
                        
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
                            doc_u = conectar_planilha()
                            aba_upload = doc_u.get_worksheet(0)
                            linhas_finais_append = []
                            valores_existentes = aba_upload.get_all_values()
                            proximo_id = len(valores_existentes) if valores_existentes else 1
                            
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
                            
                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Importou lote .txt: {len(linhas_finais_append)} inseridos, {linhas_sobrepostas} sobrepostos.")
                            st.success("🎉 Processamento executado com sucesso!")
                            st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                            st.rerun()
                        except Exception as e_upload:
                            st.error(f"Erro crítico no envio: {e_upload}")

    # 3. RELATÓRIOS
    elif menu_principal == "📈 Relatórios":
        st.markdown("### 📈 Módulo de Relatórios Acadêmicos")
        sub_relatorios = st.sidebar.radio("Sub-menu:", ["Ficha Individual (PDF)", "Estatísticas PBF e AEE/CID"])
        st.info(f"Sub-área '{sub_relatorios}' pronta para desenvolvimento de layouts.")

    # 4. PROGRAMA MIGUILIM
    elif menu_principal == "👁️ Programa Miguilim":
        st.markdown("### 👁️ Programa Miguilim - Saúde Visual e Auditiva")
        sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Encaminhamentos Clínicos"])
        st.info(f"Módulo '{sub_miguilim}' pronto para receber parâmetros específicos.")

    # 5. PROGRAMA BIBLIOTECA
    elif menu_principal == "📚 Programa Biblioteca":
        st.markdown("### 📚 Programa Biblioteca - Gestão Literária")
        sub_biblioteca = st.sidebar.radio("Sub-menu:", ["Catálogo do Acervo", "Empréstimos e Devoluções"])
        st.info(f"Módulo '{sub_biblioteca}' pronto para controle de leituras.")

    # 6. SUPORTE (Acesso restrito ao perfil Total)
    elif menu_principal == "🛠️ Suporte":
        st.markdown("### 🛠️ Painel de Suporte e Auditoria de Infraestrutura")
        sub_suporte = st.sidebar.radio("Sub-menu:", ["Manual do Sistema", "Logs de Auditoria em Tempo Real"])
        if sub_suporte == "Logs de Auditoria em Tempo Real":
            try:
                doc_s = conectar_planilha()
                aba_log_s = doc_s.worksheet("log_auditoria_ipec")
                df_logs = pd.DataFrame(aba_log_s.get_all_records())
                st.dataframe(df_logs, use_container_width=True)
            except Exception:
                st.error("Aba de logs ainda não possui registros inseridos.")
else:
    st.info("Por favor, realize o login na barra lateral para liberar as diretrizes do sistema.")
