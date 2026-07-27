# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa app.py. Versão do Código: v.1.5.076
# Data de atualização: 27/07/2026 - 15:15
# Descrição das Alterações:
#   - Inclusão do Painel de Cadastro e Gestão de Usuários na aba de Suporte para administradores (Método 2 integrado).
# ==============================================================================

import streamlit as st
import pandas as pd
import re
import unicodedata
from datetime import datetime, timedelta
import time
import os
import base64
from pypdf import PdfReader

from modules.utils import obter_horario_unai, calcular_idade_extenso, conectar_planilha, registrar_log_auditoria, COLUNAS_OFICIAIS
from modules.banco import (
    carregar_banco_dados_virtual, 
    carregar_dados_miguilim, 
    carregar_acervo_biblioteca, 
    carregar_emprestimos_biblioteca, 
    carregar_config_biblioteca,
    carregar_dados_pbf
)
from modules.autenticacao import gerenciar_autenticacao
from modules.ui_elementos import aplicar_estilos_css, renderizar_cabecalho_principal
from modules.seguranca_ipec import renderizar_painel_seguranca_sidebar, verificar_permissao_escrita

st.set_page_config(
    page_title="Sistemas de Gestão Escolar - iPeC", 
    page_icon="imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png",
    layout="wide"
)

aplicar_estilos_css()

