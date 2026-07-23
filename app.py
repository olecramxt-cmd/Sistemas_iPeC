# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.17.24 - data: 23/07/26 - 12:57

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials
import os

# CONFIGURAÇÃO ESTRITA DA PÁGINA COM NOME CORRETO NA ABA DO NAVEGADOR
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

# COLORIZAÇÃO, ESTILIZAÇÃO CSS E FONTES ELEGANTES PARA OS TÍTULOS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Montserrat:wght@400;600;700&display=swap');

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f2b5c 0%, #1e4b8f 50%, #f7c325 100%);
            color: #ffffff !important;
            padding-top: 0rem !important;
        }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #ffffff !important;
        }
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
        button[key*="excluir"], button:has(div:contains("Excluir")) {
            background-color: #cc0000 !important;
            color: white !important;
            border: 1px solid #ff9999 !important;
        }
        button[key*="excluir"]:hover, button:has(div:contains("Excluir")):hover {
            background-color: #ff1a1a !important;
            color: white !important;
        }
        .sidebar-logo-footer {
            text-align: center;
            font-size: 0.72em;
            color: #ffffff;
            margin-top: -35px;
            margin-bottom: 2px;
            padding-bottom: 2px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            line-height: 1.2;
        }
        .profile-wrapper {
            text-align: center;
            margin-top: -15px;
            margin-bottom: 5px;
        }
        .profile-img-container {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #f7c325;
            margin: 0 auto 1px auto;
            display: block;
        }
        /* FONTES ELEGANTES E SOFISTICADAS PARA OS TÍTULOS SOLICITADOS */
        .titulo-central-elegante {
            font-family: 'Cinzel', serif;
            font-size: 1.8em;
            font-weight: 700;
            color: #0f2b5c;
            letter-spacing: 0.5px;
        }
        .escola-titulo-elegante {
            font-family: 'Montserrat', sans-serif;
            font-size: 1.25em;
            font-weight: 700;
            color: #1e4b8f;
            letter-spacing: 0.8px;
            margin-top: 12px;
        }
    </style>
""", unsafe_allow_html=True)

COLUNAS_OFICIAIS = [
    "Id.", "Ano Letivo", "Aluno", "Nascimento", "Idade", "PBF", "AEE/CID", "Naturalidade", "Nacionalidade",
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
    st.sidebar.image("imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception: pass

st.sidebar.markdown("""
    <div class="sidebar-logo-footer">
        Versão: v.17.24 de 23/07/2026<br>
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
    
    st.info("Por favor, realize o login na barra lateral para liberar as diretrizes do sistema.")
