# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa seguranca_ipec.py. Versão do Código: v.1.0.003
# Data de atualização: 27/07/2026 - 17:52
# Descrição das Alterações:
#   - Módulo reutilizável de segurança, alteração de senha com fontes de alto contraste e blindagem de perfis.
# ==============================================================================

import streamlit as st
from modules.utils import conectar_planilha, registrar_log_auditoria

def renderizar_painel_seguranca_sidebar():
    """Renderiza na barra lateral a opção de alteração/recuperação de senha."""
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔑 Alterar / Esqueci Minha Senha"):
        st.markdown("<small>Preencha os dados abaixo para redefinir sua senha de acesso ao sistema.</small>", unsafe_allow_html=True)
        
        email_rec = st.text_input("Seu E-mail de Usuário:", key="rec_email_v4")
        senha_atual = st.text_input("Senha Atual (ou provisória):", type="password", key="rec_senha_atual_v4")
        nova_senha = st.text_input("Nova Senha:", type="password", key="rec_nova_senha_v4")
        confirma_nova_senha = st.text_input("Confirme a Nova Senha:", type="password", key="rec_confirma_senha_v4")
        
        if st.button("🔄 Atualizar Senha", key="btn_exec_rec_senha_v4"):
            if not email_rec or not senha_atual or not nova_senha or not confirma_nova_senha:
                st.sidebar.markdown(
                    "<div style='background-color: #fdf2f2; border: 1px solid #f8b4b4; padding: 10px; border-radius: 5px; color: #991b1b; font-weight: bold; font-size: 0.9em; margin-top: 10px;'>"
                    "⚠️ Preencha todos os campos obrigatórios para prosseguir."
                    "</div>", 
                    unsafe_allow_html=True
                )
            elif nova_senha != confirma_nova_senha:
                st.sidebar.markdown(
                    "<div style='background-color: #fdf2f2; border: 1px solid #f8b4b4; padding: 10px; border-radius: 5px; color: #991b1b; font-weight: bold; font-size: 0.9em; margin-top: 10px;'>"
                    "⚠️ As novas senhas digitadas não coincidem."
                    "</div>", 
                    unsafe_allow_html=True
                )
            else:
                try:
                    doc = conectar_planilha()
                    aba_cred = doc.worksheet("credenciais_ipec")
                    registros = aba_cred.get_all_records()
                    
                    usuario_encontrado = False
                    senha_correta = False
                    linha_alvo = -1
                    perfil_usuario_alvo = ""
                    
                    for idx, r in enumerate(registros):
                        if str(r.get("Usuario", "")).strip().lower() == email_rec.strip().lower():
                            usuario_encontrado = True
                            if str(r.get("Senha", "")).strip() == senha_atual.strip():
                                senha_correta = True
                                linha_alvo = idx + 2
                                perfil_usuario_alvo = str(r.get("Perfil", "")).strip()
                            break
                    
                    if not usuario_encontrado:
                        st.sidebar.markdown(
                            "<div style='background-color: #fdf2f2; border: 1px solid #f8b4b4; padding: 10px; border-radius: 5px; color: #991b1b; font-weight: bold; font-size: 0.9em; margin-top: 10px;'>"
                            "❌ Usuário não cadastrado no sistema! Verifique o e-mail informado."
                            "</div>", 
                            unsafe_allow_html=True
                        )
                    elif not senha_correta:
                        st.sidebar.markdown(
                            "<div style='background-color: #fdf2f2; border: 1px solid #f8b4b4; padding: 10px; border-radius: 5px; color: #991b1b; font-weight: bold; font-size: 0.9em; margin-top: 10px;'>"
                            "❌ Senha atual incorreta para este usuário."
                            "</div>", 
                            unsafe_allow_html=True
                        )
                    else:
                        aba_cred.update_cell(linha_alvo, 2, str(nova_senha).strip())
                        registrar_log_auditoria(email_rec, perfil_usuario_alvo, "Alterou/Redefiniu sua senha de acesso com sucesso.")
                        st.sidebar.markdown(
                            "<div style='background-color: #065f46; border: 1px solid #34d399; padding: 10px; border-radius: 5px; color: #ffffff; font-weight: bold; font-size: 0.9em; margin-top: 10px;'>"
                            "🎉 Senha alterada com sucesso! Faça login com a nova senha."
                            "</div>", 
                            unsafe_allow_html=True
                        )
                        st.balloons()
                except Exception as err_rec:
                    st.sidebar.error(f"Erro de conexão ao processar alteração: {err_rec}")

def verificar_permissao_escrita(email_usuario, perfil_usuario, acao_descricao="esta alteração"):
    """Verifica se o usuário possui permissão plena de escrita/alteração."""
    if perfil_usuario and perfil_usuario.strip().lower() in ["total", "admin"]:
        return True
    
    st.warning(f"🔒 **Aviso de Segurança SISTEMAS iPeC:** Seu perfil atual possui modo de **Consulta Geral**. Ação restrita ({acao_descricao}) não permitida para este nível. Apenas usuários com perfil de Categoria Especial/Total possuem autonomia para alterar registros ou configurações do sistema. A senha do Administrador Principal é protegida.")
    return False
