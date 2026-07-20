# =====================================================================
# Módulo de Triagem Visual - Programa Miguilim
# SISTEMAS iPeC - Integração com Base de Dados e Automação de Resultados
# © Prof. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão: 1.0.0
# Data: 20/07/2026
# =====================================================================

# ==========================================
# 4. PROGRAMA MIGUILIM (Integrado ao Streamlit)
# ==========================================
elif menu_principal == "👁️ Programa Miguilim":
    st.markdown("### 👁️ Programa Miguilim - Saúde Visual e Auditiva")
    sub_miguilim = st.sidebar.radio("Sub-menu:", ["Triagem de Acuidade", "Encaminhamentos Clínicos"])
    
    if sub_miguilim == "Triagem de Acuidade":
        st.markdown("#### 📋 Formulário de Triagem de Acuidade Visual")
        
        if df_db_global.empty:
            st.warning("⚠️ O banco de dados está vazio. Cadastre ou importe alunos primeiro.")
        else:
            # Seleção do aluno vindo do cadastro
            lista_alunos_miguilim = ["Selecione o Aluno..."] + [f"{r['Id.']} - {r['Aluno']} (Turma: {r.get('Turma', 'N/I)})" for _, r in df_db_global.iterrows()]
            aluno_escolhido_mig = st.selectbox("Localizar Aluno no Cadastro:", lista_alunos_miguilim)
            
            # Inicializa dados padrão para preenchimento
            p_ensino_val, turma_val, aluno_val, cpf_val, mae_val, pbf_val = "", "", "", "", "", "Não"
            
            if aluno_escolhido_mig and aluno_escolhido_mig != "Selecione o Aluno...":
                id_alvo_mig = int(aluno_escolhido_mig.split(" - ")[0])
                match_mig = df_db_global[df_db_global["Id."] == id_alvo_mig]
                if not match_mig.empty:
                    dado_aluno = match_mig.iloc[0]
                    p_ensino_val = str(dado_aluno.get("Período de Ensino", ""))
                    turma_val = str(dado_aluno.get("Turma", ""))
                    aluno_val = str(dado_aluno.get("Aluno", ""))
                    cpf_val = str(dado_aluno.get("CPF", ""))
                    mae_val = str(dado_aluno.get("Mãe", ""))
                    pbf_val = str(dado_aluno.get("PBF", "Não"))
            
            with st.form("form_miguilim_acuidade"):
                st.markdown("##### 1. Bloco de Identificação")
                col_id1, col_id2 = st.columns(2)
                with col_id1:
                    val_periodo = st.text_input("Período de Ensino / Série (Ex: 1º, 2º...):", value=p_ensino_val)
                    val_aluno_nome = st.text_input("Aluno:", value=aluno_val)
                    val_cpf = st.text_input("CPF:", value=cpf_val)
                with col_id2:
                    val_turma = st.text_input("Turma:", value=turma_val)
                    val_mae = st.text_input("Mãe do Aluno:", value=mae_val)
                
                st.markdown("##### 2. Avaliação de Acuidade Visual e Condições")
                opcoes_visao = ["1.0", "0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1", "0.0", "Sem percepção luminosa"]
                
                col_v1, col_v2 = st.columns(2)
                with col_v1:
                    st.markdown("**2.1 - Sem óculos:**")
                    sem_dir = st.selectbox("Direito (Sem Óculos):", opcoes_visao, index=0)
                    sem_esq = st.selectbox("Esquerdo (Sem Óculos):", opcoes_visao, index=0)
                with col_v2:
                    st.markdown("**2.2 - Com óculos:**")
                    com_dir = st.selectbox("Direito (Com Óculos):", opcoes_visao, index=0)
                    com_esq = st.selectbox("Esquerdo (Com Óculos):", opcoes_visao, index=0)
                
                st.markdown("**2.3 - Condições Especiais:**")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    val_estrabismo = st.selectbox("Estrabismo:", ["Não", "Sim"])
                with col_c2:
                    # Traz do cadastro mas permite alteração manual
                    index_pbf = 1 if pbf_val.strip().lower() == "sim" else 0
                    val_pbf_edit = st.selectbox("PBF (Programa Bolsa Família / Critério social):", ["Não", "Sim"], index=index_pbf)
                
                btn_processar_miguilim = st.form_submit_button("🔍 Processar Resultado e Salvar Triagem")
                
                if btn_processar_miguilim:
                    if not val_aluno_nome or val_aluno_nome == "":
                        st.error("⚠️ O campo do Aluno é obrigatório para registrar a triagem.")
                    else:
                        def conv_v(txt):
                            if txt == "Sem percepção luminosa": return 0.0
                            try: return float(txt)
                            except: return 1.0
                        
                        d_s, e_s = conv_v(sem_dir), conv_v(sem_esq)
                        d_c, e_c = conv_v(com_dir), conv_v(com_esq)
                        
                        tem_alteracao_geral = (d_s < 1.0 or e_s < 1.0 or d_c < 1.0 or e_c < 1.0 or val_estrabismo == "Sim")
                        tem_valor_critico = (d_s <= 0.6 or e_s <= 0.6 or d_c <= 0.6 or e_c <= 0.6)
                        tem_alteracao_moderada = ((d_s > 0.6 and d_s < 1.0) or (e_s > 0.6 and e_s < 1.0) or 
                                                  (d_c > 0.6 and d_c < 1.0) or (e_c > 0.6 and e_c < 1.0))
                        
                        if not tem_alteracao_geral:
                            status_resultado = "Sem alteração"
                        elif tem_valor_critico:
                            status_resultado = "Encaminhado"
                        elif tem_alteracao_moderada or val_estrabismo == "Sim":
                            status_resultado = "Alteração Moderada"
                        else:
                            status_resultado = "Não Examinado"
                            
                        st.success(f"🎉 Triagem processada com sucesso! **Resultado Atribuído:** {status_resultado}")
                        registrar_log_auditoria(st.session_state["email_usuario"], st.session_state["perfil_usuario"], f"Realizou triagem Miguilim para o aluno {val_aluno_nome} - Status: {status_resultado}")

    elif sub_miguilim == "Encaminhamentos Clínicos":
        st.markdown("### 📋 Encaminhamentos Clínicos — Programa Miguilim")
        st.info("Painel analítico para listagem de alunos encaminhados e relatórios de acompanhamento clínico visual e auditivo.")