else:
    st.sidebar.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)
    url_foto = st.session_state['foto_usuario'].strip()
    if url_foto and "http" in url_foto:
        st.sidebar.markdown(f'<img src="{url_foto}" class="profile-img-container">', unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<h1 style='text-align:center; margin:0;'>👤</h1>", unsafe_allow_html=True)
        
    st.sidebar.markdown(f"<h3 style='text-align:center; margin: 0; padding: 0; color: #ffffff;'>{st.session_state['email_usuario'].split('@')[0]}</h3>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<div style='text-align:center; color:#f7c325; font-size:0.9em; margin: 0; padding: 0;'>Perfil: {st.session_state['perfil_usuario']}</div>", unsafe_allow_html=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Efetuou logout do sistema.")
        st.session_state["autenticado"] = False
        st.session_state["perfil_usuario"] = None
        st.rerun()

    # ==========================================
    # CENTRAL DE TRABALHOS: TÍTULOS ELEGANTES E LOGO DA ESCOLA
    # ==========================================
    st.markdown('<p class="titulo-central-elegante">🏫 SISTEMAS iPeC - Central de Trabalhos</p>', unsafe_allow_html=True)
    
    col_logo_esc, col_nome_esc = st.columns([0.08, 0.92])
    with col_logo_esc:
        try:
            if os.path.exists("imagens/Logo da Escola.jpeg"):
                st.image("imagens/Logo da Escola.jpeg", width=55)
            else:
                st.markdown("🏫")
        except Exception:
            st.markdown("🏫")
    with col_nome_esc:
        st.markdown('<p class="escola-titulo-elegante">ESCOLA MUNICIPAL PROFª GLÓRIA MOREIRA</p>', unsafe_allow_html=True)

    st.markdown("---")
    
    anos_disponiveis = ["Selecione...", "2026", "2027", "2028", "2029", "2030"]
    ano_letivo_escolhido = st.selectbox("📅 Informe o Ano Letivo de Trabalho:", anos_disponiveis, index=0)
    
    df_db_global = st.session_state["dados_banco"]

    if ano_letivo_escolhido == "Selecione...":
        st.info("ℹ️ Por favor, selecione o Ano Letivo acima para liberar o acesso aos módulos operacionais.")
    else:
        # FILTRAGEM SEGURA POR ANO
        df_db_ano = pd.DataFrame(columns=COLUNAS_OFICIAIS)
        if not df_db_global.empty and "Ano Letivo" in df_db_global.columns:
            df_db_ano = df_db_global[df_db_global["Ano Letivo"].astype(str).str.strip() == str(ano_letivo_escolhido)].copy()

        # LIBERAÇÃO DO MENU CORPORATIVO MESMO SE O ANO ESTIVER VAZIO (PARA PERMITIR IMPORTAÇÃO)
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
        if menu_principal == "📊 Painel de Controle de Conformidade e Indicadores de Alunos":
            st.markdown(f"### 📊 Painel de Controle - Ano Letivo: {ano_letivo_escolhido}")
            sub_conformidade = st.sidebar.radio("Sub-menu:", ["Cadastro dos alunos", "Atualização de Dados"])
            
            if df_db_ano.empty:
                st.warning(f"⚠️ Atenção: Não existem lançamentos ou registros ativos encontrados para o ano letivo de {ano_letivo_escolhido}. Utilize o menu '📥 Importação de Dados' para enviar os registros deste ano.")
            else:
                if "f_aluno" not in st.session_state: st.session_state.f_aluno = ""
                if "f_mae" not in st.session_state: st.session_state.f_mae = ""
                if "f_turma" not in st.session_state: st.session_state.f_turma = ""
                if "f_turno" not in st.session_state: st.session_state.f_turno = ""
                if "f_status" not in st.session_state: st.session_state.f_status = ""
                if "f_pbf" not in st.session_state: st.session_state.f_pbf = ""

                df_filtrado = df_db_ano.copy()
                if st.session_state.f_aluno: df_filtrado = df_filtrado[df_filtrado["Aluno"].str.contains(st.session_state.f_aluno, case=False)]
                if st.session_state.f_mae: df_filtrado = df_filtrado[df_filtrado["Mãe"].str.contains(st.session_state.f_mae, case=False)]
                if st.session_state.f_turma: df_filtrado = df_filtrado[df_filtrado["Turma"].str.contains(st.session_state.f_turma, case=False)]
                if st.session_state.f_turno: df_filtrado = df_filtrado[df_filtrado["Turno"].str.contains(st.session_state.f_turno, case=False)]
                if st.session_state.f_status: df_filtrado = df_filtrado[df_filtrado["Status"].str.contains(st.session_state.f_status, case=False)]
                if st.session_state.f_pbf: df_filtrado = df_filtrado[df_filtrado["PBF"].str.contains(st.session_state.f_pbf, case=False)]

                if sub_conformidade == "Cadastro dos alunos":
                    st.success(f"Banco de dados ativo ({ano_letivo_escolhido}) com {len(df_db_ano)} registros oficiais na nuvem.")
                    
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

                    st.markdown("#### 📋 Tabela de Registros (Edição Direta em Tempo Real)")
                    
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
                        b_col1, b_col2, b_col3 = st.columns(3)
                        
                        with b_col1:
                            if st.button("💾 Salvar"):
                                try:
                                    doc_w = conectar_planilha()
                                    aba_w = doc_w.get_worksheet(0)
                                    
                                    alteracoes_realizadas = 0
                                    with st.spinner("Verificando e salvando apenas os registros alterados..."):
                                        for idx, row_edit in df_editavel.iterrows():
                                            id_reg = row_edit["Id."]
                                            original_match = df_db_ano[df_db_ano["Id."] == id_reg]
                                            if not original_match.empty:
                                                row_orig = original_match.iloc[0]
                                                diferente = any(str(row_edit.get(c, "")) != str(row_orig.get(c, "")) for c in COLUNAS_OFICIAIS if c != "Idade")
                                                if diferente:
                                                    linha_planilha = int(id_reg) + 1
                                                    row_edit["Idade"] = calcular_idade_extenso(row_edit["Nascimento"])
                                                    valores_alinhados = [str(row_edit.get(c, "")) for c in COLUNAS_OFICIAIS]
                                                    aba_w.update(range_name=f"A{linha_planilha}:Z{linha_planilha}", values=[valores_alinhados])
                                                    alteracoes_realizadas += 1
                                                    time.sleep(0.3)
                                    
                                    if alteracoes_realizadas > 0:
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Atualizou {alteracoes_realizadas} registro(s) via tabela interativa ({ano_letivo_escolhido}).")
                                        st.success(f"🎉 {alteracoes_realizadas} registro(s) alterado(s) e salvo(s) direto na nuvem para {ano_letivo_escolhido}!")
                                        st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                        st.rerun()
                                    else:
                                        st.info("ℹ️ Nenhuma alteração foi detectada na tabela para salvar.")
                                except Exception as err:
                                    st.error(f"Erro ao salvar alterações: {err}")

                        with b_col2:
                            if st.button("➕ Incluir Aluno"):
                                try:
                                    doc_inc = conectar_planilha()
                                    aba_inc = doc_inc.get_worksheet(0)
                                    
                                    proximo_id_val = len(carregar_banco_dados_virtual()) + 1
                                    novo_registro_vazio = {c: ("Não" if c == "PBF" else "Ativo" if c == "Status" else str(ano_letivo_escolhido) if c == "Ano Letivo" else "Não informado") for c in COLUNAS_OFICIAIS}
                                    novo_registro_vazio["Id."] = proximo_id_val
                                    novo_registro_vazio["Aluno"] = f"Novo Aluno {proximo_id_val}"
                                    
                                    valores_novo = [str(novo_registro_vazio.get(c, "")) for c in COLUNAS_OFICIAIS]
                                    aba_inc.append_row(valores_novo)
                                    
                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Incluiu novo registro vazio ID {proximo_id_val} para {ano_letivo_escolhido}.")
                                    st.success(f"🎉 Novo registro ID {proximo_id_val} incluído com sucesso na nuvem para {ano_letivo_escolhido}!")
                                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                    st.rerun()
                                except Exception as err_inc:
                                    st.error(f"Erro ao incluir: {err_inc}")

                        with b_col3:
                            lista_exclusao = [f"{int(r['Id.'])} - {r['Aluno']}" for _, r in df_db_ano.iterrows()]
                            aluno_a_excluir = st.selectbox("Selecionar para Exclusão:", ["Selecione..."] + lista_exclusao, key="sel_exc_aluno")
                            
                            if st.button("🗑️ Excluir Aluno Selecionado", key="btn_exec_excluir_aluno"):
                                if aluno_a_excluir and aluno_a_excluir != "Selecione...":
                                    st.session_state["confirmar_exclusao_aluno"] = aluno_a_excluir
                                else:
                                    st.warning("⚠️ Selecione um aluno válido para exclusão.")
                            
                            if "confirmar_exclusao_aluno" in st.session_state and st.session_state["confirmar_exclusao_aluno"]:
                                aluno_alvo_str = st.session_state["confirmar_exclusao_aluno"]
                                st.error(f"⚠️ Confirmação: O aluno **{aluno_alvo_str}** realmente deve ser excluído?")
                                c_conf1, c_conf2 = st.columns(2)
                                with c_conf1:
                                    if st.button("Sim, Excluir"):
                                        try:
                                            id_exc = int(aluno_alvo_str.split(" - ")[0])
                                            doc_exc = conectar_planilha()
                                            aba_exc = doc_exc.get_worksheet(0)
                                            
                                            linha_planilha_alvo = id_exc + 1
                                            aba_exc.delete_rows(linha_planilha_alvo)
                                            
                                            df_atualizado = carregar_banco_dados_virtual()
                                            df_atualizado = df_atualizado[df_atualizado["Id."] != id_exc].copy()
                                            
                                            if not df_atualizado.empty:
                                                df_atualizado["Id."] = range(1, len(df_atualizado) + 1)
                                                dados_para_atualizar = [COLUNAS_OFICIAIS]
                                                for _, r_up in df_atualizado.iterrows():
                                                    dados_para_atualizar.append([str(r_up.get(c, "")) for c in COLUNAS_OFICIAIS])
                                                
                                                aba_exc.update(range_name=f"A1:Z{len(dados_para_atualizar)}", values=dados_para_atualizar)
                                            
                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Excluiu registro ID {id_exc} ({ano_letivo_escolhido}).")
                                            del st.session_state["confirmar_exclusao_aluno"]
                                            st.success(f"🗑️ Registro excluído e base reindexada com sucesso!")
                                            st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                            st.rerun()
                                        except Exception as err_exc:
                                            st.error(f"Erro ao excluir: {err_exc}")
                                with c_conf2:
                                    if st.button("Não, Voltar"):
                                        del st.session_state["confirmar_exclusao_aluno"]
                                        st.rerun()

        elif menu_principal == "📥 Importação de Dados":
            st.markdown(f"### 📥 Importação de Dados - Ano Letivo: {ano_letivo_escolhido}")
            sub_lote = st.sidebar.radio("Sub-menu:", ["Importar Arquivo .TXT", "Visualizar Histórico de Envio"])
            st.info(f"Sub-área '{sub_lote}' pronta para o ano letivo de {ano_letivo_escolhido}.")

        elif menu_principal == "📈 Relatórios":
            st.markdown(f"### 📈 Módulo de Relatórios Acadêmicos - Ano Letivo: {ano_letivo_escolhido}")
            sub_relatorios = st.sidebar.radio("Sub-menu:", ["Ficha Individual (PDF)", "Estatísticas PBF e AEE/CID"])
            st.info(f"Sub-área '{sub_relatorios}' pronta para {ano_letivo_escolhido}.")

        elif menu_principal == "👁️ Programa Miguilim":
            st.markdown(f"### 👁️ Programa Miguilim - Saúde Visual e Auditiva ({ano_letivo_escolhido})")
            sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Encaminhamentos Clínicos"])
            
            if sub_miguilim == "Triagem de Acuidade":
                st.markdown(f"#### 📋 Triagem de Acuidade Visual em Lote - {ano_letivo_escolhido}")
                
                if df_db_ano.empty:
                    st.warning(f"⚠️ Não existem alunos cadastrados para o ano letivo de {ano_letivo_escolhido}. Importe os dados primeiro.")
                else:
                    def formatar_turma_limpa(row):
                        p_ensino = str(row["Período de Ensino"]).strip()
                        t_turma = str(row["Turma"]).strip()
                        p_limpo = re.sub(r'[^a-zA-Z0-9]', '', p_ensino).lower()
                        t_limpo = re.sub(r'[^a-zA-Z0-9]', '', t_turma).lower()
                        if t_limpo in p_limpo or p_limpo in t_limpo:
                            return t_turma if len(t_turma) >= len(p_ensino) else p_ensino
                        if t_turma.upper().startswith(p_ensino.upper()):
                            return t_turma
                        return f"{p_ensino} - {t_turma}"

                    df_db_ano["Turma_Formatada"] = df_db_ano.apply(formatar_turma_limpa, axis=1)
                    
                    turmas_disponiveis = ["Selecione a Turma..."] + sorted(list(df_db_ano["Turma_Formatada"].dropna().unique()))
                    turma_selecionada = st.selectbox("🎯 Filtrar por Turma / Período de Ensino:", turmas_disponiveis)
                    
                    if turma_selecionada != "Selecione a Turma...":
                        df_miguilim_filtrado = df_db_ano[df_db_ano["Turma_Formatada"] == turma_selecionada]
                        
                        if df_miguilim_filtrado.empty:
                            st.info("ℹ️ Nenhum aluno localizado para a seleção informada.")
                        else:
                            st.markdown(f"Exibindo {len(df_miguilim_filtrado)} aluno(s) para triagem visual ({ano_letivo_escolhido}).")
                            
                            dados_tabela_mig = []
                            for _, r in df_miguilim_filtrado.iterrows():
                                dados_tabela_mig.append({
                                    "Id.": r["Id."],
                                    "Aluno": r["Aluno"],
                                    "CPF": r["CPF"],
                                    "Mãe": r["Mãe"],
                                    "Sem óculos(Dir)": "",
                                    "Sem óculos(Esq)": "",
                                    "Com óculos(Dir)": "",
                                    "Com óculos(Esq)": "",
                                    "Estrabismo": "Não",
                                    "PBF": r.get("PBF", "Não"),
                                    "Sem alteração": "Não",
                                    "Alteração Moderada": "Não",
                                    "Encaminhado": "Não",
                                    "Não examinado": "Não",
                                    "Uso do celular": "Não",
                                    "Observação": ""
                                })
                            
                            df_tabela_mig_edit = pd.DataFrame(dados_tabela_mig)
                            
                            escala_visao = ["", "0", "0,1", "0,13", "0,16", "0,2", "0,25", "0,3", "0,4", "0,5", "0,6", "0,8", "1"]
                            opcoes_sim_nao = ["Não", "Sim"]
                            opcoes_celular = ["Não", "1h", "2h", "3h", "4h", "5h", "6h", "7h", "8h", "Mais de 8h"]
                            
                            conf_colunas = {
                                "Id.": st.column_config.NumberColumn("Id.", disabled=True),
                                "Aluno": st.column_config.TextColumn("Aluno", disabled=True),
                                "CPF": st.column_config.TextColumn("CPF", disabled=True),
                                "Mãe": st.column_config.TextColumn("Mãe", disabled=True),
                                "PBF": st.column_config.TextColumn("PBF", disabled=True),
                                "Sem óculos(Dir)": st.column_config.SelectboxColumn("Sem óculos(Dir)", options=escala_visao, required=False),
                                "Sem óculos(Esq)": st.column_config.SelectboxColumn("Sem óculos(Esq)", options=escala_visao, required=False),
                                "Com óculos(Dir)": st.column_config.SelectboxColumn("Com óculos(Dir)", options=escala_visao, required=False),
                                "Com óculos(Esq)": st.column_config.SelectboxColumn("Com óculos(Esq)", options=escala_visao, required=False),
                                "Estrabismo": st.column_config.SelectboxColumn("Estrabismo", options=["Não", "Sim"], required=True),
                                "Sem alteração": st.column_config.SelectboxColumn("Sem alter.", options=opcoes_sim_nao, required=True),
                                "Alteração Moderada": st.column_config.SelectboxColumn("Alt. Mod.", options=opcoes_sim_nao, required=True),
                                "Encaminhado": st.column_config.SelectboxColumn("Encaminhado", options=opcoes_sim_nao, required=True),
                                "Não examinado": st.column_config.SelectboxColumn("Não exam.", options=opcoes_sim_nao, required=True),
                                "Uso do celular": st.column_config.SelectboxColumn("Uso celular", options=opcoes_celular, required=True),
                                "Observação": st.column_config.TextColumn("Observação", max_chars=500, default="")
                            }

                            df_miguilim_resultado = st.data_editor(
                                df_tabela_mig_edit,
                                column_config=conf_colunas,
                                use_container_width=True,
                                hide_index=True,
                                key="editor_miguilim_horizontal"
                            )
                            
                            if st.button("💾 Processar e Salvar Triagens em Lote"):
                                try:
                                    erros_validacao = []
                                    for idx, row_m in df_miguilim_resultado.iterrows():
                                        aluno_nome = row_m["Aluno"]
                                        sem_alt = str(row_m["Sem alteração"]) == "Sim"
                                        alt_mod = str(row_m["Alteração Moderada"]) == "Sim"
                                        encam = str(row_m["Encaminhado"]) == "Sim"
                                        nao_exam = str(row_m["Não examinado"]) == "Sim"
                                        
                                        if sem_alt and (alt_mod or encam):
                                            erros_validacao.append(f"Aluno {aluno_nome}: Se 'Sem alteração' for 'Sim', as opções 'Alteração Moderada' e 'Encaminhado' devem ser 'Não'.")
                                        if nao_exam and (sem_alt or alt_mod or encam):
                                            erros_validacao.append(f"Aluno {aluno_nome}: 'Não examinado' só pode ser 'Sim' se nenhuma outra condição clínica estiver ativa.")

                                    if erros_validacao:
                                        for e_val in erros_validacao:
                                            st.error(e_val)
                                    else:
                                        doc_mig = conectar_planilha()
                                        try:
                                            aba_mig = doc_mig.worksheet("miguilim_ipec")
                                        except gspread.WorksheetNotFound:
                                            aba_mig = doc_mig.add_worksheet(title="miguilim_ipec", rows="1000", cols="18")
                                            aba_mig.append_row([
                                                "Ano Letivo", "Turma", "Aluno", "CPF", "Mãe", 
                                                "Sem óculos(Dir)", "Sem óculos(Esq)", "Com óculos(Dir)", "Com óculos(Esq)", 
                                                "Estrabismo", "PBF", "Sem alteração", "Alteração Moderada", 
                                                "Encaminhado", "Não examinado", "Uso do celular", "Observação", "Data_Hora"
                                            ])
                                        
                                        data_hora_atual = obter_horario_unai().strftime("%d/%m/%Y, %H:%M")
                                        linhas_para_salvar = []
                                        
                                        for _, row_m in df_miguilim_resultado.iterrows():
                                            linhas_para_salvar.append([
                                                str(ano_letivo_escolhido),
                                                str(turma_selecionada),
                                                str(row_m["Aluno"]),
                                                str(row_m["CPF"]),
                                                str(row_m["Mãe"]),
                                                str(row_m["Sem óculos(Dir)"]),
                                                str(row_m["Sem óculos(Esq)"]),
                                                str(row_m["Com óculos(Dir)"]),
                                                str(row_m["Com óculos(Esq)"]),
                                                str(row_m["Estrabismo"]),
                                                str(row_m["PBF"]),
                                                str(row_m["Sem alteração"]),
                                                str(row_m["Alteração Moderada"]),
                                                str(row_m["Encaminhado"]),
                                                str(row_m["Não examinado"]),
                                                str(row_m["Uso do celular"]),
                                                str(row_m["Observação"])[:500],
                                                data_hora_atual
                                            ])
                                        
                                        if linhas_para_salvar:
                                            aba_mig.append_rows(linhas_para_salvar)
                                        
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Salvou triagens em lote Miguilim ({ano_letivo_escolhido}) - Turma: {turma_selecionada}")
                                        st.success(f"🎉 Triagens da turma salvas com sucesso na aba 'miguilim_ipec' para o ano de {ano_letivo_escolhido}!")
                                except Exception as err_mig:
                                    st.error(f"Erro ao salvar triagens na nuvem: {err_mig}")

            elif sub_miguilim == "Encaminhamentos Clínicos":
                st.markdown(f"### 📋 Encaminhamentos Clínicos — Programa Miguilim ({ano_letivo_escolhido})")
                st.info(f"Painel analítico de encaminhamentos para o ano letivo de {ano_letivo_escolhido}.")

        elif menu_principal == "📚 Programa Biblioteca":
            st.markdown(f"### 📚 Programa Biblioteca - Gestão Literária ({ano_letivo_escolhido})")
            sub_biblioteca = st.sidebar.radio("Sub-menu:", ["Catálogo do Acervo", "Empréstimos e Devoluções"])
            st.info(f"Módulo '{sub_biblioteca}' pronto para {ano_letivo_escolhido}.")

        elif menu_principal == "🛠️ Suporte":
            st.markdown(f"### 🛠️ Painel de Suporte e Auditoria de Infraestrutura ({ano_letivo_escolhido})")
            sub_suporte = st.sidebar.radio("Sub-menu:", ["Manual do Sistema", "Logs de Auditoria em Tempo Real"])
            if sub_suporte == "Logs de Auditoria em Tempo Real":
                try:
                    doc_s = conectar_planilha()
                    aba_log_s = doc_s.worksheet("log_auditoria_ipec")
                    df_logs = pd.DataFrame(aba_log_s.get_all_records())
                    st.dataframe(df_logs, use_container_width=True)
                except Exception:
                    st.error("Aba de logs ainda não possui registros inseridos.")
