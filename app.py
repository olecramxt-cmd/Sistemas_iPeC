elif sub_conformidade == "Atualização de Dados":
                    st.markdown(f"#### 🔍 Atualização e Edição Individual de Alunos ({ano_letivo_escolhido})")
                    
                    if df_db_ano.empty:
                        st.warning("⚠️ Nenhum aluno cadastrado para este ano letivo.")
                    else:
                        lista_alunos_cadastrados = ["Selecione o Aluno..."] + [f"{int(r['Id.'])} - {r['Aluno']} (Mãe: {r['Mãe']})" for _, r in df_db_ano.iterrows()]
                        aluno_selecionado_busca = st.selectbox("Selecione o aluno para alteração individual:", lista_alunos_cadastrados, key="sel_aluno_atualizacao_individual_v51")
                        
                        if aluno_selecionado_busca and aluno_selecionado_busca != "Selecione o Aluno...":
                            try:
                                id_alvo_ind = int(aluno_selecionado_busca.split(" - ")[0])
                                df_aluno_ind = df_db_ano[df_db_ano["Id."] == id_alvo_ind].copy()
                                
                                if not df_aluno_ind.empty:
                                    st.markdown("##### ✍️ Ficha Cadastral e Edição Individual do Aluno")
                                    reg_atual = df_aluno_ind.iloc[0]
                                    
                                    with st.form(f"form_atualizacao_individual_v51_{id_alvo_ind}"):
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
                            except Exception as err_sel:
                                st.error(f"Erro ao carregar dados do aluno: {err_sel}")
