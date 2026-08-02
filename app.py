# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa app.py. Versão do Código: v.1.5.096
# Data de atualização: 02/08/2026 - 08:31
# Descrição das Alterações:
#   - Supressão total de cabeçalhos e URLs automáticas injetadas pelo navegador no motor de impressão Blob (v.1.5.096).
#   - Padronização rigorosa do rodapé corporativo nas impressões (Ficha Individual e PBF).
#   - Blindagem integral de todos os demais módulos.
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
    if primeiro_nome in terminacoes_femininas or primeiro_nome.endswith(terminacoes_femininas):
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
        Versão: v.1.5.096 de 02/08/2026<br>
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
            opcoes_menu = ["📊 Painel de Controle de Conformidade e Indicadores de Alunos"]
            if st.session_state["perfil_usuario"] == "Total":
                opcoes_menu.append("📥 Importação de Dados")
            opcoes_menu.extend(["👁️ Programa Miguilim", "📚 Programa Biblioteca", "💰 Programa Bolsa Família"])
            if st.session_state["perfil_usuario"] == "Total":
                opcoes_menu.append("🛠️ Suporte")
                
        menu_principal = st.sidebar.selectbox("Selecione a Área:", opcoes_menu)

        if menu_principal == "📊 Painel de Controle de Conformidade e Indicadores de Alunos":
            st.markdown(f"### 📊 Painel de Controle - Ano Letivo: {ano_letivo_escolhido}")
            sub_conformidade = st.sidebar.radio("Sub-menu:", ["Cadastro de Alunos", "Atualização de Dados", "Relatórios"])
            
            if df_db_ano.empty and sub_conformidade in ["Atualização de Dados", "Relatórios"]:
                st.warning(f"⚠️ Atenção: Não existem lançamentos para o ano letivo de {ano_letivo_escolhido}.")
            else:
                if sub_conformidade == "Relatórios":
                    st.markdown(f"#### 📄 Relatórios Individuais de Alunos — Ano: {ano_letivo_escolhido}")
                    sub_sub_rel_painel = st.radio("Selecione o Relatório:", ["Ficha Individual"], horizontal=True, key="sub_sub_rel_painel_v96")
                    
                    if sub_sub_rel_painel == "Ficha Individual":
                        lista_alunos_ficha = ["Selecione o Aluno..."]
                        for _, r_al in df_db_ano.iterrows():
                            val_id_s = str(r_al.get('Id.', '')).strip()
                            if val_id_s.isdigit():
                                lista_alunos_ficha.append(f"{int(val_id_s)} - {r_al.get('Aluno', '')} (Mãe: {r_al.get('Mãe', '')})")
                        
                        aluno_ficha_sel = st.selectbox("Selecione o Aluno para Emissão da Ficha Individual:", lista_alunos_ficha, key="sel_aluno_ficha_ind_v96")
                        
                        if aluno_ficha_sel and aluno_ficha_sel != "Selecione o Aluno...":
                            id_alvo_ficha = int(aluno_ficha_sel.split(" - ")[0])
                            reg_ficha = df_db_ano[df_db_ano["Id."].astype(str).str.strip() == str(id_alvo_ficha)].iloc[0]
                            
                            st.markdown("##### 📋 Prévia dos Dados Pessoais do Aluno")
                            col_pf1, col_pf2 = st.columns(2)
                            with col_pf1:
                                st.markdown(f"**Nome:** {reg_ficha.get('Aluno', '')}")
                                st.markdown(f"**Nascimento:** {reg_ficha.get('Nascimento', '')} (Idade: {reg_ficha.get('Idade', '')})")
                                st.markdown(f"**Mãe:** {reg_ficha.get('Mãe', '')}")
                                st.markdown(f"**Pai:** {reg_ficha.get('Pai', '')}")
                                st.markdown(f"**Sexo:** {reg_ficha.get('Sexo', '')}")
                                st.markdown(f"**CPF:** {reg_ficha.get('CPF', '')}")
                                st.markdown(f"**RG / Certidão:** {reg_ficha.get('CERTIDÃO', '')}")
                            with col_pf2:
                                st.markdown(f"**Turma:** {reg_ficha.get('Turma', '')}")
                                st.markdown(f"**Turno:** {reg_ficha.get('Turno', '')}")
                                st.markdown(f"**Período de Ensino:** {reg_ficha.get('Período de Ensino', '')}")
                                st.markdown(f"**Endereço:** {reg_ficha.get('Endereço', '')}, {reg_ficha.get('Bairro', '')}")
                                st.markdown(f"**Telefone:** {reg_ficha.get('Telefone', '')}")
                                st.markdown(f"**Bolsa Família (PBF):** {reg_ficha.get('PBF', '')}")
                                st.markdown(f"**Status:** {reg_ficha.get('Status', '')}")

                            operador_atual = st.session_state.get('email_usuario', 'Sistema').split('@')[0]
                            
                            logo_base64_str = ""
                            try:
                                caminho_logo = "imagens/Logo da Escola.jpeg"
                                if os.path.exists(caminho_logo):
                                    with open(caminho_logo, "rb") as img_file:
                                        logo_base64_str = base64.b64encode(img_file.read()).decode("utf-8")
                            except Exception:
                                logo_base64_str = ""

                            tag_img_logo = f'<img src="data:image/jpeg;base64,{logo_base64_str}" class="logo-escola"/>' if logo_base64_str else ''

                            html_ficha_conteudo = (
                                "<table style='width: 100%; border-collapse: collapse; margin-top: 10px; font-family: \"Times New Roman\", Times, serif; font-size: 12pt;'>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; width: 30%; background-color: #f2f2f2; font-weight: bold;'>Nome do Aluno</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Aluno', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Data de Nascimento</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Nascimento', '')} (Idade: {reg_ficha.get('Idade', '')})</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Filiação (Mãe)</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Mãe', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Filiação (Pai)</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Pai', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Sexo</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Sexo', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>CPF</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('CPF', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Certidão / Documento</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('CERTIDÃO', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Turma / Período</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Turma', '')} - {reg_ficha.get('Período de Ensino', '')} ({reg_ficha.get('Turno', '')})</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Endereço e Bairro</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Endereço', '')}, {reg_ficha.get('Bairro', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Telefone de Contato</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Telefone', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Programa Bolsa Família (PBF)</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('PBF', '')}</td></tr>"
                                f"<tr><td style='border: 1px solid #999; padding: 8px; background-color: #f2f2f2; font-weight: bold;'>Situação / Status</td><td style='border: 1px solid #999; padding: 8px;'>{reg_ficha.get('Status', '')}</td></tr>"
                                "</table>"
                            )

                            html_botao_impressao_ficha = (
                                "<div>"
                                "<script>"
                                "function abrirFichaBlob() {"
                                "var htmlConteudo = '<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Ficha de Identificação do Aluno</title>' +"
                                "'<style>' +"
                                "'@page { size: A4; margin: 15mm; margin-bottom: 25mm; }' +"
                                "'body { font-family: \"Times New Roman\", Times, serif; font-size: 12pt; line-height: 1.5; color: #000; margin: 0; padding: 0; -webkit-print-color-adjust: exact; }' +"
                                "'.header-container { display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }' +"
                                "'.logo-escola { width: 70px; height: auto; margin-right: 20px; }' +"
                                "'.titulo-escola { flex-grow: 1; text-align: center; }' +"
                                "'.titulo-escola h2 { margin: 0; font-size: 14pt; font-family: \"Times New Roman\", Times, serif; text-transform: uppercase; font-weight: bold; }' +"
                                "'.subtitulo-escola { text-align: center; font-size: 12pt; font-family: \"Times New Roman\", Times, serif; font-weight: bold; margin-bottom: 20px; color: #000; }' +"
                                "'.footer-container { position: fixed; bottom: -15mm; left: 0; width: 100%; display: flex; justify-content: space-between; align-items: center; font-size: 11pt; font-family: \"Times New Roman\", Times, serif; border-top: 1px solid #ccc; padding-top: 8px; color: #000; background: white; }' +"
                                "'@media print { @page { margin-top: 10mm; margin-bottom: 20mm; } body { margin: 0; } .footer-container { position: fixed; bottom: 0; } }' +"
                                "'%p::after { content: counter(page); }' +"
                                "'%pages::after { content: counter(pages); }' +"
                                "'%</style></head><body>' +"
                                "'<div class=\"header-container\">' +"
                                + repr(tag_img_logo) + " +"
                                "'<div class=\"titulo-escola\">' +"
                                "'<h2>ESCOLA MUNICIPAL PROFª GLÓRIA MOREIRA</h2>' +"
                                "'</div></div>' +"
                                "'<div class=\"subtitulo-escola\">FICHA DE IDENTIFICAÇÃO DO ALUNO</div>' +"
                                + repr(html_ficha_conteudo) + " +"
                                "'<div class=\"footer-container\">' +"
                                "'<div style=\"width: 33%; text-align: left;\">© Sistemas iPeC - v.1.5.096</div>' +"
                                "'<div style=\"width: 34%; text-align: center;\">Operador: " + operador_atual + "</div>' +"
                                "'<div style=\"width: 33%; text-align: right;\">p.1/1</div>' +"
                                "'</div></body></html>';"
                                "var blob = new Blob([htmlConteudo], { type: 'text/html;charset=utf-8' });"
                                "var url = URL.createObjectURL(blob);"
                                "var win = window.open(url, '_blank');"
                                "if (win) {"
                                "win.focus();"
                                "setTimeout(function() { win.print(); }, 800);"
                                "} else {"
                                "alert('Por favor, permita pop-ups para este site para imprimir o relatório.');"
                                "}"
                                "}"
                                "</script>"
                                "<button onclick=\"abrirFichaBlob()\" style=\"background-color: #0e4166; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px;\">"
                                "🖨️ Imprimir Ficha Individual"
                                "</button>"
                                "</div>"
                            )
                            st.components.v1.html(html_botao_impressao_ficha, height=70)

                elif sub_conformidade == "Cadastro de Alunos":
                    total_reg_alunos = len(df_db_ano)
                    tot_m = 0
                    tot_f = 0
                    for _, r_sex in df_db_ano.iterrows():
                        val_sexo = str(r_sex.get("Sexo", "")).strip().upper()
                        if val_sexo.startswith("M"):
                            tot_m += 1
                        elif val_sexo.startswith("F"):
                            tot_f += 1
                        else:
                            inf_g = inferir_genero_por_nome(str(r_sex.get("Aluno", "")))
                            if inf_g == "Masculino":
                                tot_m += 1
                            else:
                                tot_f += 1
                    
                    pct_m = (tot_m / total_reg_alunos * 100) if total_reg_alunos > 0 else 0
                    pct_f = (tot_f / total_reg_alunos * 100) if total_reg_alunos > 0 else 0

                    st.success(f"Banco de dados ativo ({ano_letivo_escolhido}) com {total_reg_alunos} registros oficiais na nuvem. | 👦 Masculino: {tot_m} - {pct_m:.1f}% | 👧 Feminino: {tot_f} - {pct_f:.1f}%")
                    
                    st.markdown("#### 🔍 Busca Rápida e Inteligente de Alunos")
                    
                    def atualizar_filtro_aluno():
                        st.session_state.f_aluno = st.session_state.input_f_aluno_v96
                    def atualizar_filtro_mae():
                        st.session_state.f_mae = st.session_state.input_f_mae_v96
                    def atualizar_filtro_turma():
                        st.session_state.f_turma = st.session_state.input_f_turma_v96
                    def atualizar_filtro_turno():
                        st.session_state.f_turno = st.session_state.input_f_turno_v96
                    def atualizar_filtro_status():
                        st.session_state.f_status = st.session_state.input_f_status_v96
                    def atualizar_filtro_pbf():
                        st.session_state.f_pbf = st.session_state.input_f_pbf_v96

                    filtro_cols = st.columns(2)
                    with filtro_cols[0]:
                        st.text_input("Filtrar por Aluno:", value=st.session_state.f_aluno, key="input_f_aluno_v96", on_change=atualizar_filtro_aluno)
                        st.text_input("Filtrar por Mãe:", value=st.session_state.f_mae, key="input_f_mae_v96", on_change=atualizar_filtro_mae)
                        st.text_input("Filtrar por Turma:", value=st.session_state.f_turma, key="input_f_turma_v96", on_change=atualizar_filtro_turma)
                    with filtro_cols[1]:
                        st.text_input("Filtrar por Turno:", value=st.session_state.f_turno, key="input_f_turno_v96", on_change=atualizar_filtro_turno)
                        st.text_input("Filtrar por Status:", value=st.session_state.f_status, key="input_f_status_v96", on_change=atualizar_filtro_status)
                        st.text_input("Filtrar por PBF (Sim/Não):", value=st.session_state.f_pbf, key="input_f_pbf_v96", on_change=atualizar_filtro_pbf)

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

                    if df_filtrado.empty:
                        st.markdown('<div class="aviso-nao-encontrado-pulsante">⚠️ ATENÇÃO: Nenhum registro foi encontrado com os filtros informados ou o aluno não existe na base de dados!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("#### 📋 Tabela de Registros (Edição Direta em Tempo Real)")
                        
                        def colorir_transferidos(row):
                            transf_val = str(row.get("Transferência", "")).strip()
                            if transf_val and transf_val not in ["Não informado", "", "nan", "None", "nat"]:
                                return ['color: red; font-weight: bold;'] * len(row)
                            return [''] * len(row)

                        df_estilizado = df_filtrado.style.apply(colorir_transferidos, axis=1)
                        st.dataframe(df_estilizado, use_container_width=True, hide_index=True, key="editor_dados_tabela_v96")

                        if st.session_state["perfil_usuario"] == "Total":
                            col_bt1, col_bt2, col_bt3 = st.columns([2, 2, 3])
                            
                            with col_bt1:
                                if st.button("💾 Salvar Alterações Gerais"):
                                    if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Salvar Alterações Gerais"):
                                        try:
                                            doc_w = conectar_planilha()
                                            aba_w = doc_w.get_worksheet(0)
                                            alteracoes = 0
                                            for _, row_edit in df_filtrado.iterrows():
                                                id_reg = row_edit["Id."]
                                                original_match = df_db_ano[df_db_ano["Id."] == id_reg]
                                                if not original_match.empty:
                                                    row_orig = original_match.iloc[0]
                                                    if any(str(row_edit.get(c, "")) != str(row_orig.get(c, "")) for c in COLUNAS_OFICIAIS if c != "Idade"):
                                                        linha_planilha = int(str(id_reg).strip()) + 1 if str(id_reg).strip().isdigit() else 2
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
                                            
                                            dados_totais_planilha = aba_inc.get_all_records()
                                            maior_id = 0
                                            for r_tot in dados_totais_planilha:
                                                val_id_str = str(r_tot.get("Id.", "")).strip()
                                                if val_id_str.isdigit():
                                                    num_id = int(val_id_str)
                                                    if num_id > maior_id:
                                                        maior_id = num_id
                                            proximo_id_gerado = maior_id + 1

                                            nova_linha = [""] * len(COLUNAS_OFICIAIS)
                                            nova_linha[0] = str(proximo_id_gerado)
                                            nova_linha[1] = str(ano_letivo_escolhido)
                                            nova_linha[2] = "NOVO ALUNO"
                                            nova_linha[9] = "Não informado"
                                            nova_linha[21] = "Turma A"
                                            nova_linha[24] = "Matriculado"
                                            aba_inc.append_row(nova_linha)
                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Incluiu novo aluno ID {proximo_id_gerado} em {ano_letivo_escolhido}.")
                                            st.success("🎉 Novo aluno incluído com sucesso na base!")
                                            st.cache_data.clear()
                                            st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                            st.rerun()
                                        except Exception as err_inc:
                                            st.error(f"Erro ao incluir aluno: {err_inc}")

                            with col_bt3:
                                lista_excluir_op = ["Selecione..."]
                                for _, r in df_db_ano.iterrows():
                                    val_id_s = str(r.get('Id.', '')).strip()
                                    if val_id_s.isdigit():
                                        id_fmt = int(val_id_s)
                                        lista_excluir_op.append(f"{id_fmt} - {r.get('Aluno', '')} (Mãe: {r.get('Mãe', '')})")

                                aluno_para_excluir = st.selectbox("Selecionar para Exclusão:", lista_excluir_op, key="sel_exc_painel_v96")
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

                elif sub_conformidade == "Atualização de Dados":
                    st.markdown(f"#### 🔍 Atualização e Edição Individual de Alunos ({ano_letivo_escolhido})")
                    
                    if df_db_ano.empty:
                        st.warning("⚠️ Nenhum aluno cadastrado para este ano letivo.")
                    else:
                        lista_alunos_cadastrados = ["Selecione o Aluno..."]
                        for _, r in df_db_ano.iterrows():
                            val_id_s = str(r.get('Id.', '')).strip()
                            if val_id_s.isdigit():
                                lista_alunos_cadastrados.append(f"{int(val_id_s)} - {r.get('Aluno', '')} (Mãe: {r.get('Mãe', '')})")

                        aluno_selecionado_busca = st.selectbox("Selecione o aluno para alteração individual:", lista_alunos_cadastrados, key="sel_aluno_atualizacao_individual_v96")
                        
                        if aluno_selecionado_busca and aluno_selecionado_busca != "Selecione o Aluno...":
                            try:
                                id_alvo_ind = int(aluno_selecionado_busca.split(" - ")[0])
                                df_aluno_ind = df_db_ano[df_db_ano["Id."].astype(str).str.strip() == str(id_alvo_ind)].copy()
                                
                                if not df_aluno_ind.empty:
                                    reg_atual = df_aluno_ind.iloc[0]
                                    st.markdown(f"##### ✍️ Ficha Cadastral e Edição: {reg_atual.get('Aluno', '')}")
                                    
                                    with st.form(f"form_atualizacao_individual_v96_{id_alvo_ind}"):
                                        col_up1, col_up2, col_up3 = st.columns(3)
                                        with col_up1:
                                            novo_nome = st.text_input("Nome do Aluno:", value=str(reg_atual.get("Aluno", "")))
                                            novo_nasc = st.text_input("Nascimento (DD/MM/AAAA):", value=str(reg_atual.get("Nascimento", "")))
                                            pbf_val = str(reg_atual.get("PBF", "")).strip()
                                            novo_pbf = st.selectbox("PBF:", ["Sim", "Não"], index=0 if pbf_val=="Sim" else 1)
                                            novo_aeecid = st.text_input("AEE/CID:", value=str(reg_atual.get("AEE/CID", "")))
                                            novo_nat = st.text_input("Naturalidade:", value=str(reg_atual.get("Naturalidade", "")))
                                            novo_nacionalidade = st.text_input("Nacionalidade:", value=str(reg_atual.get("Nacionalidade", "")))
                                        with col_up2:
                                            nova_mae = st.text_input("Mãe:", value=str(reg_atual.get("Mãe", "")))
                                            novo_pai = st.text_input("Pai:", value=str(reg_atual.get("Pai", "")))
                                            sexo_val = str(reg_atual.get("Sexo", "")).strip()
                                            sexo_idx = 0 if sexo_val=="Masculino" else (1 if sexo_val=="Feminino" else 2)
                                            novo_sexo = st.selectbox("Sexo:", ["Masculino", "Feminino", "Outro"], index=sexo_idx)
                                            novo_tel = st.text_input("Telefone:", value=str(reg_atual.get("Telefone", "")))
                                            novo_email = st.text_input("E-mail(s):", value=str(reg_atual.get("E-mail(s)", "")))
                                            novo_end = st.text_input("Endereço:", value=str(reg_atual.get("Endereço", "")))
                                        with col_up3:
                                            novo_bairro = st.text_input("Bairro:", value=str(reg_atual.get("Bairro", "")))
                                            novo_cartcid = st.text_input("Cartão Cidadão:", value=str(reg_atual.get("Cartão Cidadão", "")))
                                            novo_sus = st.text_input("Cartão do SUS:", value=str(reg_atual.get("Cartão do SUS", "")))
                                            nova_cert = st.text_input("CERTIDÃO:", value=str(reg_atual.get("CERTIDÃO", "")))
                                            novo_cpf = st.text_input("CPF:", value=str(reg_atual.get("CPF", "")))
                                            novo_periodo = st.text_input("Período de Ensino:", value=str(reg_atual.get("Período de Ensino", "")))

                                        col_up4, col_up5, col_up6, col_up7 = st.columns(4)
                                        with col_up4: nova_turma = st.text_input("Turma:", value=str(reg_atual.get("Turma", "")))
                                        with col_up5: novo_turno = st.text_input("Turno:", value=str(reg_atual.get("Turno", "")))
                                        with col_up6: novo_pae = st.text_input("Professor Apoio (PAE):", value=str(reg_atual.get("Professor de Apoio Escolar - PAE", "")))
                                        with col_up7: 
                                            status_val = str(reg_atual.get("Status", "")).strip()
                                            status_idx = 0 if status_val=="Matriculado" else (1 if status_val=="Transferido" else 2)
                                            novo_status = st.selectbox("Status:", ["Matriculado", "Transferido", "Desistente"], index=status_idx)
                                        
                                        nova_transf = st.text_input("Transferência:", value=str(reg_atual.get("Transferência", "")))
                                        
                                        st.markdown("---")
                                        btn_salvar_ind_form = st.form_submit_button("💾 Salvar Alterações do Aluno")
                                        
                                        if btn_salvar_ind_form:
                                            if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Alterar Aluno Individual"):
                                                try:
                                                    doc_ind = conectar_planilha()
                                                    aba_ind = doc_ind.get_worksheet(0)
                                                    linha_planilha_ind = int(id_alvo_ind) + 1
                                                    
                                                    idade_calculada = calcular_idade_extenso(novo_nasc)
                                                    
                                                    valores_atualizados = [
                                                        str(id_alvo_ind),
                                                        str(ano_letivo_escolhido),
                                                        str(novo_nome).strip(),
                                                        str(novo_nasc).strip(),
                                                        str(idade_calculada),
                                                        str(novo_pbf).strip(),
                                                        str(novo_aeecid).strip(),
                                                        str(novo_nat).strip(),
                                                        str(novo_nacionalidade).strip(),
                                                        str(nova_mae).strip(),
                                                        str(novo_pai).strip(),
                                                        str(novo_sexo).strip(),
                                                        str(novo_tel).strip(),
                                                        str(novo_email).strip(),
                                                        str(novo_end).strip(),
                                                        str(novo_bairro).strip(),
                                                        str(novo_cartcid).strip(),
                                                        str(novo_sus).strip(),
                                                        str(nova_cert).strip(),
                                                        str(novo_cpf).strip(),
                                                        str(novo_periodo).strip(),
                                                        str(nova_turma).strip(),
                                                        str(novo_turno).strip(),
                                                        str(novo_pae).strip(),
                                                        str(novo_status).strip(),
                                                        str(nova_transf).strip()
                                                    ]
                                                    
                                                    aba_ind.update(range_name=f"A{linha_planilha_ind}:Z{linha_planilha_ind}", values=[valores_atualizados])
                                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Atualizou individualmente o aluno ID {id_alvo_ind} em {ano_letivo_escolhido}.")
                                                    st.success("🎉 Aluno atualizado individualmente com sucesso na nuvem!")
                                                    st.cache_data.clear()
                                                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                                    st.rerun()
                                                except Exception as err_ind_form:
                                                    st.error(f"Erro ao salvar alteração individual: {err_ind_form}")
                                else:
                                    st.warning("⚠️ Registro do aluno não localizado no DataFrame filtrado.")
                            except Exception as err_sel:
                                st.error(f"Erro ao carregar dados do aluno: {err_sel}")

        elif menu_principal == "📥 Importação de Dados":
            if st.session_state["perfil_usuario"] != "Total":
                st.warning("⚠️ Acesso restrito! O Módulo de Importação de Dados é exclusivo para usuários com perfil Total.")
            else:
                st.markdown(f"### 📥 Módulo de Importação Inteligente de Dados — Ano: {ano_letivo_escolhido}")
                sub_lote = st.sidebar.radio("Sub-menu:", ["Importar Arquivo .TXT", "Visualizar Histórico de Envio"])
                
                if sub_lote == "Importar Arquivo .TXT":
                    st.info("Selecione ou arraste os arquivos de lote oficiais (.TXT) para atualizar a base de alunos. O sistema identificará automaticamente novas matrículas, alterações de turma e transferências com total segurança.")
                    arquivos_escolhidos = st.file_uploader("Escolha os arquivos de lote (.TXT)", accept_multiple_files=True, key="upl_lote_txt_v96")
                    
                    if arquivos_escolhidos:
                        st.markdown("---")
                        confirma_importacao = st.radio("Confirma importação em Lote?", ["Escolha...", "Não", "Sim"], index=0, key="radio_confirma_imp_lote_v96")
                        
                        if confirma_importacao == "Escolha...":
                            st.info("ℹ️ Selecione 'Sim' para confirmar o processamento ou 'Não' para limpar a tela.")
                        elif confirma_importacao == "Não":
                            st.warning("⚠️ Operação de importação cancelada e tela limpa.")
                        else:
                            try:
                                doc_imp = conectar_planilha()
                                aba_alunos_imp = doc_imp.get_worksheet(0)
                                registros_nuvem_raw = aba_alunos_imp.get_all_values()
                                
                                data_atual_str = obter_horario_unai().strftime("%d/%m/%Y")
                                
                                dados_importados_lista = []
                                turmas_envolvidas_lote = set()
                                
                                for arq in arquivos_escolhidos:
                                    conteudo_bytes = arq.read()
                                    try:
                                        texto_arq = conteudo_bytes.decode("utf-8")
                                    except:
                                        try:
                                            texto_arq = conteudo_bytes.decode("latin-1")
                                        except:
                                            texto_arq = str(conteudo_bytes)
                                    
                                    for linha in texto_arq.split("\n"):
                                        if linha.strip():
                                            partes = linha.split(";") if ";" in linha else [linha]
                                            nome_l = partes[0].strip().upper()
                                            mae_l = partes[1].strip().upper() if len(partes) > 1 else ""
                                            turma_l = partes[2].strip() if len(partes) > 2 else "Turma A"
                                            periodo_l = partes[3].strip() if len(partes) > 3 else "Ensino Fundamental"
                                            if len(nome_l) > 3:
                                                dados_importados_lista.append({
                                                    "Aluno": nome_l,
                                                    "Mãe": mae_l,
                                                    "Turma": turma_l,
                                                    "Período de Ensino": periodo_l
                                                })
                                                turmas_envolvidas_lote.add(turma_l)

                                df_lote_novo = pd.DataFrame(dados_importados_lista)
                                
                                inseridos_count = 0
                                atualizados_turma_count = 0
                                transferidos_count = 0
                                
                                if not df_lote_novo.empty and len(registros_nuvem_raw) > 1:
                                    cabecalho = registros_nuvem_raw[0]
                                    linhas_dados_nuvem = registros_nuvem_raw[1:]
                                    
                                    idx_aluno = cabecalho.index("Aluno") if "Aluno" in cabecalho else 2
                                    idx_ano = cabecalho.index("Ano Letivo") if "Ano Letivo" in cabecalho else 1
                                    idx_mae = cabecalho.index("Mãe") if "Mãe" in cabecalho else 9
                                    idx_turma = cabecalho.index("Turma") if "Turma" in cabecalho else 21
                                    idx_periodo = cabecalho.index("Período de Ensino") if "Período de Ensino" in cabecalho else 20
                                    idx_transf = cabecalho.index("Transferência") if "Transferência" in cabecalho else 25
                                    
                                    lote_atualizacoes_sheet = []
                                    
                                    for idx_l, reg_linha in enumerate(linhas_dados_nuvem):
                                        if len(reg_linha) > max(idx_aluno, idx_ano):
                                            ano_reg = str(reg_linha[idx_ano]).strip()
                                            if ano_reg == str(ano_letivo_escolhido):
                                                turma_nuvem = str(reg_linha[idx_turma]).strip() if len(reg_linha) > idx_turma else ""
                                                
                                                if turma_nuvem in turmas_envolvidas_lote:
                                                    nome_nuvem = str(reg_linha[idx_aluno]).strip().upper()
                                                    
                                                    match_lote = df_lote_novo[(df_lote_novo["Aluno"].str.upper() == nome_nuvem) & (df_lote_novo["Turma"] == turma_nuvem)]
                                                    if not match_lote.empty:
                                                        reg_lote_match = match_lote.iloc[0]
                                                        nova_turma_arq = str(reg_lote_match.get("Turma", ""))
                                                        novo_periodo_arq = str(reg_lote_match.get("Período de Ensino", ""))
                                                        
                                                        turma_atual_nuvem = str(reg_linha[idx_turma]) if len(reg_linha) > idx_turma else ""
                                                        periodo_atual_nuvem = str(reg_linha[idx_periodo]) if len(reg_linha) > idx_periodo else ""
                                                        
                                                        if nova_turma_arq and nova_turma_arq != turma_atual_nuvem or (novo_periodo_arq and novo_periodo_arq != periodo_atual_nuvem):
                                                            if len(reg_linha) <= idx_turma: reg_linha.extend([""] * (idx_turma - len(reg_linha) + 1))
                                                            if len(reg_linha) <= idx_periodo: reg_linha.extend([""] * (idx_periodo - len(reg_linha) + 1))
                                                            reg_linha[idx_turma] = nova_turma_arq
                                                            reg_linha[idx_periodo] = novo_periodo_arq
                                                            
                                                            num_linha_planilha = idx_l + 2
                                                            lote_atualizacoes_sheet.append({
                                                                'range': f"A{num_linha_planilha}:Z{num_linha_planilha}",
                                                                'values': [reg_linha]
                                                            })
                                                            atualizados_turma_count += 1
                                                    else:
                                                        transf_atual = str(reg_linha[idx_transf]) if len(reg_linha) > idx_transf else ""
                                                        if not transf_atual or transf_atual in ["Não informado", "", "nan", "None"]:
                                                            if len(reg_linha) <= idx_transf: reg_linha.extend([""] * (idx_transf - len(reg_linha) + 1))
                                                            reg_linha[idx_transf] = data_atual_str
                                                            
                                                            num_linha_planilha = idx_l + 2
                                                            lote_atualizacoes_sheet.append({
                                                                'range': f"A{num_linha_planilha}:Z{num_linha_planilha}",
                                                                'values': [reg_linha]
                                                            })
                                                            transferidos_count += 1

                                    if lote_atualizacoes_sheet:
                                        aba_alunos_imp.batch_update(lote_atualizacoes_sheet)

                                try:
                                    aba_hist = doc_imp.worksheet("historico_importacao_ipec")
                                except Exception:
                                    aba_hist = doc_imp.add_worksheet(title="historico_importacao_ipec", rows="1000", cols="6")
                                    aba_hist.append_row(["Data_Hora", "AnoLetivo", "Operador", "Inseridos", "AtualizadosTurma", "Transferidos"])
                                
                                data_hora_log = obter_horario_unai().strftime("%d/%m/%Y, %H:%M")
                                aba_hist.append_row([data_hora_log, str(ano_letivo_escolhido), str(st.session_state["email_usuario"]), inseridos_count, atualizados_turma_count, transferidos_count])
                                
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Executou importação inteligente restrita por turma para {ano_letivo_escolhido}.")
                                st.success(f"🎉 Importação inteligente executada com sucesso! Atualizados: {atualizados_turma_count} | Transferidos marcados na turma: {transferidos_count}. Verifique o Histórico abaixo.")
                                st.cache_data.clear()
                                st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                st.rerun()
                            except Exception as err_imp_lote:
                                st.error(f"Erro ao processar importação inteligente: {err_imp_lote}")
                else:
                    st.markdown("#### 📜 Histórico de Lotes Importados")
                    try:
                        doc_h = conectar_planilha()
                        aba_h = doc_h.worksheet("historico_importacao_ipec")
                        dados_hist_raw = aba_h.get_all_values()
                        
                        linhas_validas = []
                        mapeamento_linhas_originais = []
                        
                        if len(dados_hist_raw) > 1:
                            cab_h = dados_hist_raw[0]
                            for idx_orig, r_val in enumerate(dados_hist_raw[1:], start=2):
                                if any(str(c).strip() for c in r_val):
                                    linhas_validas.append(r_val)
                                    mapeamento_linhas_originais.append(idx_orig)
                            
                            if linhas_validas:
                                df_hist = pd.DataFrame(linhas_validas, columns=cab_h)
                                st.dataframe(df_hist, use_container_width=True, hide_index=True)
                                
                                st.markdown("---")
                                st.markdown("##### 🗑️ Exclusão de Registro do Histórico")
                                lista_op_hist = ["Selecione o registro para apagar..."]
                                for idx_h_reg, r_hist in enumerate(linhas_validas):
                                    linha_real_plan = mapeamento_linhas_originais[idx_h_reg]
                                    lista_op_hist.append(f"Linha {linha_real_plan} - Data: {r_hist[0]} | Ano: {r_hist[1]} | Op: {r_hist[2]}")
                                    
                                item_hist_sel = st.selectbox("Selecione a linha do histórico:", lista_op_hist, key="sel_hist_apagar_v96")
                                
                                if item_hist_sel != "Selecione o registro para apagar...":
                                    linha_plan_hist = int(item_hist_sel.split(" - ")[0].replace("Linha ", "").strip())
                                    st.warning("⚠️ ATENÇÃO: Os dados desta linha serão apagados e não poderão ser recuperados!")
                                    
                                    confirma_exc_hist = st.radio("Deseja realmente apagar esta linha do histórico?", ["Não", "Sim"], index=0, key="radio_conf_exc_hist_v96")
                                    if confirma_exc_hist == "Sim":
                                        if st.button("➖ Confirmar Exclusão da Linha do Histórico"):
                                            if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Excluir Histórico Importação"):
                                                try:
                                                    aba_h.delete_rows(linha_plan_hist)
                                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Excluiu fisicamente a linha {linha_plan_hist} do histórico de importação.")
                                                    st.success("🗑️ Linha do histórico apagada e removida com sucesso!")
                                                    st.rerun()
                                                except Exception as err_exc_h:
                                                    st.error(f"Erro ao apagar histórico: {err_exc_h}")
                            else:
                                st.info("ℹ️ Nenhum histórico de envio registrado até o momento.")
                        else:
                            st.info("ℹ️ Nenhum histórico de envio registrado até o momento.")
                    except Exception:
                        st.info("ℹ️ Aba de histórico de importação vazia ou não inicializada.")

        elif menu_principal == "👁️ Programa Miguilim":
            st.markdown(f"### 👁️ Programa Miguilim - Saúde Visual ({ano_letivo_escolhido})")
            
            sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Relatórios"])
            
            if sub_miguilim == "Triagem de Acuidade":
                st.markdown(f"#### 📋 Triagem de Acuidade Visual em Lote - {ano_letivo_escolhido}")
                
                if df_db_ano.empty:
                    st.warning(f"⚠️ Não existem alunos cadastrados para o ano letivo de {ano_letivo_escolhido}.")
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
                    
                    turmas_disponiveis = ["Selecione a Turma...", "Todas as turmas"] + sorted(list(df_db_ano["Turma_Formatada"].dropna().unique()))
                    turma_selecionada = st.selectbox("🎯 Filtrar por Turma / Período de Ensino:", turmas_disponiveis)
                    
                    if turma_selecionada != "Selecione a Turma...":
                        if turma_selecionada == "Todas as turmas":
                            df_miguilim_filtrado = df_db_ano.copy()
                        else:
                            df_miguilim_filtrado = df_db_ano[df_db_ano["Turma_Formatada"] == turma_selecionada]
                        
                        if df_miguilim_filtrado.empty:
                            st.info("ℹ️ Nenhum aluno localizado.")
                        else:
                            total_reg_mig = len(df_miguilim_filtrado)
                            tot_m_mig = 0
                            tot_f_mig = 0
                            for _, r_sex_mig in df_miguilim_filtrado.iterrows():
                                val_sexo_mig = str(r_sex_mig.get("Sexo", "")).strip().upper()
                                if val_sexo_mig.startswith("M"):
                                    tot_m_mig += 1
                                elif val_sexo_mig.startswith("F"):
                                    tot_f_mig += 1
                                else:
                                    inf_g_mig = inferir_genero_por_nome(str(r_sex_mig.get("Aluno", "")))
                                    if inf_g_mig == "Masculino":
                                        tot_m_mig += 1
                                    else:
                                        tot_f_mig += 1
                            
                            pct_m_mig = (tot_m_mig / total_reg_mig * 100) if total_reg_mig > 0 else 0
                            pct_f_mig = (tot_f_mig / total_reg_mig * 100) if total_reg_mig > 0 else 0

                            st.success(f"Módulo Miguilim ativo com {total_reg_mig} alunos carregados para o ano de {ano_letivo_escolhido}. | 👦 Masculino: {tot_m_mig} - {pct_m_mig:.1f}% | 👧 Feminino: {tot_f_mig} - {pct_f_mig:.1f}%")
                            
                            df_salvos_nuvem = carregar_dados_miguilim(ano_letivo_escolhido)

                            dados_tabela_mig = []
                            for _, r in df_miguilim_filtrado.iterrows():
                                aluno_nome = str(r["Aluno"]).strip()
                                
                                sa_bool = False
                                am_bool = False
                                enc_bool = False
                                ne_bool = False
                                uso_cel = "Não"
                                obs_txt = ""
                                sem_dir = ""
                                sem_esq = ""
                                com_dir = ""
                                com_esq = ""
                                estrab = "Não"

                                if not df_salvos_nuvem.empty:
                                    match_aluno = df_salvos_nuvem[df_salvos_nuvem["Aluno"].astype(str).str.strip() == aluno_nome]
                                    if not match_aluno.empty:
                                        reg_aluno = match_aluno.iloc[0]
                                        sa_bool = str(reg_aluno.get("Sem Alteração", "")).strip() == "Sem Alteração"
                                        am_bool = str(reg_aluno.get("Alteração Moderada", "")).strip() == "Alteração Moderada"
                                        enc_bool = str(reg_aluno.get("Encaminhado", "")).strip() == "Encaminhado"
                                        ne_bool = str(reg_aluno.get("Não Examinado", "")).strip() == "Não Examinado"
                                        uso_cel = str(reg_aluno.get("Uso do celular", "Não"))
                                        obs_txt = str(reg_aluno.get("Observação", ""))
                                        sem_dir = str(reg_aluno.get("Sem óculos(Dir)", ""))
                                        sem_esq = str(reg_aluno.get("Sem óculos(Esq)", ""))
                                        com_dir = str(reg_aluno.get("Com óculos(Dir)", ""))
                                        com_esq = str(reg_aluno.get("Com óculos(Esq)", ""))
                                        estrab = str(reg_aluno.get("Estrabismo", "Não"))

                                dados_tabela_mig.append({
                                    "Id.": r["Id."],
                                    "Aluno": r["Aluno"],
                                    "CPF": r["CPF"],
                                    "Mãe": r["Mãe"],
                                    "Sem óculos(Dir)": sem_dir,
                                    "Sem óculos(Esq)": sem_esq,
                                    "Com óculos(Dir)": com_dir,
                                    "Com óculos(Esq)": com_esq,
                                    "Estrabismo": estrab,
                                    "PBF": r.get("PBF", "Não"),
                                    "Sem Alteração": sa_bool,
                                    "Alteração Moderada": am_bool,
                                    "Encaminhado": enc_bool,
                                    "Não Examinado": ne_bool,
                                    "Uso do celular": uso_cel,
                                    "Observação": obs_txt
                                })
                            
                            df_tabela_mig_edit = pd.DataFrame(dados_tabela_mig)
                            
                            escala_visao = ["", "0", "0,1", "0,13", "0,16", "0,2", "0,25", "0,3", "0,4", "0,5", "0,6", "0,8", "1"]
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
                                "Sem Alteração": st.column_config.CheckboxColumn("Sem Alteração", default=False),
                                "Alteração Moderada": st.column_config.CheckboxColumn("Alteração Moderada", default=False),
                                "Encaminhado": st.column_config.CheckboxColumn("Encaminhado", default=False),
                                "Não Examinado": st.column_config.CheckboxColumn("Não Examinado", default=False),
                                "Uso do celular": st.column_config.SelectboxColumn("Uso celular", options=opcoes_celular, required=True),
                                "Observação": st.column_config.TextColumn("Observação", max_chars=500, default="")
                            }

                            df_miguilim_resultado = st.data_editor(
                                df_tabela_mig_edit,
                                column_config=conf_colunas,
                                use_container_width=True,
                                hide_index=True,
                                key="editor_miguilim_v96"
                            )
                            
                            if st.button("💾 Processar e Salvar Triagens em Lote"):
                                if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Salvar Triagens Miguilim"):
                                    try:
                                        erros_validacao = []
                                        for _, row_m in df_miguilim_resultado.iterrows():
                                            aluno_nome = row_m["Aluno"]
                                            sa = bool(row_m["Sem Alteração"])
                                            am = bool(row_m["Alteração Moderada"])
                                            enc = bool(row_m["Encaminhado"])
                                            ne = bool(row_m["Não Examinado"])
                                            
                                            total_marcados = sum([sa, am, enc, ne])
                                            if total_marcados > 1:
                                                erros_validacao.append(f"Aluno {aluno_nome}: Mais de uma opção clínica foi marcada. Selecione apenas uma.")

                                        if erros_validacao:
                                            for e_val in erros_validacao:
                                                st.error(e_val)
                                        else:
                                            doc_mig = conectar_planilha()
                                            try:
                                                aba_mig = doc_mig.worksheet("miguilim_ipec")
                                            except Exception:
                                                aba_mig = doc_mig.add_worksheet(title="miguilim_ipec", rows="1000", cols="18")
                                                aba_mig.append_row([
                                                    "Ano Letivo", "Turma", "Aluno", "CPF", "Mãe", 
                                                    "Sem óculos(Dir)", "Sem óculos(Esq)", "Com óculos(Dir)", "Com óculos(Esq)", 
                                                    "Estrabismo", "PBF", "Sem Alteração", "Alteração Moderada", 
                                                    "Encaminhado", "Não Examinado", "Uso do celular", "Observação", "Data_Hora"
                                                ])
                                            
                                            registros_existentes = aba_mig.get_all_records()
                                            data_hora_atual = obter_horario_unai().strftime("%d/%m/%Y, %H:%M")
                                            
                                            lote_para_adicionar = []
                                            atualizados = 0
                                            novos = 0

                                            for _, row_m in df_miguilim_resultado.iterrows():
                                                aluno_atual = str(row_m["Aluno"]).strip()
                                                ano_atual = str(ano_letivo_escolhido).strip()
                                                
                                                sa_val = "Sem Alteração" if bool(row_m["Sem Alteração"]) else ""
                                                am_val = "Alteração Moderada" if bool(row_m["Alteração Moderada"]) else ""
                                                enc_val = "Encaminhado" if bool(row_m["Encaminhado"]) else ""
                                                ne_val = "Não Examinado" if bool(row_m["Não Examinado"]) else ""

                                                linha_dados = [
                                                    ano_atual,
                                                    str(turma_selecionada),
                                                    aluno_atual,
                                                    str(row_m["CPF"]),
                                                    str(row_m["Mãe"]),
                                                    str(row_m["Sem óculos(Dir)"]),
                                                    str(row_m["Sem óculos(Esq)"]),
                                                    str(row_m["Com óculos(Dir)"]),
                                                    str(row_m["Com óculos(Esq)"]),
                                                    str(row_m["Estrabismo"]),
                                                    str(row_m["PBF"]),
                                                    sa_val,
                                                    am_val,
                                                    enc_val,
                                                    ne_val,
                                                    str(row_m["Uso do celular"]),
                                                    str(row_m["Observação"])[:500],
                                                    data_hora_atual
                                                ]

                                                encontrado_idx = -1
                                                for idx_reg, reg in enumerate(registros_existentes):
                                                    if str(reg.get("Aluno", "")).strip() == aluno_atual and str(reg.get("Ano Letivo", "")).strip() == ano_atual:
                                                        encontrado_idx = idx_reg + 2
                                                        break
                                                
                                                if encontrado_idx != -1:
                                                    aba_mig.update(range_name=f"A{encontrado_idx}:R{encontrado_idx}", values=[linha_dados])
                                                    atualizados += 1
                                                else:
                                                    lote_para_adicionar.append(linha_dados)
                                                    novos += 1

                                            if lote_para_adicionar:
                                                aba_mig.append_rows(lote_para_adicionar)

                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Salvou triagens Miguilim ({ano_letivo_escolhido})")
                                            st.success(f"🎉 Triagens processadas com sucesso! ({novos} novo(s), {atualizados} atualizado(s)).")
                                    except Exception as err_mig:
                                        st.error(f"Erro ao salvar triagens: {err_mig}")

            elif sub_miguilim == "Relatórios":
                st.markdown(f"### 📊 Relatórios do Programa Miguilim ({ano_letivo_escolhido})")
                sub_sub_mig = st.radio("Selecione a Opção de Relatório:", ["Encaminhamentos Clínicos", "Carta de Apresentação", "Formulário de Preenchimento"], horizontal=True, key="sub_sub_mig_v96")
                
                st.info(f"Painel corporativo da opção '{sub_sub_mig}' estruturado para o ano de {ano_letivo_escolhido}.")

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
                "Configuração",
                "Relatórios Gerais", 
                "Recibos", 
                "Relatório do Acervo", 
                "Relatório de Empréstimo", 
                "Gráficos"
            ], key="sub_bib_v96")
            
            if sub_biblioteca == "Catálogo do Acervo":
                st.markdown(f"#### 📖 Gestão do Acervo Bibliográfico ({ano_letivo_escolhido})")
                
                df_emprestimos_geral = carregar_emprestimos_biblioteca()
                
                st.markdown("##### 🔍 Pesquisa de Obras no Acervo")
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    termo_titulo = st.text_input("Filtrar por Título da Obra:", key="f_tit_v96")
                with col_p2:
                    termo_autor = st.text_input("Filtrar por Autor / Organizador:", key="f_aut_v96")
                with col_p3:
                    filtro_cat = st.selectbox("Filtrar por Categoria:", ["Todas", "Didático", "Literário"], key="f_cat_v96")

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
                        key="tabela_acervo_v96"
                    )
                    
                    try:
                        linhas_selecionadas = tabela_evento.get("selection", {}).get("rows", [])
                        if linhas_selecionadas:
                            idx_sel = linhas_selecionadas[0]
                            livro_sel = df_acervo_filtrado.iloc[idx_sel]
                            
                            st.session_state.lib_tombo = str(livro_sel.get("Tombo", ""))
                            st.session_state.lib_titulo = str(livro_sel.get("Titulo", ""))
                            st.session_state.lib_autor = str(livro_sel.get("Autor", ""))
                            st.session_state.lib_cat = str(livro_sel.get("Categoria", "Didático"))
                            st.session_state.lib_disc = str(livro_sel.get("Disciplina", ""))
                            st.session_state.lib_total = 1
                        else:
                            st.session_state.lib_tombo = ""
                            st.session_state.lib_titulo = ""
                            st.session_state.lib_autor = ""
                            st.session_state.lib_cat = "Didático"
                            st.session_state.lib_disc = ""
                            st.session_state.lib_total = 1
                    except Exception:
                        st.session_state.lib_tombo = ""
                        st.session_state.lib_titulo = ""
                        st.session_state.lib_autor = ""
                        st.session_state.lib_cat = "Didático"
                        st.session_state.lib_disc = ""
                        st.session_state.lib_total = 1
                else:
                    st.info("ℹ️ Nenhum livro cadastrado ou localizado com os filtros informados.")

                st.markdown("---")
                st.markdown("##### ✍️ Cadastro de Livro e Alteração (Reativo ao Clique)")
                
                with st.form("form_biblioteca_v96", clear_on_submit=False):
                    input_tombo = st.text_input("Código de Tombo / ISBN Base:", value=st.session_state.get("lib_tombo", ""))
                    input_titulo = st.text_input("Título da Obra:", value=st.session_state.get("lib_titulo", ""))
                    
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        input_autor = st.text_input("Autor / Organizador:", value=st.session_state.get("lib_autor", ""))
                    with col_f2:
                        cat_idx = 0 if str(st.session_state.get("lib_cat", "Didático")).strip().lower() == "didático" else 1
                        input_cat = st.selectbox("Categoria:", ["Didático", "Literário"], index=cat_idx)
                    
                    col_f3, col_f4 = st.columns(2)
                    with col_f3:
                        input_disc = st.text_input("Gênero / Disciplina:", value=st.session_state.get("lib_disc", ""))
                    with col_f4:
                        input_total = st.number_input("Total de Novos Exemplares a Gerar:", min_value=1, value=int(st.session_state.get("lib_total", 1)))
                    
                    st.markdown("---")
                    st.markdown("##### ⚙️ Ações e Gerenciamento do Livro")
                    
                    col_b1, col_b2, col_b3 = st.columns(3)
                    btn_salvar_livro = col_b1.form_submit_button("💾 Salvar Livro")
                    btn_alterar_livro = col_b2.form_submit_button("🔄 Alterar Livro")
                    btn_excluir_livro = col_b3.form_submit_button("🗑️ Excluir Livro")

                    if btn_salvar_livro:
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Salvar Livro"):
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
                                        st.success("🎉 Livro(s) cadastrado(s) com sucesso na nuvem!")
                                        st.rerun()
                                    else:
                                        maior_sufixo = 0
                                        for t_ex in matches_existentes:
                                            parts = t_ex.rsplit("-", 1)
                                            if len(parts) == 2 and parts[1].isdigit():
                                                num_suf = int(parts[1])
                                                if num_suf > maior_sufixo: maior_sufixo = num_suf
                                        if maior_sufixo == 0: maior_sufixo = 1
                                        
                                        linhas_lote = []
                                        for j in range(1, qtd_novos + 1):
                                            proximo_num = maior_sufixo + j
                                            t_novo_seq = f"{tombo_base}-{proximo_num:03d}"
                                            linhas_lote.append([t_novo_seq, str(input_titulo).strip(), str(input_autor).strip(), str(input_cat).strip(), str(input_disc).strip(), 1, 1, "ATIVO"])
                                        
                                        aba_b.append_rows(linhas_lote)
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Gerou novos exemplares sequenciais Tombo base: {tombo_base}")
                                        st.success(f"🎉 {qtd_novos} novo(s) exemplar(es) gerado(s) sequencialmente!")
                                        st.rerun()
                                except Exception as err_l:
                                    st.error(f"Erro ao salvar: {err_l}")

                    if btn_alterar_livro:
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Alterar Livro"):
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
                                            1, 1, "ATIVO"
                                        ]
                                        aba_b.update(range_name=f"A{idx_encontrado}:H{idx_encontrado}", values=[linha_alt])
                                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Alterou livro Tombo: {input_tombo}")
                                        st.success("🎉 Livro alterado com sucesso na nuvem!")
                                        st.rerun()
                                    else:
                                        st.error("⚠️ Código de Tombo não localizado no acervo para alteração.")
                                except Exception as err_alt:
                                    st.error(f"Erro ao alterar livro: {err_alt}")

                    if btn_excluir_livro:
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Excluir Livro"):
                            if not input_tombo:
                                st.error("⚠️ Informe o Código de Tombo exato que deseja excluir.")
                            else:
                                st.session_state.tombo_para_excluir_seguro = str(input_tombo).strip()
                                st.session_state.acionou_exclusao_form = True

                if st.session_state.get("acionou_exclusao_form", False):
                    tombo_alvo_exc = st.session_state.get("tombo_para_excluir_seguro", "")
                    st.warning(f"⚠️ ATENÇÃO: A exclusão do Título é uma função irreversível e definitiva no sistema (Tombo: {tombo_alvo_exc})!")
                    confirma_excluir_form = st.radio("Deseja realmente prosseguir com a exclusão deste livro?", ["Não", "Sim"], index=0, key="radio_conf_exc_v96")
                    
                    if confirma_excluir_form == "Sim":
                        if st.button("🔴 Confirmar Exclusão Definitiva"):
                            if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Confirmar Exclusão Definitiva"):
                                emprestado_ativo = False
                                if not df_emprestimos_geral.empty:
                                    match_emp = df_emprestimos_geral[(df_emprestimos_geral["Tombo"].astype(str).str.strip() == str(tombo_alvo_exc)) & (df_emprestimos_geral["Status"].astype(str).str.strip().isin(["Ativo", "Atrasado"]))]
                                    if not match_emp.empty: emprestado_ativo = True
                                
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
                                            st.session_state.acionou_exclusao_form = False
                                            st.session_state.tombo_para_excluir_seguro = ""
                                            st.success("🎉 Livro excluído/inativado com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error(f"⚠️ Tombo '{tombo_alvo_exc}' não localizado na planilha.")
                                    except Exception as err_exc_aba:
                                        st.error(f"Erro ao excluir: {err_exc_aba}")

            elif sub_biblioteca == "Configuração":
                st.markdown(f"#### ⚙️ Configuração de Prazos e Limites de Empréstimo — Biblioteca")
                cfg_atuais = carregar_config_biblioteca()
                dt_fixa_str = cfg_atuais.get("DataFixaDidatico", "15/12/2026")
                try: dt_fixa_obj = datetime.strptime(dt_fixa_str, "%d/%m/%Y").date()
                except: dt_fixa_obj = datetime(2026, 12, 15).date()

                with st.form("form_config_biblioteca_v96"):
                    prazo_lit_dias = st.number_input("Prazo padrão para Livros Literários (em dias):", min_value=1, value=int(cfg_atuais.get("PrazoLiterarioDias", 14)))
                    data_did_fixa = st.date_input("Data Fixa de Devolução para Livros Didáticos:", value=dt_fixa_obj, format="DD/MM/YYYY")
                    limite_lit = st.number_input("Limite Máximo de Empréstimos Simultâneos de Livros Literários por Aluno:", min_value=1, value=int(cfg_atuais.get("LimiteLiterario", 2)))
                    
                    btn_salvar_cfg = st.form_submit_button("💾 Salvar Configurações da Biblioteca")
                    if btn_salvar_cfg:
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Salvar Configurações Biblioteca"):
                            try:
                                doc_cfg = conectar_planilha()
                                aba_cfg = doc_cfg.worksheet("biblioteca_config_ipec")
                                aba_cfg.clear()
                                aba_cfg.append_row(["Chave", "Valor"])
                                aba_cfg.append_row(["PrazoLiterarioDias", int(prazo_lit_dias)])
                                aba_cfg.append_row(["DataFixaDidatico", data_did_fixa.strftime("%d/%m/%Y")])
                                aba_cfg.append_row(["LimiteLiterario", int(limite_lit)])
                                registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Atualizou configurações da biblioteca")
                                st.success("🎉 Configurações salvas com sucesso na nuvem!")
                                st.rerun()
                            except Exception as err_cfg: st.error(f"Erro ao salvar configurações: {err_cfg}")

            elif sub_biblioteca == "Empréstimos e Devoluções":
                st.markdown(f"#### 🔄 Controle de Empréstimos, Devoluções e Reservas — Ano: {ano_letivo_escolhido}")
                df_acervo_disp = carregar_acervo_biblioteca()
                df_emprestimos = carregar_emprestimos_biblioteca()
                cfg_prazos = carregar_config_biblioteca()
                hoje_dt = obter_horario_unai().date()
                
                df_livros_ativos_global = df_acervo_disp[df_acervo_disp["Status"].astype(str).str.strip() != "INATIVO / EXCLUÍDO"] if not df_acervo_disp.empty else pd.DataFrame()
                lista_livros_op_global = [f"Tombo: {r['Tombo']} - {r['Titulo']} [{r.get('Categoria','Literário')}]" for _, r in df_livros_ativos_global.iterrows()]
                lista_alunos_op_global = [f"{r['Aluno']} (Turma: {r['Turma']})" for _, r in df_db_ano.iterrows()] if not df_db_ano.empty else []

                sub_aba_emp = st.radio("Gestão de Circulação:", ["Novo Empréstimo", "Consulta de Empréstimos por Aluno", "Empréstimos Ativos / Devoluções / Atrasos", "Reservas de Livros"], horizontal=True, key="sub_aba_emp_v96")
                
                if sub_aba_emp == "Novo Empréstimo":
                    aluno_emp_sel = st.selectbox("Selecione o Leitor (Aluno):", ["Selecione..."] + lista_alunos_op_global, key="sel_leitor_v96")
                    livro_emp_sel = st.selectbox("Selecione o Item do Acervo (Livro):", ["Selecione..."] + lista_livros_op_global, key="sel_livro_v96")
                    data_emp = st.date_input("Data do Empréstimo:", value=hoje_dt, key="dt_emp_v96", format="DD/MM/YYYY")
                    
                    cat_livro_atual = "Literário"
                    dias_prazo_lit = int(cfg_prazos.get("PrazoLiterarioDias", 14))
                    data_did_fixa_str = cfg_prazos.get("DataFixaDidatico", "15/12/2026")
                    try: data_did_obj = datetime.strptime(data_did_fixa_str, "%d/%m/%Y").date()
                    except: data_did_obj = datetime(2026, 12, 15).date()

                    data_prev_calc = data_emp + timedelta(days=dias_prazo_lit)
                    if livro_emp_sel != "Selecione...":
                        if "Didático" in livro_emp_sel or "didático" in livro_emp_sel.lower():
                            cat_livro_atual = "Didático"
                            data_prev_calc = data_did_obj
                    
                    data_prev = st.date_input("Devolver até:", value=data_prev_calc, key="dt_prev_v96", format="DD/MM/YYYY")
                    obs_emp = st.text_input("Observações / Ocorrências:", key="obs_emp_v96")
                    
                    if st.button("📥 Concluir e Registrar Empréstimo", key="btn_concluir_emp_v96"):
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Registrar Empréstimo"):
                            if aluno_emp_sel == "Selecione..." or livro_emp_sel == "Selecione...":
                                st.error("⚠️ Selecione o aluno e o livro para efetuar o empréstimo.")
                            else:
                                tombo_alvo = livro_emp_sel.split(" - ")[0].replace("Tombo: ", "").strip()
                                nome_aluno_extraido = aluno_emp_sel.split(" (Turma:")[0].strip()
                                turma_aluno_extraida = aluno_emp_sel.split("Turma: ")[1].replace(")", "").strip()
                                titulo_livro_extraido = livro_emp_sel.split(" - ", 1)[1].rsplit(" [", 1)[0].strip()
                                
                                try:
                                    doc_e = conectar_planilha()
                                    aba_e = doc_e.worksheet("biblioteca_emprestimos_ipec")
                                    aba_e.append_row([
                                        str(ano_letivo_escolhido), str(tombo_alvo), str(titulo_livro_extraido),
                                        str(nome_aluno_extraido), str(turma_aluno_extraida),
                                        str(data_emp.strftime("%d/%m/%Y")), str(data_prev.strftime("%d/%m/%Y")),
                                        "Ativo", "", str(obs_emp)
                                    ])
                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Registrou empréstimo Tombo {tombo_alvo}")
                                    st.success("🎉 Empréstimo registrado com sucesso na nuvem!")
                                    st.rerun()
                                except Exception as err_emp: st.error(f"Erro: {err_emp}")

                elif sub_aba_emp == "Empréstimos Ativos / Devoluções / Atrasos":
                    st.markdown(f"### 📚 Circulação Ativa — Ano Letivo: {ano_letivo_escolhido}")
                    if not df_emprestimos.empty:
                        df_emp_ano = df_emprestimos[df_emprestimos["AnoLetivo"].astype(str).str.strip() == str(ano_letivo_escolhido)].copy()
                        if not df_emp_ano.empty:
                            st.dataframe(df_emp_ano, use_container_width=True, hide_index=True)
                            lista_emp_ativos = [f"Tombo: {r['Tombo']} - Aluno: {r['Aluno']} (Devolver em: {r['DataPrevista']})" for _, r in df_emp_ano.iterrows() if str(r['Status']).strip() in ["Ativo", "Atrasado"]]
                            if lista_emp_ativos:
                                emp_selecionado_acao = st.selectbox("Selecione o empréstimo para dar Baixa (Devolução):", ["Selecione..."] + lista_emp_ativos, key="sel_baixa_v96")
                                if st.button("✅ Confirmar Devolução (Baixa)") and emp_selecionado_acao != "Selecione...":
                                    if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Confirmar Devolução"):
                                        tombo_dev = emp_selecionado_acao.split(" - ")[0].replace("Tombo: ", "").strip()
                                        aluno_dev = emp_selecionado_acao.split("Aluno: ")[1].split(" (Devolver")[0].strip()
                                        try:
                                            doc_d = conectar_planilha()
                                            aba_d = doc_d.worksheet("biblioteca_emprestimos_ipec")
                                            regs_d = aba_d.get_all_records()
                                            for i_d, r_d in enumerate(regs_d):
                                                if str(r_d.get("Tombo", "")).strip() == tombo_dev and str(r_d.get("Aluno", "")).strip() == aluno_dev and str(r_d.get("Status", "")).strip() in ["Ativo", "Atrasado"]:
                                                    aba_d.update(range_name=f"H{i_d+2}:I{i_d+2}", values=[["Devolvido", hoje_dt.strftime("%d/%m/%Y")]])
                                                    break
                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Devolveu Tombo {tombo_dev}")
                                            st.success("🎉 Devolução registrada!")
                                            st.rerun()
                                        except Exception as e: st.error(f"Erro: {e}")

            elif sub_biblioteca in ["Relatórios Gerais", "Recibos", "Relatório do Acervo", "Relatório de Empréstimo", "Gráficos"]:
                st.markdown(f"### 📊 Módulo de Relatórios e Gráficos — Biblioteca ({sub_biblioteca})")
                st.info(f"Painel corporativo de '{sub_biblioteca}' estruturado para o ano de {ano_letivo_escolhido}.")

        elif menu_principal == "💰 Programa Bolsa Família":
            st.markdown(f"### 💰 Programa Bolsa Família (PBF) — Ano Letivo: {ano_letivo_escolhido}")
            sub_pbf = st.sidebar.radio("Sub-menu:", ["Importar Dados", "Visualizar Dados", "Relatório", "Atualização em Lote (PBF)"], key="sub_pbf_v96")
            
            periodos_pbf = ["Fev/Mar", "Abr/Maio", "Jun/Jul", "Ags/Set", "Out/Nov"]

            if sub_pbf == "Importar Dados":
                st.markdown("#### 📂 Importação de Dados Bimestrais do PBF (Formato PDF)")
                st.info("Selecione o período de referência e carregue o arquivo PDF oficial.")
                
                periodo_imp = st.selectbox("Selecione o Período de Referência:", periodos_pbf, key="sel_periodo_pbf_imp_v96")
                
                df_verif_existente = carregar_dados_pbf(ano_letivo_escolhido, periodo_imp)
                tem_dados_salvos = not df_verif_existente.empty
                
                sobrescrever_autorizado = True
                if tem_dados_salvos:
                    st.warning(f"⚠️ Atenção: Já existem {len(df_verif_existente)} registros salvos na nuvem para o período [{periodo_imp}] ({ano_letivo_escolhido}).")
                    conf_sobrescrever = st.radio("Deseja sobrescrever os dados existentes? Esta operação é irreversível!", ["Escolha...", "Não", "Sim"], index=0, key="radio_sobrescrever_pbf_v96")
                    if conf_sobrescrever == "Escolha...":
                        sobrescrever_autorizado = False
                        st.info("ℹ️ Selecione 'Sim' para sobrescrever ou 'Não' para cancelar a importação.")
                    elif conf_sobrescrever == "Não":
                        sobrescrever_autorizado = False
                        st.warning("⚠️ Operação cancelada. Nenhum dado foi alterado.")
                    else:
                        sobrescrever_autorizado = True

                if not tem_dados_salvos or sobrescrever_autorizado:
                    if not tem_dados_salvos or (tem_dados_salvos and conf_sobrescrever == "Sim"):
                        arquivo_pbf = st.file_uploader(f"Carregar arquivo PDF para o período [{periodo_imp}] ({ano_letivo_escolhido}):", type=["pdf"], key=f"upl_pbf_pdf_v96_{periodo_imp}")
                        
                        if arquivo_pbf is not None:
                            if st.button("📥 Processar e Salvar no Banco PBF", key="btn_salvar_pbf_lote_v96"):
                                if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Processar Importação PDF PBF"):
                                    try:
                                        linhas_extraidas = []
                                        reader = PdfReader(arquivo_pbf)
                                        texto_total = ""
                                        for pagina in reader.pages:
                                            t_pag = pagina.extract_text()
                                            if t_pag:
                                                texto_total += t_pag + "\n"
                                        
                                        termos_proibidos = [
                                            "ESCOLA", "RELATÓRIO", "PRESENÇA", "INEP", "MUNICIPAL", "SECRETARIA",
                                            "ANO", "PERÍODO", "DATA", "HORA", "REGISTRO", "SITUAÇÃO", "LEGENDA",
                                            "ATIVO", "FINALIZADO", "LANÇAMENTO", "MARÇO", "FEVEREIRO", "ABRIL", "MAIO",
                                            "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
                                            "DEPENDÊNCIA", "ADMINISTRATIVA", "UNAÍ", "MG", "ALUNOS", "FREQUÊNCIA",
                                            "AUXILIAR", "OPERADOR", "FUNDAMENTAL", "ENSINO", "%"
                                        ]

                                        def validar_e_adicionar_aluno(texto):
                                            t_clean = str(texto).upper().strip()
                                            t_clean = re.sub(r'^.*?/MARÇO\)\s*', '', t_clean)
                                            t_clean = re.sub(r'^.*?/MARÇO\s*', '', t_clean)
                                            t_clean = re.sub(r'^\(FEVEREIRO.*?\)\s*', '', t_clean)
                                            t_clean = re.sub(r'^\d{2}/\d{2}/\d{4}.*$', '', t_clean).strip()
                                            t_clean = re.sub(r'^\d{2}:\d{2}.*$', '', t_clean).strip()

                                            if len(t_clean) < 5:
                                                return
                                            
                                            contem_proibido = False
                                            for termo in termos_proibidos:
                                                if termo in t_clean:
                                                    contem_proibido = True
                                                    break
                                            
                                            if not contem_proibido and not any(dig in t_clean for dig in ["31292141", "2026/"]):
                                                linhas_extraidas.append({"Aluno": t_clean})

                                        linhas_brutas = texto_total.split("\n")
                                        i = 0
                                        while i < len(linhas_brutas):
                                            l_atual = linhas_brutas[i].strip()
                                            if "2026(" in l_atual or "2026 (" in l_atual:
                                                candidato_linhas = []
                                                j = i + 1
                                                while j < len(linhas_brutas) and j < i + 5:
                                                    prox = linhas_brutas[j].strip()
                                                    if len(prox) > 3 and not "%" in prox and not "ano Ensino" in prox and not "Fundamental" in prox and not "/" in prox and not ":" in prox:
                                                        candidato_linhas.append(prox)
                                                    j += 1
                                                if candidato_linhas:
                                                    nome_completo = " ".join(candidato_linhas).upper()
                                                    validar_e_adicionar_aluno(nome_completo)
                                            i += 1

                                        df_novo_pbf = pd.DataFrame(linhas_extraidas).drop_duplicates(subset=["Aluno"])

                                        if not df_novo_pbf.empty:
                                            doc_pbf = conectar_planilha()
                                            nome_aba_pbf = f"pbf_{ano_letivo_escolhido}_{periodo_imp.replace('/', '_').replace('.', '').lower()}"
                                            
                                            try:
                                                aba_pbf = doc_pbf.worksheet(nome_aba_pbf)
                                                doc_pbf.del_worksheet(aba_pbf)
                                            except Exception:
                                                pass
                                            
                                            aba_pbf = doc_pbf.add_worksheet(title=nome_aba_pbf, rows="2000", cols="5")
                                            aba_pbf.append_row(["AnoLetivo", "Periodo", "Aluno", "DataImportacao"])
                                            
                                            data_hora_imp = obter_horario_unai().strftime("%d/%m/%Y %H:%M")
                                            lote_linhas = [[str(ano_letivo_escolhido), str(periodo_imp), str(r["Aluno"]), data_hora_imp] for _, r in df_novo_pbf.iterrows()]
                                            
                                            if lote_linhas:
                                                aba_pbf.append_rows(lote_linhas)

                                            registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Importou dados PBF para {periodo_imp} ({ano_letivo_escolhido})")
                                            st.success(f"🎉 Dados do período {periodo_imp} importados com sucesso ({len(lote_linhas)} registros limpos)!")
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ O arquivo PDF enviado não retornou registros válidos após a filtragem.")
                                    except Exception as err_pbf_imp:
                                        st.error(f"Erro ao processar importação PDF: {err_pbf_imp}")

            elif sub_pbf == "Visualizar Dados":
                st.markdown("#### 👁️ Visualização de Dados Importados (Linhas e Colunas)")
                periodo_vis = st.selectbox("Selecione o Período de Referência para Visualização:", periodos_pbf, key="sel_periodo_pbf_vis_v96")
                
                df_pbf_vis = carregar_dados_pbf(ano_letivo_escolhido, periodo_vis)
                if not df_pbf_vis.empty:
                    tot_reg_vis = len(df_pbf_vis)
                    tot_masc_vis = 0
                    tot_fem_vis = 0
                    for _, r_v in df_pbf_vis.iterrows():
                        nome_al_v = str(r_v["Aluno"])
                        sexo_inferido = inferir_genero_por_nome(nome_al_v)
                        if not df_db_ano.empty and "Aluno" in df_db_ano.columns:
                            match_cad = df_db_ano[df_db_ano["Aluno"].apply(lambda x: remover_acentos(str(x)) == remover_acentos(nome_al_v))]
                            if not match_cad.empty:
                                s_cad = str(match_cad.iloc[0].get("Sexo", "")).strip().capitalize()
                                if s_cad in ["Masculino", "Feminino"]:
                                    sexo_inferido = s_cad
                        if sexo_inferido == "Feminino":
                            tot_fem_vis += 1
                        else:
                            tot_masc_vis += 1

                    pct_masc_vis = (tot_masc_vis / tot_reg_vis * 100) if tot_reg_vis > 0 else 0
                    pct_fem_vis = (tot_fem_vis / tot_reg_vis * 100) if tot_reg_vis > 0 else 0

                    msg_estatistica = f"Exibindo {tot_reg_vis} registros limpos para o período {periodo_vis} ({ano_letivo_escolhido}). | 👦 Masculino: {tot_masc_vis} ({pct_masc_vis:.1f}%) | 👧 Feminino: {tot_fem_vis} ({pct_fem_vis:.1f}%)"
                    st.success(msg_estatistica)

                    df_pbf_vis = df_pbf_vis.rename(columns={
                        "AnoLetivo": "Ano Letivo",
                        "Periodo": "Período",
                        "DataImportacao": "Data/Importação"
                    })
                    st.dataframe(df_pbf_vis, use_container_width=True, hide_index=True)
                else:
                    st.info(f"ℹ️ Nenhum dado importado para o período {periodo_vis} no ano de {ano_letivo_escolhido}.")

            elif sub_pbf == "Relatório":
                st.markdown(f"### 🖨️ Relatório Oficial do Bolsa Família")
                periodo_imp_ref = st.selectbox("Selecione o Período de Referência para Relatório:", periodos_pbf, key="sel_periodo_pbf_imp_ref_v96")
                
                tipo_rel_pbf = st.radio("Selecione o Tipo de Relatório:", ["Por Turma", "Geral"], horizontal=True, key="radio_tipo_rel_pbf_v96")
                
                st.markdown("##### 📋 Prévia dos Dados da Turma")
                
                df_pbf_rel = carregar_dados_pbf(ano_letivo_escolhido, periodo_imp_ref)
                if not df_pbf_rel.empty:
                    if not df_db_ano.empty and "Aluno" in df_db_ano.columns and "Turma" in df_db_ano.columns:
                        mapa_turmas = {}
                        mapa_periodo_ens = {}
                        mapa_sexo = {}
                        for _, r_cad in df_db_ano.iterrows():
                            nome_cad_norm = remover_acentos(str(r_cad["Aluno"]))
                            mapa_turmas[nome_cad_norm] = str(r_cad.get("Turma", "")).strip()
                            mapa_periodo_ens[nome_cad_norm] = str(r_cad.get("Período de Ensino", "")).strip()
                            
                            sexo_cad = str(r_cad.get("Sexo", "")).strip().capitalize()
                            if sexo_cad in ["Masculino", "Feminino"]:
                                mapa_sexo[nome_cad_norm] = sexo_cad
                            else:
                                mapa_sexo[nome_cad_norm] = "Masculino"
                        
                        lista_localizacao = []
                        lista_genero = []
                        for _, r_pbf in df_pbf_rel.iterrows():
                            nome_al_raw = str(r_pbf["Aluno"])
                            nome_al_norm = remover_acentos(nome_al_raw)
                            t_encontrada = mapa_turmas.get(nome_al_norm, "")
                            p_encontrado = mapa_periodo_ens.get(nome_al_norm, "")
                            s_encontrado = mapa_sexo.get(nome_al_norm, "")
                            
                            if not s_encontrado:
                                s_encontrado = inferir_genero_por_nome(nome_al_raw)
                            
                            if t_encontrada and p_encontrado:
                                lista_localizacao.append(f"{p_encontrado} - {t_encontrada}")
                            elif t_encontrada:
                                lista_localizacao.append(t_encontrada)
                            else:
                                lista_localizacao.append("Não cadastrado no ano")
                            lista_genero.append(s_encontrado)
                            
                        df_pbf_rel["Período/Turma"] = lista_localizacao
                        df_pbf_rel["Sexo"] = lista_genero
                    else:
                        df_pbf_rel["Período/Turma"] = "Não informada"
                        df_pbf_rel["Sexo"] = df_pbf_rel["Aluno"].apply(lambda x: inferir_genero_por_nome(str(x)))

                    if tipo_rel_pbf == "Por Turma":
                        turmas_disponiveis_pbf = sorted(list(df_pbf_rel["Período/Turma"].dropna().unique()))
                        turma_escolhida_filtro = st.selectbox("Selecione a Turma / Período para o Relatório:", ["Todas"] + turmas_disponiveis_pbf, key="sel_turma_pbf_filtro_v96")
                        if turma_escolhida_filtro != "Todas":
                            df_pbf_rel = df_pbf_rel[df_pbf_rel["Período/Turma"] == turma_escolhida_filtro].copy()

                    total_reg = len(df_pbf_rel)
                    tot_masc = len(df_pbf_rel[df_pbf_rel["Sexo"] == "Masculino"])
                    tot_fem = len(df_pbf_rel[df_pbf_rel["Sexo"] == "Feminino"])
                    pct_masc = (tot_masc / total_reg * 100) if total_reg > 0 else 0
                    pct_fem = (tot_fem / total_reg * 100) if total_reg > 0 else 0

                    df_pbf_rel = df_pbf_rel.rename(columns={
                        "AnoLetivo": "Ano Letivo",
                        "Periodo": "Período",
                        "DataImportacao": "Data/Importação"
                    })

                    operador_atual = st.session_state.get('email_usuario', 'Sistema').split('@')[0]
                    
                    html_tabela_impressao = df_pbf_rel[['Aluno', 'Período/Turma']].to_html(index=False, classes='table table-bordered table-striped')
                    
                    subtitulo_referencia = f"PERÍODO DE REFERÊNCIA: {periodo_imp_ref} - {ano_letivo_escolhido}"

                    logo_base64_str = ""
                    try:
                        caminho_logo = "imagens/Logo da Escola.jpeg"
                        if os.path.exists(caminho_logo):
                            with open(caminho_logo, "rb") as img_file:
                                logo_base64_str = base64.b64encode(img_file.read()).decode("utf-8")
                    except Exception:
                        logo_base64_str = ""

                    tag_img_logo = f'<img src="data:image/jpeg;base64,{logo_base64_str}" class="logo-escola"/>' if logo_base64_str else ''

                    html_botao_impressao = (
                        "<div>"
                        "<script>"
                        "function abrirJanelaImpressoraBlob() {"
                        "var htmlConteudo = '<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Relatório PBF</title>' +"
                        "'<style>' +"
                        "'@page { size: A4; margin: 15mm; margin-bottom: 25mm; }' +"
                        "'body { font-family: \"Times New Roman\", Times, serif; font-size: 12pt; line-height: 1.5; color: #000; margin: 0; padding: 0; -webkit-print-color-adjust: exact; }' +"
                        "'.header-container { display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; }' +"
                        "'.logo-escola { width: 70px; height: auto; margin-right: 20px; }' +"
                        "'.titulo-escola { flex-grow: 1; text-align: center; }' +"
                        "'.titulo-escola h2 { margin: 0; font-size: 14pt; font-family: \"Times New Roman\", Times, serif; text-transform: uppercase; font-weight: bold; }' +"
                        "'.subtitulo-escola { text-align: center; font-size: 12pt; font-family: \"Times New Roman\", Times, serif; font-weight: bold; margin-bottom: 5px; color: #000; }' +"
                        "'.subperiodo-escola { text-align: center; font-size: 11pt; font-family: \"Times New Roman\", Times, serif; font-weight: bold; margin-bottom: 20px; color: #000; }' +"
                        "'table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 40px; font-family: \"Times New Roman\", Times, serif; font-size: 12pt; }' +"
                        "'th, td { border: 1px solid #999; padding: 8px 10px; text-align: left; }' +"
                        "'th { background-color: #d3d3d3; color: #000; text-transform: uppercase; font-weight: bold; }' +"
                        "'tr:nth-child(even) { background-color: #f2f2f2; }' +"
                        "'.footer-container { position: fixed; bottom: -15mm; left: 0; width: 100%; display: flex; justify-content: space-between; align-items: center; font-size: 11pt; font-family: \"Times New Roman\", Times, serif; border-top: 1px solid #ccc; padding-top: 8px; color: #000; background: white; }' +"
                        "'@media print { @page { margin-top: 10mm; margin-bottom: 20mm; } body { margin: 0; } .footer-container { position: fixed; bottom: 0; } }' +"
                        "'%p::after { content: counter(page); }' +"
                        "'%pages::after { content: counter(pages); }' +"
                        "'%</style></head><body>' +"
                        "'<div class=\"header-container\">' +"
                        + repr(tag_img_logo) + " +"
                        "'<div class=\"titulo-escola\">' +"
                        "'<h2>ESCOLA MUNICIPAL PROFª GLÓRIA MOREIRA</h2>' +"
                        "'</div></div>' +"
                        "'<div class=\"subtitulo-escola\">RELATÓRIO DE ALUNOS INSCRITOS NO PROGRAMA DO BOLSA FAMÍLIA</div>' +"
                        "'<div class=\"subperiodo-escola\">" + subtitulo_referencia + "</div>' +"
                        + repr(html_tabela_impressao) + " +"
                        "'<div class=\"footer-container\">' +"
                        "'<div style=\"width: 33%; text-align: left;\">© Sistemas iPeC - v.1.5.096</div>' +"
                        "'<div style=\"width: 34%; text-align: center;\">Operador: " + operador_atual + "</div>' +"
                        "'<div style=\"width: 33%; text-align: right;\">p.1/1</div>' +"
                        "'</div></body></html>';"
                        "var blob = new Blob([htmlConteudo], { type: 'text/html;charset=utf-8' });"
                        "var url = URL.createObjectURL(blob);"
                        "var win = window.open(url, '_blank');"
                        "if (win) {"
                        "win.focus();"
                        "setTimeout(function() { win.print(); }, 800);"
                        "} else {"
                        "alert('Por favor, permita pop-ups para este site para imprimir o relatório.');"
                        "}"
                        "}"
                        "</script>"
                        "<button onclick=\"abrirJanelaImpressoraBlob()\" style=\"background-color: #0e4166; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px;\">"
                        "🖨️ Imprimir Relatório"
                        "</button>"
                        "</div>"
                    )
                    st.components.v1.html(html_botao_impressao, height=70)
                else:
                    st.warning(f"⚠️ Não há dados disponíveis para impressão no período {periodo_imp_ref}.")

            elif sub_pbf == "Atualização em Lote (PBF)":
                st.markdown("#### 🔄 Rotina de Atualização em Lote para o Cadastro de Alunos")
                st.info("Esta rotina cruzará a lista de beneficiários importada com o cadastro de alunos do ano letivo vigente. Os alunos presentes na lista terão o campo PBF atualizado para 'Sim', e os demais para 'Não'.")
                
                periodo_lote_pbf = st.selectbox("Selecione o Período de Referência Base:", periodos_pbf, key="sel_periodo_pbf_lote_rotina_v96")
                
                confirma_lote = st.radio("⚠️ Atenção: Os dados do cadastro desses alunos serão alterados. Deseja continuar?", ["Escolha...", "Não", "Sim"], index=0, key="radio_confirma_lote_pbf_v96")
                
                if confirma_lote == "Sim":
                    if st.button("🚀 Executar Atualização em Lote do PBF no Cadastro"):
                        if verificar_permissao_escrita(st.session_state["email_usuario"], st.session_state["perfil_usuario"], "Executar Atualização em Lote PBF"):
                            try:
                                df_pbf_fonte = carregar_dados_pbf(ano_letivo_escolhido, periodo_lote_pbf)
                                if df_pbf_fonte.empty:
                                    st.warning(f"⚠️ Nenhum dado importado encontrado para o período {periodo_lote_pbf}.")
                                else:
                                    doc_lote = conectar_planilha()
                                    aba_alunos_lote = doc_lote.get_worksheet(0)
                                    todos_alunos_plan = aba_alunos_lote.get_all_records()
                                    
                                    nomes_pbf_set = {remover_acentos(str(r.get("Aluno", ""))) for _, r in df_pbf_fonte.iterrows()}
                                    
                                    atualizados_count = 0
                                    lote_atualizacoes = []
                                    
                                    for idx_l, reg_al in enumerate(todos_alunos_plan):
                                        if str(reg_al.get("Ano Letivo", "")).strip() == str(ano_letivo_escolhido):
                                            nome_aluno_atual = remover_acentos(str(reg_al.get("Aluno", "")))
                                            novo_status_pbf = "Sim" if nome_aluno_atual in nomes_pbf_set else "Não"
                                            
                                            if str(reg_al.get("PBF", "")).strip() != novo_status_pbf:
                                                linha_plan_al = idx_l + 2
                                                reg_al["PBF"] = novo_status_pbf
                                                reg_al["Idade"] = calcular_idade_extenso(reg_al.get("Nascimento", ""))
                                                valores_linha_corrigidos = [str(reg_al.get(c, "")) for c in COLUNAS_OFICIAIS]
                                                
                                                lote_atualizacoes.append({
                                                    'range': f"A{linha_plan_al}:Z{linha_plan_al}",
                                                    'values': [valores_linha_corrigidos]
                                                })
                                                atualizados_count += 1

                                    if lote_atualizacoes:
                                        aba_alunos_lote.batch_update(lote_atualizacoes)
                                    
                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Executou atualização em lote PBF ({periodo_lote_pbf}) - {atualizados_count} alteracoes.")
                                    st.success(f"🎉 Atualização em lote concluída com sucesso! {atualizados_count} aluno(s) tiveram o status PBF atualizado na nuvem.")
                                    st.cache_data.clear()
                                    st.session_state["dados_banco"] = carregar_banco_dados_virtual()
                                    st.rerun()
                            except Exception as err_lote_pbf:
                                st.error(f"Erro na execução da atualização em lote: {err_lote_pbf}")
                elif confirma_lote == "Não":
                    st.info("ℹ️ Operação de atualização em lote cancelada pelo usuário.")

        elif menu_principal == "🛠️ Suporte":
            st.markdown(f"### 🛠️ Painel de Suporte e Gestão de Usuários ({ano_letivo_escolhido})")
            if st.session_state["perfil_usuario"] == "Total":
                sub_sup_adm = st.sidebar.radio("Sub-menu Sup:", ["Cadastrar Novo Usuário", "Logs de Auditoria em Tempo Real"], key="sub_sup_adm_v96")
                if sub_sup_adm == "Cadastrar Novo Usuário":
                    st.markdown("#### 👤 Painel Administrativo: Cadastro de Novo Usuário")
                    with st.form("form_cad_novo_usuario_v96"):
                        novo_email_cad = st.text_input("E-mail do Novo Usuário (Login):")
                        nova_senha_cad = st.text_input("Senha Inicial Provisória:", type="password")
                        novo_perfil_cad = st.selectbox("Perfil de Acesso:", ["Consulta", "Total"])
                        nova_foto_cad = st.text_input("URL da Foto (Opcional):")
                        
                        btn_salvar_novo_user = st.form_submit_button("💾 Cadastrar Novo Usuário na Nuvem")
                        if btn_salvar_novo_user:
                            if not novo_email_cad or not nova_senha_cad: st.error("Informe e-mail e senha.")
                            else:
                                try:
                                    doc_u = conectar_planilha()
                                    try: aba_c = doc_u.worksheet("credenciais_ipec")
                                    except Exception:
                                        aba_c = doc_u.add_worksheet(title="credenciais_ipec", rows="100", cols="4")
                                        aba_c.append_row(["Usuario", "Senha", "Perfil", "Foto"])
                                    aba_c.append_row([novo_email_cad.strip(), nova_senha_cad.strip(), novo_perfil_cad.strip(), nova_foto_cad.strip()])
                                    registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Cadastrou usuário: {novo_email_cad}")
                                    st.success(f"🎉 Usuário '{novo_email_cad}' cadastrado com sucesso!")
                                    st.balloons()
                                except Exception as e: st.error(f"Erro: {e}")
                else:
                    try:
                        doc_s = conectar_planilha()
                        aba_log_s = doc_s.worksheet("log_auditoria_ipec")
                        df_logs = pd.DataFrame(aba_log_s.get_all_records())
                        st.dataframe(df_logs, use_container_width=True)
                    except Exception: st.error("Aba de logs vazia.")
            else:
                st.warning("⚠️ Área restrita ao Administrador Principal.")
