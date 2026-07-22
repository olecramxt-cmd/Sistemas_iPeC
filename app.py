# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.17.20 - data: 22/07/26 - 16:50

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials

# CONFIGURAÇÃO ESTRITA DA PÁGINA COM NOME E LOGO NA ABA DO NAVEGADOR
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

# COLORIZAÇÃO E ESTILIZAÇÃO CSS COM ISOLAMENTO CIRÚRGICO DO BOTÃO DE EXCLUSÃO
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
        /* ISOLAMENTO EXCLUSIVO: Apenas o botão de exclusão fica vermelho */
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
        
        # Mapeamento flexível para capturar variações no nome da coluna de ano ("Ano Le", "Ano", etc.)
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

# INTERFACE: SIDEBAR DE CONTROLE DE ACESSO (LIMPA, APENAS LOGO E DADOS)
try:
    st.sidebar.image("imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception: pass

st.sidebar.markdown("""
    <div class="sidebar-logo-footer">
        Versão: v.17.20 de 22/07/2026<br>
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
    # CENTRAL DE TRABALHOS: FILTRO GLOBAL DE ANO
    # ==========================================
    st.markdown("### 🏫 SISTEMAS iPeC - Central de Trabalhos")
    st.markdown("---")
    
    anos_disponiveis = ["Selecione...", "2026", "2027", "2028", "2029", "2030"]
    ano_letivo_escolhido = st.selectbox("📅 Informe o Ano Letivo de Trabalho:", anos_disponiveis, index=0)
    
    df_db_global = st.session_state["dados_banco"]

    if ano_letivo_escolhido == "Selecione...":
        st.info("ℹ️ Por favor, selecione o Ano Letivo acima para liberar o acesso aos módulos operacionais.")
    else:
        if not df_db_global.empty and "Ano Letivo" in df_db_global.columns:
            df_db_global = df_db_global[df_db_global["Ano Letivo"].astype(str).str.strip() == str(ano_letivo_escolhido)]

        if df_db_global.empty:
            st.warning(f"⚠️ Atenção: Não existem lançamentos ou registros ativos encontrados para o ano letivo de {ano_letivo_escolhido}.")
        else:
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
                        st.success(f"Banco de dados ativo ({ano_letivo_escolhido}) com {len(df_db_global)} registros oficiais na nuvem.")
                        
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
                                                original_match = df_db_global[df_db_global["Id."] == id_reg]
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
                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Atualizou {alteracoes_realizadas} registro(s) via tabela interativa.")
                                            st.success(f"🎉 {alteracoes_realizadas} registro(s) alterado(s) e salvo(s) direto na nuvem com sucesso!")
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
                                        st.success(f"🎉 Novo registro ID {proximo_id_val} incluído com sucesso na nuvem para {ano_letivo_escolhido}! Edite-o na tabela acima.")
                                        st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                        st.rerun()
                                    except Exception as err_inc:
                                        st.error(f"Erro ao incluir: {err_inc}")

                            with b_col3:
                                lista_exclusao = [f"{int(r['Id.'])} - {r['Aluno']}" for _, r in df_db_global.iterrows()]
                                aluno_a_excluir = st.selectbox("Selecionar para Exclusão:", ["Selecione..."] + lista_exclusao, key="sel_exc_aluno")
                                
                                # Botão de exclusão com estilização vermelha implacável
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
                                                
                                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Excluiu registro ID {id_exc} da planilha e reindexou base.")
                                                del st.session_state["confirmar_exclusao_aluno"]
                                                st.success(f"🗑️ Registro excluído e base reindexada com sucesso na nuvem!")
                                                st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                                st.rerun()
                                            except Exception as err_exc:
                                                st.error(f"Erro ao excluir: {err_exc}")
                                    with c_conf2:
                                        if st.button("Não, Voltar"):
                                            del st.session_state["confirmar_exclusao_aluno"]
                                            st.rerun()
                    else:
                        st.info("Banco de dados vazio ou redefinido.")
                        
            elif menu_principal == "📥 Importação de Dados":
                st.markdown(f"### 📥 Importação de Dados - Ano Letivo: {ano_letivo_escolhido}")
                sub_lote = st.sidebar.radio("Sub-menu:", ["Importar Arquivo .TXT", "Visualizar Histórico de Envio"])
                
                if sub_lote == "Importar Arquivo .TXT":
                    arquivos_escolhidos = st.file_uploader("Escolha os arquivos .txt", type=["txt"], accept_multiple_files=True)
                    if arquivos_escolhidos:
                        lista_dfs = []
                        for arquivo in arquivos_escolhidos:
                            df_m = minerar_txt_ipec(arquivo)
                            if not df_m.empty: 
                                df_m["Ano Letivo"] = ano_letivo_escolhido
                                lista_dfs.append(df_m)
                                
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
                                st.warning(f"O sistema identificou {len(conflitos_detectados)} alunos que já existem na planilha para {ano_letivo_escolhido}.")
                                
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
                                        item["Ano Letivo"] = ano_letivo_escolhido
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
                                            dados_novos["Ano Letivo"] = ano_letivo_escolhido
                                            dados_novos["Idade"] = calcular_idade_extenso(dados_novos["Nascimento"])
                                            dados_novos["Telefone"] = formatar_telefone(dados_novos["Telefone"])
                                            valores_update = [str(dados_novos.get(c, "Não informado")) for c in COLUNAS_OFICIAIS]
                                            l_alvo = c["linha_planilha"]
                                            aba_upload.update(range_name=f"A{l_alvo}:Z{l_alvo}", values=[valores_update])
                                            linhas_sobrepostas += 1
                                    
                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Importou lote .txt ({ano_letivo_escolhido}): {len(linhas_finais_append)} inseridos, {linhas_sobrepostas} sobrepostos.")
                                    st.success("🎉 Processamento executado com sucesso!")
                                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                    st.rerun()
                                except Exception as e_upload:
                                    st.error(f"Erro crítico no envio: {e_upload}")

            elif menu_principal == "📈 Relatórios":
                st.markdown(f"### 📈 Módulo de Relatórios Acadêmicos - Ano Letivo: {ano_letivo_escolhido}")
                sub_relatorios = st.sidebar.radio("Sub-menu:", ["Ficha Individual (PDF)", "Estatísticas PBF e AEE/CID"])
                st.info(f"Sub-área '{sub_relatorios}' pronta para desenvolvimento de layouts.")

            elif menu_principal == "👁️ Programa Miguilim":
                st.markdown(f"### 👁️ Programa Miguilim - Saúde Visual e Auditiva ({ano_letivo_escolhido})")
                sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Encaminhamentos Clínicos"])
                
                if sub_miguilim == "Triagem de Acuidade":
                    st.markdown("#### 📋 Triagem de Acuidade Visual em Lote (Layout Horizontal)")
                    
                    if df_db_global.empty:
                        st.warning("⚠️ O banco de dados está vazio. Cadastre ou importe alunos primeiro.")
                    else:
                        df_db_global["Turma_Formatada"] = df_db_global["Período de Ensino"].astype(str).str.strip() + " - " + df_db_global["Turma"].astype(str).str.strip()
                        
                        turmas_disponiveis = ["Selecione a Turma..."] + sorted(list(df_db_global["Turma_Formatada"].dropna().unique()))
                        turma_selecionada = st.selectbox("🎯 Filtrar por Turma / Período de Ensino:", turmas_disponiveis)
                        
                        if turma_selecionada != "Selecione a Turma...":
                            df_miguilim_filtrado = df_db_global[df_db_global["Turma_Formatada"] == turma_selecionada]
                            
                            if df_miguilim_filtrado.empty:
                                st.info("ℹ️ Nenhum aluno localizado para a seleção informada.")
                            else:
                                st.markdown(f"Exibindo {len(df_miguilim_filtrado)} aluno(s) para triagem visual.")
                                
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
                                        "Sem alteração": False,
                                        "Alteração Moderada": False,
                                        "Encaminhado": False,
                                        "Não examinado": False,
                                        "Uso do celular": "Não",
                                        "Observação": ""
                                    })
                                
                                df_tabela_mig_edit = pd.DataFrame(dados_tabela_mig)
                                
                                escala_visao = ["", "0", "0,1", "0,13", "0,16", "0,2", "0,25", "0,3", "0,4", "0,5", "0,6", "0,8", "1"]
                                
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
                                    "Sem alteração": st.column_config.CheckboxColumn("Sem alter.", default=False),
                                    "Alteração Moderada": st.column_config.CheckboxColumn("Alt. Mod.", default=False),
                                    "Encaminhado": st.column_config.CheckboxColumn("Encaminhado", default=False),
                                    "Não examinado": st.column_config.CheckboxColumn("Não exam.", default=False),
                                    "Uso do celular": st.column_config.SelectboxColumn("Uso celular", options=["Não", "Sim"], required=True),
                                    "Observação": st.column_config.TextColumn("Observação", default="")
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
                                                str(row_m["Observação"]),
                                                data_hora_atual
                                            ])
                                        
                                        if linhas_para_salvar:
                                            aba_mig.append_rows(linhas_para_salvar)
                                        
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Salvou triagens em lote Miguilim ({ano_letivo_escolhido}) - Turma: {turma_selecionada}")
                                        st.success("🎉 Todas as triagens da turma foram processadas e salvas com sucesso na aba exclusiva 'miguilim_ipec'!")
                                    except Exception as err_mig:
                                        st.error(f"Erro ao salvar triagens na nuvem: {err_mig}")

                elif sub_miguilim == "Encaminhamentos Clínicos":
                    st.markdown(f"### 📋 Encaminhamentos Clínicos — Programa Miguilim ({ano_letivo_escolhido})")
                    st.info("Painel analítico para listagem de alunos encaminhados e relatórios de acompanhamento clínico visual e auditivo.")

            elif menu_principal == "📚 Programa Biblioteca":
                st.markdown(f"### 📚 Programa Biblioteca - Gestão Literária ({ano_letivo_escolhido})")
                sub_biblioteca = st.sidebar.radio("Sub-menu:", ["Catálogo do Acervo", "Empréstimos e Devoluções"])
                st.info(f"Módulo '{sub_biblioteca}' pronto para controle de leituras.")

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
