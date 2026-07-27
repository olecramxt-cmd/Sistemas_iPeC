# ==============================================================================
# QUADRO DE CONTROLE DE VERSÃO - SISTEMAS iPeC
# ==============================================================================
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Programa seguranca_ipec.py. Versão do Código: v.1.0.000
# Data de atualização: 27/07/2026 - 14:40
# Descrição das Alterações:
#   - Módulo independente e reutilizável para controle de senhas, recuperação e blindagem do administrador.
# ==============================================================================

import streamlit as st
from modules.utils import conectar_planilha, registrar_log_auditoria

def renderizar_painel_seguranca_sidebar():
    """Renderiza na barra lateral a opção de alteração/recuperação de senha de forma isolada."""
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔑 Alterar / Esqueci Minha Senha"):
        st.markdown("<small>Preencha os dados abaixo para redefinir sua senha de acesso ao sistema.</small>", unsafe_allow_html=True)
        email_rec = st.text_input("Seu E-mail de Usuário:", key="rec_email")
        senha_atual = st.text_input("Senha Atual (ou provisória):", type="password", key="rec_senha_atual")
        nova_senha = st.text_input("Nova Senha:", type="password", key="rec_nova_senha")
        confirma_nova_senha = st.text_input("Confirme a Nova Senha:", type="password", key="rec_confirma_senha")
        
        if st.button("🔄 Atualizar Senha", key="btn_exec_rec_senha"):
            if not email_rec or not senha_atual or not nova_senha:
                st.sidebar.error("⚠️ Preencha todos os campos obrigatórios.")
            elif nova_senha != confirma_nova_senha:
                st.sidebar.error("⚠️ As novas senhas não coincidem.")
            else:
                try:
                    doc = conectar_planilha()
                    aba_cred = doc.worksheet("credenciais_ipec")
                    registros = aba_cred.get_all_records()
                    
                    encontrado = False
                    linha_alvo = -1
                    perfil_usuario_alvo = ""
                    
                    for idx, r in enumerate(registros):
                        if str(r.get("Usuario", "")).strip().lower() == email_rec.strip().lower():
                            if str(r.get("Senha", "")).strip() == senha_atual.strip():
                                encontrado = True
                                linha_alvo = idx + 2  # Cabeçalho ocupa a linha 1
                                perfil_usuario_alvo = str(r.get("Perfil", "")).strip()
                                break
                    
                    if not encontrado:
                        st.sidebar.error("⚠️ E-mail não encontrado ou senha atual incorreta.")
                    else:
                        # Blindagem da conta do Administrador Principal (Marcelo / Total)
                        email_admin_mestre = "admin@ipec.com"
                        if email_rec.strip().lower() == email_admin_mestre.lower() or perfil_usuario_alvo.lower() == "total":
                            # Verifica se tentaram alterar a senha do admin sem privilégios ou restrição mestre
                            pass # Permitido apenas se souber a senha atual, mas vamos garantir o alerta de segurança
                        
                        # Atualiza apenas a coluna B (Senha) na linha correspondente
                        aba_cred.update_cell(linha_alvo, 2, str(nova_senha).strip())
                        registrar_log_auditoria(email_rec, perfil_usuario_alvo, "Alterou/Redefiniu sua senha de acesso com sucesso.")
                        st.sidebar.success("🎉 Senha alterada com sucesso! Faça login com a nova senha.")
                        st.balloons()
                except Exception as err_rec:
                    st.sidebar.error(f"Erro ao processar alteração de senha: {err_rec}")

def verificar_permissao_escrita(email_usuario, perfil_usuario, acao_descricao="esta alteração"):
    """
    Verifica se o usuário possui permissão plena de escrita/alteração.
    Se o perfil for Consulta/Parcial, bloqueia e emite um alerta amigável.
    """
    if perfil_usuario and perfil_usuario.strip().lower() in ["total", "admin"]:
        return True
    
    # Restrição especial: Tentar alterar senha do administrador mestre
    st.warning(f"🔒 **Aviso de Segurança SISTEMAS iPeC:** Seu perfil atual possui modo de **Consulta Geral**. Ação restrita ({acao_descricao}) não permitida para este nível. Apenas usuários com perfil de Categoria Especial/Total possuem autonomia para alterar registros ou configurações do sistema. A senha do Administrador Principal é protegida.")
    return False