def remover_acentos(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    nfkd = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

def inferir_genero_por_nome(nome_completo):
    if not isinstance(nome_completo, str) or not nome_completo.strip():
        return "Masculino"
    primeiro_nome = remover_acentos(nome_completo.strip().split()[0])
    terminacoes_femininas = ('a', 'ice', 'is', 'iz', 'ade', 'ute')
    nomes_femininos_excecoes = {'beatriz', 'tairine', 'thais', 'kamilly', 'emilly', 'ketelyn', 'kellyn', 'evellyn'}
    nomes_masculinos_excecoes = {'lucas', 'nicolas', 'dias', 'jonas', 'elias', 'tomas'}
    
    if primeiro_nome in nomes_masculinos_excecoes:
        return "Masculino"
    if primeiro_nome in nomes_femininos_excecoes or primeiro_nome.endswith(terminacoes_femininas):
        return "Feminino"
    return "Masculino"

if "dados_banco" not in st.session_state:
    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "perfil_usuario" not in st.session_state:
    st.session_state["perfil_usuario"] = None
if "email_usuario" not in st.session_state:
    st.session_state["email_usuario"] = ""
if "foto_usuario" not in st.session_state:
    st.session_state["foto_usuario"] = ""

try:
    st.sidebar.image("imagens/Logo_inovador_iPeC_com_circuito-removebg-preview.png", use_container_width=True)
except Exception: pass

st.sidebar.markdown("""
    <div class="sidebar-logo-footer">
        Versão: v.1.5.076 de 27/07/2026<br>
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
            st.sidebar.markdown(
                "<div style='background-color: #991b1b; border: 1px solid #f8b4b4; padding: 10px; border-radius: 5px; color: #ffffff; font-weight: bold; font-size: 0.9em; margin-top: 10px; text-align: center;'>"
                "⚠️ Credenciais incorretas."
                "</div>", 
                unsafe_allow_html=True
            )
    
    renderizar_painel_seguranca_sidebar()
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
    
    renderizar_painel_seguranca_sidebar()
    
    if st.sidebar.button("🚪 Sair do Sistema"):
        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Efetuou logout do sistema.")
        st.session_state["autenticado"] = False
        st.session_state["perfil_usuario"] = None
        st.rerun()

    renderizar_cabecalho_principal()
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
            opcoes_menu = [
                "📊 Painel de Controle de Conformidade e Indicadores de Alunos",
                "📥 Importação de Dados",
                "📈 Relatórios", 
                "👁️ Programa Miguilim", 
                "📚 Programa Biblioteca", 
                "💰 Programa Bolsa Família",
                "🛠️ Suporte"
            ]
                
        menu_principal = st.sidebar.selectbox("Selecione a Área:", opcoes_menu)

        if menu_principal == "📊 Painel de Controle de Conformidade e Indicadores de Alunos":
            st.markdown(f"### 📊 Painel de Controle - Ano Letivo: {ano_letivo_escolhido}")
            sub_conformidade = st.sidebar.radio("Sub-menu:", ["Cadastro de Alunos", "Atualização de Dados"])
            
            if df_db_ano.empty and sub_conformidade == "Atualização de Dados":
                st.warning(f"⚠️ Atenção: Não existem lançamentos para o ano letivo de {ano_letivo_escolhido}.")
            else:
                if "f_aluno" not in st.session_state: st.session_state.f_aluno = ""
                if "f_mae" not in st.session_state: st.session_state.f_mae = ""
                if "f_turma" not in st.session_state: st.session_state.f_turma = ""
                if "f_turno" not in st.session_state: st.session_state.f_turno = ""
                if "f_status" not in st.session_state: st.session_state.f_status = ""
                if "f_pbf" not in st.session_state: st.session_state.f_pbf = ""

                df_filtrado = df_db_ano.copy()
                if not df_filtrado.empty:
                    if st.session_state.f_aluno:
                        termo = remover_acentos(st.session_state.f_aluno)
                        df_filtrado = df_filtrado[df_filtrado["Aluno"].apply(lambda x: termo in remover_acentos(x))]
                    if st.session_state.f_mae:
                        termo = remover_acentos(st.session_state.f_mae)
                        df_filtrado = df_filtrado[df_filtrado["Mãe"].apply(lambda x: termo in remover_acentos(x))]
                    if st.session_state.f_turma:
                        termo = remover_acentos(st.session_state.f_turma)
                        df_filtrado = df_filtrado[df_filtrado["Turma"].apply(lambda x: termo in remover_acentos(x))]
                    if st.session_state.f_turno:
                        termo = remover_acentos(st.session_state.f_turno)
                        df_filtrado = df_filtrado[df_filtrado["Turno"].apply(lambda x: termo in remover_acentos(x))]
                    if st.session_state.f_status:
                        termo = remover_acentos(st.session_state.f_status)
                        df_filtrado = df_filtrado[df_filtrado["Status"].apply(lambda x: termo in remover_acentos(x))]
                    if st.session_state.f_pbf:
                        termo = remover_acentos(st.session_state.f_pbf)
                        df_filtrado = df_filtrado[df_filtrado["PBF"].apply(lambda x: termo in remover_acentos(x))]

                if sub_conformidade == "Cadastro de Alunos":
                    st.success(f"Banco de dados ativo ({ano_letivo_escolhido}) com {len(df_db_ano)} registros oficiais na nuvem.")
                    
                    st.markdown("#### 🛠️ Filtros de Coluna Simultâneos (Busca Inteligente Sem Acentos/Case-Insensitive)")
                    filtro_cols = st.columns(2)
                    with filtro_cols[0]:
                        st.session_state.f_aluno = st.text_input("Filtrar por Aluno:", value=st.session_state.f_aluno)
                        st.session_state.f_mae = st.text_input("Filtrar por Mãe:", value=st.session_state.f_mae)
                        st.session_state.f_turma = st.text_input("Filtrar por Turma:", value=st.session_state.f_turma)
                    with filtro_cols[1]:
                        st.session_state.f_turno = st.text_input("Filtrar por Turno:", value=st.session_state.f_turno)
                        st.session_state.f_status = st.text_input("Filtrar por Status:", value=st.session_state.f_status)
                        st.session_state.f_pbf = st.text_input("Filtrar por PBF (Sim/Não):", value=st.session_state.f_pbf)

                    if df_filtrado.empty:
                        st.markdown('<div class="aviso-nao-encontrado-pulsante">⚠️ ATENÇÃO: Nenhum registro foi encontrado com os filtros informados ou o aluno não existe na base de dados!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("#### 📋 Tabela de Registros")
                        if st.session_state["perfil_usuario"] == "Total":
                            df_editavel = st.data_editor(df_filtrado, use_container_width=True, hide_index=True, key="editor_dados_tabela_v76")
                            col_bt1, col_bt2, col_bt3 = st.columns([2, 2, 3])
                            
                            with col_bt1:
                                if st.button("💾 Salvar Alterações Gerais"):
                                    if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Salvar Alterações Gerais"):
                                        try:
                                            doc_w = conectar_planilha()
                                            aba_w = doc_w.get_worksheet(0)
                                            alteracoes = 0
                                            for _, row_edit in df_editavel.iterrows():
                                                id_reg = row_edit["Id."]
                                                original_match = df_db_ano[df_db_ano["Id."] == id_reg]
                                                if not original_match.empty:
                                                    row_orig = original_match.iloc[0]
                                                    if any(str(row_edit.get(c, "")) != str(row_orig.get(c, "")) for c in COLUNAS_OFICIAIS if c != "Idade"):
                                                        linha_planilha = int(id_reg) + 1
                                                        row_edit["Idade"] = calcular_idade_extenso(row_edit["Nascimento"])
                                                        valores_alinhados = [str(row_edit.get(c, "")) for c in COLUNAS_OFICIAIS]
                                                        aba_w.update(range_name=f"A{linha_planilha}:Z{linha_planilha}", values=[valores_alinhados])
                                                        alteracoes += 1
                                                        time.sleep(0.3)
                                            if alteracoes > 0:
                                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Atualizou {alteracoes} registros em {ano_letivo_escolhido}.")
                                                st.success(f"🎉 {alteracoes} registro(s) atualizado(s) com sucesso na nuvem!")
                                                st.cache_data.clear()
                                                st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                                st.rerun()
                                            else:
                                                st.info("ℹ️ Nenhuma alteração detectada.")
                                        except Exception as e: st.error(f"Erro: {e}")

                            with col_bt2:
                                if st.button("➕ Incluir Aluno"):
                                    if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Incluir Aluno"):
                                        try:
                                            doc_inc = conectar_planilha()
                                            aba_inc = doc_inc.get_worksheet(0)
                                            nova_linha = [""] * len(COLUNAS_OFICIAIS)
                                            nova_linha[1] = str(ano_letivo_escolhido)
                                            nova_linha[2] = "NOVO ALUNO"
                                            nova_linha[9] = "Não informado"
                                            nova_linha[21] = "Turma A"
                                            nova_linha[24] = "Matriculado"
                                            aba_inc.append_row(nova_linha)
                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Incluiu novo aluno em {ano_letivo_escolhido}.")
                                            st.success("🎉 Novo aluno incluído com sucesso na base!")
                                            st.cache_data.clear()
                                            st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                            st.rerun()
                                        except Exception as err_inc:
                                            st.error(f"Erro ao incluir aluno: {err_inc}")

                            with col_bt3:
                                lista_excluir_op = ["Selecione..."] + [f"{int(r['Id.'])} - {r['Aluno']} (Mãe: {r['Mãe']})" for _, r in df_db_ano.iterrows()]
                                aluno_para_excluir = st.selectbox("Selecionar para Exclusão:", lista_excluir_op, key="sel_exc_painel_v76")
                                if aluno_para_excluir != "Selecione...":
                                    id_exc = int(aluno_para_excluir.split(" - ")[0])
                                    if st.button("🗑️ Excluir Aluno Selecionado"):
                                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Excluir Aluno"):
                                            try:
                                                doc_ex = conectar_planilha()
                                                aba_ex = doc_ex.get_worksheet(0)
                                                linha_planilha_exc = int(id_exc) + 1
                                                valores_vazios = [""] * len(COLUNAS_OFICIAIS)
                                                aba_ex.update(range_name=f"A{linha_planilha_exc}:Z{linha_planilha_exc}", values=[valores_vazios])
                                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Excluiu aluno ID {id_exc} em {ano_letivo_escolhido}.")
                                                st.success("🗑️ Aluno excluído com sucesso da nuvem!")
                                                st.cache_data.clear()
                                                st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                                st.rerun()
                                            except Exception as err_excl:
                                                st.error(f"Erro ao excluir aluno: {err_excl}")
                        else:
                            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                            st.info("ℹ️ Você está navegando em **Modo de Consulta**.")

                elif sub_conformidade == "Atualização de Dados":
                    st.markdown(f"#### 🔍 Consulta de Alunos ({ano_letivo_escolhido})")
                    st.dataframe(df_db_ano, use_container_width=True, hide_index=True)

        elif menu_principal == "📥 Importação de Dados":
            st.markdown(f"### 📥 Módulo de Importação de Dados — Ano: {ano_letivo_escolhido}")
            if st.session_state["perfil_usuario"] != "Total":
                st.warning("⚠️ Módulo restrito a administradores.")
            else:
                st.info("Área de importação liberada.")

        elif menu_principal == "📈 Relatórios":
            st.markdown(f"### 📈 Relatórios Gerais e Estatísticas — Ano: {ano_letivo_escolhido}")
            st.info("Módulo de relatórios gerais disponível.")

        elif menu_principal == "👁️ Programa Miguilim":
            st.markdown(f"### 👁️ Programa Miguilim - Saúde Visual e Auditiva ({ano_letivo_escolhido})")
            st.dataframe(df_db_ano[["Id.", "Aluno", "Turma", "PBF"]], use_container_width=True, hide_index=True)

        elif menu_principal == "📚 Programa Biblioteca":
            st.markdown(f"### 📚 Programa Biblioteca - Gestão Literária ({ano_letivo_escolhido})")
            df_acervo_geral = carregar_acervo_biblioteca()
            if not df_acervo_geral.empty:
                st.dataframe(df_acervo_geral, use_container_width=True, hide_index=True)
            else:
                st.info("Acervo vazio.")

        elif menu_principal == "💰 Programa Bolsa Família":
            st.markdown(f"### 💰 Programa Bolsa Família (PBF) — Ano Letivo: {ano_letivo_escolhido}")
            sub_pbf = st.sidebar.radio("Sub-menu:", ["Visualizar Dados", "Imprimir / Relatório"], key="sub_pbf_v76")
            if sub_pbf == "Imprimir / Relatório":
                st.markdown("##### 🖨️ Impressão e Relatório Oficial do Bolsa Família")
                periodos_pbf = ["Fev/Mar", "Abr/Maio", "Jun/Jul", "Ags/Set", "Out/Nov"]
                periodo_imp_ref = st.selectbox("Selecione o Período:", periodos_pbf, key="sel_pbf_ref_v76")
                df_pbf_rel = carregar_dados_pbf(ano_letivo_escolhido, periodo_imp_ref)
                if not df_pbf_rel.empty:
                    st.dataframe(df_pbf_rel, use_container_width=True, hide_index=True)
                    st.info("Relatório pronto para impressão.")
                else:
                    st.warning("Nenhum dado PBF para este período.")

        elif menu_principal == "🛠️ Suporte":
            st.markdown(f"### 🛠️ Painel de Suporte e Gestão de Usuários ({ano_letivo_escolhido})")
            
            if st.session_state["perfil_usuario"] == "Total":
                sub_suporte_adm = st.sidebar.radio("Sub-menu Sup:", ["Cadastrar Novo Usuário", "Logs de Auditoria"], key="sub_sup_adm_v76")
                
                if sub_suporte_adm == "Cadastrar Novo Usuário":
                    st.markdown("#### 👤 Painel Administrativo: Cadastro de Novo Usuário")
                    st.markdown("<small>Preencha os dados abaixo para cadastrar um novo usuário operador ou administrador no sistema.</small>", unsafe_allow_html=True)
                    
                    with st.form("form_cad_novo_usuario_v76"):
                        novo_email_cad = st.text_input("E-mail do Novo Usuário (Login):", placeholder="operador@ipec.com")
                        nova_senha_cad = st.text_input("Senha Inicial Provisória:", type="password")
                        novo_perfil_cad = st.selectbox("Perfil de Acesso:", ["Consulta", "Total"])
                        nova_foto_cad = st.text_input("URL da Foto (Opcional):", placeholder="https://exemplo.com/foto.jpg")
                        
                        btn_salvar_novo_user = st.form_submit_button("💾 Cadastrar Novo Usuário na Nuvem")
                        
                        if btn_salvar_novo_user:
                            if not novo_email_cad or not nova_senha_cad:
                                st.error("⚠️ Informe o e-mail e a senha inicial do novo usuário.")
                            else:
                                try:
                                    doc_u = conectar_planilha()
                                    try:
                                        aba_c = doc_u.worksheet("credenciais_ipec")
                                    except Exception:
                                        aba_c = doc_u.add_worksheet(title="credenciais_ipec", rows="100", cols="4")
                                        aba_c.append_row(["Usuario", "Senha", "Perfil", "Foto"])
                                    
                                    registros_atuais_cred = aba_c.get_all_records()
                                    ja_existe = False
                                    for rc in registros_atuais_cred:
                                        if str(rc.get("Usuario", "")).strip().lower() == novo_email_cad.strip().lower():
                                            ja_existe = True
                                            break
                                    
                                    if ja_existe:
                                        st.error(f"❌ O e-mail '{novo_email_cad}' já está cadastrado no sistema!")
                                    else:
                                        aba_c.append_row([
                                            str(novo_email_cad).strip(),
                                            str(nova_senha_cad).strip(),
                                            str(novo_perfil_cad).strip(),
                                            str(nova_foto_cad).strip()
                                        ])
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Cadastrou novo usuário: {novo_email_cad} ({novo_perfil_cad})")
                                        st.success(f"🎉 Novo usuário '{novo_email_cad}' cadastrado com sucesso na nuvem!")
                                        st.balloons()
                                except Exception as err_cad_user:
                                    st.error(f"Erro ao cadastrar usuário: {err_cad_user}")
                else:
                    try:
                        doc_s = conectar_planilha()
                        aba_log_s = doc_s.worksheet("log_auditoria_ipec")
                        df_logs = pd.DataFrame(aba_log_s.get_all_records())
                        st.dataframe(df_logs, use_container_width=True)
                    except Exception: st.error("Aba de logs vazia.")
            else:
                st.warning("⚠️ O painel de suporte administrativo é restrito ao Administrador Principal.")
