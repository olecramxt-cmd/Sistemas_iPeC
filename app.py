# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão do código: v.1.5.019 - data: 24/07/26 - 06:23

# [Trecho do Catálogo do Acervo corrigido para substituição exata]

            elif sub_biblioteca == "Catálogo do Acervo":
                st.markdown(f"#### 📖 Gestão do Acervo Bibliográfico ({ano_letivo_escolhido})")
                
                df_emprestimos_geral = carregar_emprestimos_biblioteca()
                
                st.markdown("##### 🔍 Pesquisa de Obras no Acervo")
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    termo_titulo = st.text_input("Filtrar por Título da Obra:", key="filtro_tit_bib")
                with col_p2:
                    termo_autor = st.text_input("Filtrar por Autor / Organizador:", key="filtro_aut_bib")
                with col_p3:
                    filtro_cat = st.selectbox("Filtrar por Categoria:", ["Todas", "Didático", "Literário"], key="filtro_cat_bib")

                df_acervo_filtrado = df_acervo_geral.copy()
                if not df_acervo_filtrado.empty:
                    if termo_titulo:
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Titulo"].str.contains(termo_titulo, case=False, na=False)]
                    if termo_autor:
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Autor"].str.contains(termo_autor, case=False, na=False)]
                    if filtro_cat != "Todas":
                        df_acervo_filtrado = df_acervo_filtrado[df_acervo_filtrado["Categoria"].str.strip() == filtro_cat]

                st.markdown("##### 📋 Acervo Localizado (Clique na linha para carregar no formulário abaixo)")
                
                # Variáveis locais de apoio para preenchimento limpo
                val_t = ""
                val_tit = ""
                val_aut = ""
                val_cat_idx = 0
                val_disc = ""
                val_tot = 1

                if not df_acervo_filtrado.empty:
                    tabela_evento = st.dataframe(
                        df_acervo_filtrado, 
                        use_container_width=True, 
                        hide_index=True, 
                        selection_mode="single-row", 
                        on_select="rerun",
                        key="tabela_acervo_selecao_v7"
                    )
                    
                    try:
                        linhas_selecionadas = tabela_evento.get("selection", {}).get("rows", [])
                        if linhas_selecionadas:
                            idx_sel = linhas_selecionadas[0]
                            livro_selecionado_linha = df_acervo_filtrado.iloc[idx_sel]
                            
                            val_t = str(livro_selecionado_linha.get("Tombo", ""))
                            val_tit = str(livro_selecionado_linha.get("Titulo", ""))
                            val_autor_linha = str(livro_selecionado_linha.get("Autor", ""))
                            val_cat_linha = str(livro_selecionado_linha.get("Categoria", "Didático"))
                            val_cat_idx = 0 if val_cat_linha.strip().lower() == "didático" else 1
                            val_disc = str(livro_selecionado_linha.get("Disciplina", ""))
                            val_tot = 1
                    except Exception: pass
                else:
                    st.info("ℹ️ Nenhum livro cadastrado ou localizado com os filtros informados.")

                st.markdown("---")
                st.markdown("##### ✍️ Cadastro de Livro e Alteração (Reativo ao Clique)")
                
                # Formulário nativo do Streamlit para isolar o estado dos inputs sem conflito de session_state externo
                with st.form("form_cadastro_alteracao_livro_limpo", clear_on_submit=False):
                    input_tombo = st.text_input("Código de Tombo / ISBN Base:", value=val_t)
                    input_titulo = st.text_input("Título da Obra:", value=val_tit)
                    
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        input_autor = st.text_input("Autor / Organizador:", value=val_aut)
                    with col_f2:
                        input_cat = st.selectbox("Categoria:", ["Didático", "Literário"], index=val_cat_idx)
                    
                    col_f3, col_f4 = st.columns(2)
                    with col_f3:
                        input_disc = st.text_input("Gênero / Disciplina:", value=val_disc)
                    with col_f4:
                        input_total = st.number_input("Total de Novos Exemplares a Gerar:", min_value=1, value=val_tot)
                    
                    st.markdown("---")
                    st.markdown("##### ⚙️ Ações e Gerenciamento do Livro")
                    
                    col_b1, col_b2, col_b3 = st.columns(3)
                    btn_salvar_livro = col_b1.form_submit_button("💾 Salvar Livro")
                    btn_alterar_livro = col_b2.form_submit_button("🔄 Alterar Livro")
                    btn_excluir_livro = col_b3.form_submit_button("🗑️ Excluir Livro")

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
                    confirma_excluir_form = st.radio("Deseja realmente prosseguir com a exclusão deste livro?", ["Não", "Sim"], index=0, key="radio_conf_exc_form_seguro_v7")
                    
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
                                        st.session_state.acionou_exclusao_form = False
                                        st.session_state.tombo_para_excluir_seguro = ""
                                        st.success("🎉 Livro excluído/inativado com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error(f"⚠️ Tombo '{tombo_alvo_exc}' não localizado na planilha.")
                                except Exception as err_exc_aba:
                                    st.error(f"Erro ao excluir: {err_exc_aba}")
