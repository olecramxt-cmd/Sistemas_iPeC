# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.1.5.018 - data: 24/07/26 - 06:19

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
import time
import gspread
from google.oauth2.service_account import Credentials
import os
import base64

# CONFIGURAÇÃO ESTRITA DA PÁGINA
st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

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
            background-color: rgba(255, 255, 255, 0.15);
            padding: 10px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .stRadio label {
            color: #ffffff !important;
            font-weight: 600 !important;
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
        .header-container-unico {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 5px;
            margin-bottom: 10px;
        }
        .header-logo-img {
            width: 55px;
            height: auto;
            border-radius: 4px;
        }
        .header-textos-bloco {
            display: flex;
            flex-direction: column;
        }
        .titulo-central-elegante {
            font-family: 'Segoe UI Black', Arial, sans-serif;
            font-size: 32px;
            font-weight: 900;
            color: #0f2b5c;
            line-height: 1.1;
            margin: 0 0 3px 0;
        }
        .escola-titulo-elegante {
            font-family: 'Segoe UI Black', Arial, sans-serif;
            font-size: 19px;
            font-weight: 900;
            color: #1e4b8f;
            letter-spacing: 0.8px;
            margin: 0;
        }
        .sidebar-aviso-branco {
            color: #ffffff !important;
            font-size: 0.9em;
            background-color: rgba(255, 255, 255, 0.15);
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .tarja-verde-ipec {
            background-color: #2e7d32;
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 1.05em;
            margin-bottom: 15px;
            text-align: center;
            border: 1px solid #81c784;
        }
    </style>
""", unsafe_allow_html=True)

COLUNAS_OFICIAIS = [
    "Id.", "Ano Letivo", "Aluno", "Nascimento", "Idade", "PBF", "AEE/CID", "Naturalidade", "Nacionalidade",
    "Mãe", "Pai", "Sexo", "Telefone", "E-mail(s)", "Endereço", "Bairro",
    "Cartão Cidadão", "Cartão do SUS", "CERTIDÃO", "CPF", "Período de Ensino",
    "Turma", "Turno", "Professor de Apoio Escolar - PAE", "Status", "Transferência"
]

def obter_horario_unai():
    return datetime.utcnow() - timedelta(hours=3)

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

        for col in COLUNAS_OFICIAIS:
            if col not in df_bruto.columns:
                df_bruto[col] = "Não informado" if col != "PBF" else "Não"
            else:
                df_bruto[col] = df_bruto[col].astype(str).str.strip().replace(["", "NaN", "nan", "None"], "Não informado")
        return df_bruto[COLUNAS_OFICIAIS]
    except Exception: return pd.DataFrame(columns=COLUNAS_OFICIAIS)

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
        except gspread.WorksheetNotFound:
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
        except gspread.WorksheetNotFound:
            aba_emp = doc.add_worksheet(title="biblioteca_emprestimos_ipec", rows="10000", cols="11")
            aba_emp.append_row(["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])
        registros = aba_emp.get_all_records()
        return pd.DataFrame(registros) if registros else pd.DataFrame(columns=["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])
    except Exception:
        return pd.DataFrame(columns=["AnoLetivo", "Tombo", "Titulo", "Aluno", "Turma", "DataEmprestimo", "DataPrevista", "Status", "DataDevolucao", "Observacao"])

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

if "dados_banco" not in st.session_state:
    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["perfil_usuario"] = None
    st.session_state["email_usuario"] = ""
    st.session_state["foto_usuario"] = ""

# Inicialização limpa e vazia dos estados de seleção do acervo para garantir campos em branco se não houver clique
if "sel_tombo_reg" not in st.session_state: st.session_state.sel_tombo_reg = ""
if "sel_titulo_reg" not in st.session_state: st.session_state.sel_titulo_reg = ""
if "sel_autor_reg" not in st.session_state: st.session_state.sel_autor_reg = ""
if "sel_cat_reg" not in st.session_state: st.session_state.sel_cat_reg = "Didático"
if "sel_disc_reg" not in st.session_state: st.session_state.sel_disc_reg = ""
if "sel_total_reg" not in st.session_state: st.session_state.sel_total_reg = 1
if "acionou_exclusao_form" not in st.session_state: st.session_state.acionou_exclusao_form = False
if "tombo_para_excluir_seguro" not in st.session_state: st.session_state.tombo_para_excluir_seguro = ""

try:
    st.sidebar.image("imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception: pass

st.sidebar.markdown("""
    <div class="sidebar-logo-footer">
        Versão: v.1.5.018 de 24/07/2026<br>
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

    logo_base64 = ""
    try:
        path_logo = "imagens/Logo da Escola.jpeg"
        if os.path.exists(path_logo):
            with open(path_logo, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception: pass

    html_cabecalho = f"""
    <div class="header-container-unico">
        <img src="data:image/jpeg;base64,{logo_base64}" class="header-logo-img">
        <div class="header-textos-bloco">
            <p class="titulo-central-elegante">🏫 SISTEMAS iPeC - Central de Trabalhos</p>
            <p class="escola-titulo-elegante">ESCOLA MUNICIPAL PROFª GLÓRIA MOREIRA</p>
        </div>
    </div>
    """
    st.markdown(html_cabecalho, unsafe_allow_html=True)

    st.markdown("---")
    
    anos_disponiveis = ["Selecione...", "2026", "2027", "2028", "2029", "2030"]
    ano_letivo_escolhido = st.selectbox("📅 Informe o Ano Letivo de Trabalho:", anos_disponiveis, index=0)
    
    df_db_global = st.session_state["dados_banco"]

    if ano_letivo_escolhido == "Selecione...":
        st.info("ℹ️ Por favor, selecione o Ano Letivo acima para liberar o acesso aos módulos operacionais.")
    else:
        df_db_ano = pd.DataFrame(columns=COLUNAS_OFICIAIS)
        if not df_db_global.empty and "Ano Letivo" in df_db_global.columns:
            df_db_ano = df_db_global[df_db_global["Ano Letivo"].astype(str).str.strip() == str(ano_letivo_escolhido)].copy()

        st.sidebar.markdown("---")
        st.sidebar.title("🧭 Menu Corporativo")
        
        if df_db_ano.empty:
            st.sidebar.markdown(f'<div class="sidebar-aviso-branco">Ano {ano_letivo_escolhido} vazio. Utilize a Importação para cadastrar o lote inicial.</div>', unsafe_allow_html=True)
            opcoes_menu = ["📥 Importação de Dados"]
        else:
            opcoes_menu = ["📊 Painel de Controle de Conformidade e Indicadores de Alunos"]
            if st.session_state["perfil_usuario"] == "Total":
                opcoes_menu.append("📥 Importação de Dados")
            opcoes_menu.extend(["📈 Relatórios", "👁️ Programa Miguilim", "📚 Programa Biblioteca"])
            if st.session_state["perfil_usuario"] == "Total":
                opcoes_menu.append("🛠️ Suporte")
                
        menu_principal = st.sidebar.selectbox("Selecione a Área:", opcoes_menu)

        if menu_principal == "📊 Painel de Controle de Conformidade e Indicadores de Alunos":
            st.markdown(f"### 📊 Painel de Controle - Ano Letivo: {ano_letivo_escolhido}")
            sub_conformidade = st.sidebar.radio("Sub-menu:", ["Cadastro de Alunos", "Atualização de Dados"])
            
            if df_db_ano.empty:
                st.warning(f"⚠️ Atenção: Não existem lançamentos para o ano letivo de {ano_letivo_escolhido}.")
            else:
                st.success(f"Banco de dados ativo ({ano_letivo_escolhido}) com {len(df_db_ano)} registros oficiais na nuvem.")
                st.dataframe(df_db_ano, use_container_width=True, hide_index=True)

        elif menu_principal == "📥 Importação de Dados":
            st.markdown(f"### 📥 Módulo de Importação de Dados — Ano: {ano_letivo_escolhido}")
            sub_lote = st.sidebar.radio("Sub-menu:", ["Importar Arquivo .TXT", "Visualizar Histórico de Envio"])
            if sub_lote == "Importar Arquivo .TXT":
                st.info(f"Carregue os arquivos .TXT correspondentes para popular o ano letivo de {ano_letivo_escolhido}.")
                arquivos_escolhidos = st.file_uploader("Escolha os arquivos .txt", type=["txt"], accept_multiple_files=True)
                if arquivos_escolhidos:
                    st.success(f"{len(arquivos_escolhidos)} arquivo(s) carregado(s) com sucesso para processamento.")
            else:
                st.markdown("#### 📜 Histórico de Lotes Importados")
                try:
                    doc_h = conectar_planilha()
                    aba_h = doc_h.worksheet("historico_importacao_ipec")
                    df_hist = pd.DataFrame(aba_h.get_all_records())
                    if not df_hist.empty:
                        st.dataframe(df_hist, use_container_width=True)
                    else:
                        st.info("ℹ️ Nenhum histórico de envio registrado até o momento.")
                except Exception:
                    st.info("ℹ️ Aba de histórico de importação vazia ou não inicializada.")

        elif menu_principal == "📈 Relatórios":
            st.markdown(f"### 📈 Relatórios Gerais e Estatísticas — Ano: {ano_letivo_escolhido}")
            sub_relatorios = st.sidebar.radio("Sub-menu:", ["Ficha Individual (PDF)", "Estatísticas PBF e AEE/CID"])
            st.info(f"Sub-área '{sub_relatorios}' pronta.")

        elif menu_principal == "👁️ Programa Miguilim":
            st.markdown(f"### 👁️ Programa Miguilim — Gestão Oftalmológica e Saúde Escolar ({ano_letivo_escolhido})")
            sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Encaminhamentos Clínicos"])
            if sub_miguilim == "Triagem de Acuidade":
                st.markdown(f"#### 📋 Triagem de Acuidade Visual em Lote - {ano_letivo_escolhido}")
                if df_db_ano.empty:
                    st.warning("⚠️ Não existem alunos cadastrados para este ano letivo.")
                else:
                    st.success(f"Módulo Miguilim ativo com {len(df_db_ano)} alunos carregados para o ano de {ano_letivo_escolhido}.")
                    st.dataframe(df_db_ano[["Id.", "Ano Letivo", "Aluno", "Turma", "Turno", "Telefone"]], use_container_width=True, hide_index=True)
            else:
                st.markdown(f"### 📋 Encaminhamentos Clínicos — Programa Miguilim ({ano_letivo_escolhido})")
                st.info(f"Painel analítico de encaminhamentos para o ano de {ano_letivo_escolhido}.")

        elif menu_principal == "📚 Programa Biblioteca":
            st.markdown(f"### 📚 Programa Biblioteca - Gestão Literária ({ano_letivo_escolhido})")
            
            df_acervo_geral = carregar_acervo_biblioteca()
            df_ativos = df_acervo_geral[df_acervo_geral["Status"].astype(str).str.strip() != "INATIVO / EXCLUÍDO"] if not df_acervo_geral.empty else pd.DataFrame()
            
            total_lit = 0
            total_did = 0
            if not df_ativos.empty and "Categoria" in df_ativos.columns:
                cats = df_ativos["Categoria"].astype(str).str.strip().str.lower()
                total_lit = len(df_ativos[cats == "literário"])
                total_did = len(df_ativos[cats == "didático"])
            
            st.markdown(f'<div class="tarja-verde-ipec">📚 Total de Livros do Acervo Literário: {total_lit}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tarja-verde-ipec">📖 Total de Livros do Acervo Didático: {total_did}</div>', unsafe_allow_html=True)

            sub_biblioteca = st.sidebar.radio("Sub-menu:", [
                "Catálogo do Acervo", 
                "Empréstimos e Devoluções", 
                "Relatórios Gerais", 
                "Recibos", 
                "Relatório do Acervo", 
                "Relatório de Empréstimo", 
                "Gráficos"
            ])
            
            if sub_biblioteca == "Catálogo do Acervo":
                st.markdown(f"#### 📖 Gestão do Acervo Bibliográfico ({ano_letivo_escolhido})")
                
                df_emprestimos_geral = carregar_emprestimos_biblioteca()
                
                st.markdown("##### 🔍 Pesquisa de Obras no Acervo")
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    termo_titulo = st.text_input("Filtrar por Título da Obra:")
                with col_p2:
                    termo_autor = st.text_input("Filtrar por Autor / Organizador:")
                with col_p3:
                    filtro_cat = st.selectbox("Filtrar por Categoria:", ["Todas", "Didático", "Literário"])

                df_acervo_filtrado = df_acervo_geral.copy()
                if not df_acervo_filtrado.empty:
                    if termo_titulo:
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Titulo"].str.contains(termo_titulo, case=False, na=False)]
                    if termo_autor:
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Autor"].str.contains(termo_autor, case=False, na=False)]
                    if filtro_cat != "Todas":
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Categoria"].str.strip() == filtro_cat]

                st.markdown("##### 📋 Acervo Localizado (Clique na linha para carregar no formulário abaixo)")
                if not df_acervo_filtrado.empty:
                    tabela_evento = st.dataframe(
                        df_acervo_filtrado, 
                        use_container_width=True, 
                        hide_index=True, 
                        selection_mode="single-row", 
                        on_select="rerun",
                        key="tabela_acervo_selecao_v6"
                    )
                    
                    try:
                        linhas_selecionadas = tabela_evento.get("selection", {}).get("rows", [])
                        if linhas_selecionadas:
                            idx_sel = linhas_selecionadas[0]
                            livro_selecionado_linha = df_acervo_filtrado.iloc[idx_sel]
                            
                            st.session_state.sel_tombo_reg = str(livro_selecionado_linha.get("Tombo", ""))
                            st.session_state.sel_titulo_reg = str(livro_selecionado_linha.get("Titulo", ""))
                            st.session_state.sel_autor_reg = str(livro_selecionado_linha.get("Autor", ""))
                            st.session_state.sel_cat_reg = str(livro_selecionado_linha.get("Categoria", "Didático"))
                            st.session_state.sel_disc_reg = str(livro_selecionado_linha.get("Disciplina", ""))
                            st.session_state.sel_total_reg = 1
                        else:
                            # Se nenhuma linha estiver selecionada, garante que os campos fiquem absolutamente em branco
                            st.session_state.sel_tombo_reg = ""
                            st.session_state.sel_titulo_reg = ""
                            st.session_state.sel_autor_reg = ""
                            st.session_state.sel_cat_reg = "Didático"
                            st.session_state.sel_disc_reg = ""
                            st.session_state.sel_total_reg = 1
                    except Exception: 
                        st.session_state.sel_tombo_reg = ""
                        st.session_state.sel_titulo_reg = ""
                        st.session_state.sel_autor_reg = ""
                        st.session_state.sel_cat_reg = "Didático"
                        st.session_state.sel_disc_reg = ""
                        st.session_state.sel_total_reg = 1
                else:
                    st.info("ℹ️ Nenhum livro cadastrado ou localizado com os filtros informados.")

                st.markdown("---")
                st.markdown("##### ✍️ Cadastro de Livro e Alteração (Reativo ao Clique)")
                
                # Campos reativos alimentados pelas variáveis da sessão (garantindo limpeza total se não houver seleção)
                input_tombo = st.text_input("Código de Tombo / ISBN Base:", value=st.session_state.sel_tombo_reg, key="input_tombo_ui")
                input_titulo = st.text_input("Título da Obra:", value=st.session_state.sel_titulo_reg, key="input_titulo_ui")
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    input_autor = st.text_input("Autor / Organizador:", value=st.session_state.sel_autor_reg, key="input_autor_ui")
                with col_f2:
                    cat_idx_val = 0 if st.session_state.sel_cat_reg == "Didático" else 1
                    input_cat = st.selectbox("Categoria:", ["Didático", "Literário"], index=cat_idx_val, key="input_cat_ui")
                
                col_f3, col_f4 = st.columns(2)
                with col_f3:
                    input_disc = st.text_input("Gênero / Disciplina:", value=st.session_state.sel_disc_reg, key="input_disc_ui")
                with col_f4:
                    input_total = st.number_input("Total de Novos Exemplares a Gerar:", min_value=1, value=st.session_state.sel_total_reg, key="input_total_ui")
                
                st.markdown("---")
                st.markdown("##### ⚙️ Ações e Gerenciamento do Livro")
                
                col_b1, col_b2, col_b3 = st.columns(3)
                btn_salvar_livro = col_b1.button("💾 Salvar Livro")
                btn_alterar_livro = col_b2.button("🔄 Alterar Livro")
                btn_excluir_livro = col_b3.button("🗑️ Excluir Livro")

                if btn_salvar_livro:
                    if not input_tombo or not input_titulo:
                        st.error("⚠️ Informe pelo menos o Código de Tombo / ISBN e o Título da Obra.")
                    else:
                        try:
                            doc_b = conectar_planilha()
                            aba_b = doc_b.worksheet("biblioteca_acervo_ipec")
                            dados_atuais_acervo = aba_b.get_all_records()
                            
                            tombo_base = str(input_tombo).strip()
                            qtd_novos = int(input_total)
                            
                            tombos_existentes = [str(r.get("Tombo", "")).strip() for r in dados_atuais_acervo]
                            matches_existentes = [t for t in tombos_existentes if t == tombo_base or t.startswith(tombo_base + "-")]
                            
                            if not matches_existentes:
                                linhas_lote = []
                                for i in range(1, qtd_novos + 1):
                                    t_novo = f"{tombo_base}-{i:03d}" if qtd_novos > 1 or "-" in tombo_base else tombo_base
                                    linhas_lote.append([t_novo, str(input_titulo).strip(), str(input_autor).strip(), str(input_cat).strip(), str(input_disc).strip(), 1, 1, "ATIVO"])
                                aba_b.append_rows(linhas_lote)
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Cadastrou novo acervo Tombo base: {tombo_base}")
                                
                                st.session_state.sel_tombo_reg = ""
                                st.session_state.sel_titulo_reg = ""
                                st.session_state.sel_autor_reg = ""
                                st.session_state.sel_cat_reg = "Didático"
                                st.session_state.sel_disc_reg = ""
                                st.session_state.sel_total_reg = 1

                                st.success("🎉 Livro(s) cadastrado(s) com sucesso na nuvem!")
                                st.rerun()
                            else:
                                maior_sufixo = 0
                                for t_ex in matches_existentes:
                                    parts = t_ex.rsplit("-", 1)
                                    if len(parts) == 2 and parts[1].isdigit():
                                        num_suf = int(parts[1])
                                        if num_suf > maior_sufixo:
                                            maior_sufixo = num_suf
                                
                                if maior_sufixo == 0:
                                    maior_sufixo = 1
                                
                                linhas_lote = []
                                for j in range(1, qtd_novos + 1):
                                    proximo_num = maior_sufixo + j
                                    t_novo_seq = f"{tombo_base}-{proximo_num:03d}"
                                    linhas_lote.append([t_novo_seq, str(input_titulo).strip(), str(input_autor).strip(), str(input_cat).strip(), str(input_disc).strip(), 1, 1, "ATIVO"])
                                
                                aba_b.append_rows(linhas_lote)
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Gerou novos exemplares sequenciais para o Tombo base: {tombo_base}")
                                
                                st.session_state.sel_tombo_reg = ""
                                st.session_state.sel_titulo_reg = ""
                                st.session_state.sel_autor_reg = ""
                                st.session_state.sel_cat_reg = "Didático"
                                st.session_state.sel_disc_reg = ""
                                st.session_state.sel_total_reg = 1

                                st.success(f"🎉 {qtd_novos} novo(s) exemplar(es) gerado(s) sequencialmente a partir do código existente!")
                                st.rerun()

                        except Exception as err_l:
                            st.error(f"Erro ao salvar: {err_l}")

                if btn_alterar_livro:
                    if not input_tombo:
                        st.error("⚠️ Informe o Código de Tombo exato do livro que deseja alterar.")
                    else:
                        try:
                            doc_b = conectar_planilha()
                            aba_b = doc_b.worksheet("biblioteca_acervo_ipec")
                            registros = aba_b.get_all_records()
                            
                            idx_encontrado = -1
                            for i, r in enumerate(registros):
                                if str(r.get("Tombo", "")).strip() == str(input_tombo).strip():
                                    idx_encontrado = i + 2
                                    break
                            
                            if idx_encontrado != -1:
                                linha_alt = [
                                    str(input_tombo).strip(),
                                    str(input_titulo).strip(),
                                    str(input_autor).strip(),
                                    str(input_cat).strip(),
                                    str(input_disc).strip(),
                                    1,
                                    1,
                                    "ATIVO"
                                ]
                                aba_b.update(range_name=f"A{idx_encontrado}:H{idx_encontrado}", values=[linha_alt])
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Alterou livro Tombo: {input_tombo}")
                                
                                st.session_state.sel_tombo_reg = ""
                                st.session_state.sel_titulo_reg = ""
                                st.session_state.sel_autor_reg = ""
                                st.session_state.sel_cat_reg = "Didático"
                                st.session_state.sel_disc_reg = ""
                                st.session_state.sel_total_reg = 1

                                st.success("🎉 Livro alterado com sucesso na nuvem!")
                                st.rerun()
                            else:
                                st.error("⚠️ Código de Tombo não localizado no acervo para alteração.")
                        except Exception as err_alt:
                            st.error(f"Erro ao alterar livro: {err_alt}")

                if btn_excluir_livro:
                    if not input_tombo:
                        st.error("⚠️ Informe o Código de Tombo exato que deseja excluir.")
                    else:
                        st.session_state.tombo_para_excluir_seguro = str(input_tombo).strip()
                        st.session_state.acionou_exclusao_form = True

                if st.session_state.get("acionou_exclusao_form", False):
                    tombo_alvo_exc = st.session_state.tombo_para_excluir_seguro
                    st.warning(f"⚠️ ATENÇÃO: A exclusão do Título é uma função irreversível e definitiva no sistema (Tombo: {tombo_alvo_exc})!")
                    confirma_excluir_form = st.radio("Deseja realmente prosseguir com a exclusão deste livro?", ["Não", "Sim"], index=0, key="radio_conf_exc_form_seguro_v6")
                    
                    if confirma_excluir_form == "Sim":
                        if st.button("🔴 Confirmar Exclusão Definitiva"):
                            emprestado_ativo = False
                            if not df_emprestimos_geral.empty:
                                match_emp = df_emprestimos_geral[(df_emprestimos_geral["Tombo"].astype(str).str.strip() == str(tombo_alvo_exc)) & (df_emprestimos_geral["Status"].astype(str).str.strip().isin(["Ativo", "Atrasado"]))]
                                if not match_emp.empty:
                                    emprestado_ativo = True
                            
                            if emprestado_ativo:
                                st.error("❌ ERRO: Este livro está atualmente emprestado! A exclusão não pode ocorrer antes de efetuar a devolução.")
                            else:
                                try:
                                    doc_ex = conectar_planilha()
                                    aba_ex = doc_ex.worksheet("biblioteca_acervo_ipec")
                                    regs_ex = aba_ex.get_all_records()
                                    
                                    idx_l = -1
                                    for idx_r, r_ex in enumerate(regs_ex):
                                        if str(r_ex.get("Tombo", "")).strip() == str(tombo_alvo_exc).strip():
                                            idx_l = idx_r + 2
                                            break
                                    
                                    if idx_l != -1:
                                        aba_ex.update(range_name=f"H{idx_l}:H{idx_l}", values=[["INATIVO / EXCLUÍDO"]])
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Excluiu/Inativou Tombo: {tombo_alvo_exc}")
                                        
                                        st.session_state.sel_tombo_reg = ""
                                        st.session_state.sel_titulo_reg = ""
                                        st.session_state.sel_autor_reg = ""
                                        st.session_state.sel_cat_reg = "Didático"
                                        st.session_state.sel_disc_reg = ""
                                        st.session_state.sel_total_reg = 1
                                        st.session_state.acionou_exclusao_form = False
                                        st.session_state.tombo_para_excluir_seguro = ""

                                        st.success("🎉 Livro excluído/inativado com sucesso com preservação de índice na nuvem!")
                                        st.rerun()
                                    else:
                                        st.error(f"⚠️ Tombo '{tombo_alvo_exc}' não localizado na planilha.")
                                except Exception as err_exc_aba:
                                    st.error(f"Erro ao excluir: {err_exc_aba}")

            elif sub_biblioteca == "Empréstimos e Devoluções":
                st.markdown(f"#### 🔄 Controle de Empréstimos e Devoluções — Ano: {ano_letivo_escolhido}")
                st.info("Módulo de empréstimos integrado e pronto.")

            elif sub_biblioteca in ["Relatórios Gerais", "Recibos", "Relatório do Acervo", "Relatório de Empréstimo", "Gráficos"]:
                st.markdown(f"### 📊 Módulo de Relatórios e Gráficos — Biblioteca ({sub_biblioteca})")
                st.info(f"Painel corporativo de '{sub_biblioteca}' estruturado para o ano de {ano_letivo_escolhido}.")

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
                    st.error("Aba de logs vazia.")
