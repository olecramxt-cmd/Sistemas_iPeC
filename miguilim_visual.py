# =====================================================================
# Módulo de Triagem Visual - Programa Miguilim
# SISTEMAS iPeC - Integração com Base de Dados e Automação de Resultados
# © Prof. Esp. Marcelo Xavier Travassos - SISTEMAS iPeC.
# Versão: 1.0.0
# Data: 20/07/2026
# =====================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import openpyxl  # Exemplo de integração para manipulação de planilhas

class MiguilimVisualApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMAS iPeC - Programa Miguilim (Triagem Visual)")
        self.root.geometry("800x650")
        
        # Variáveis de controle dos campos
        self.var_periodo = tk.StringVar()
        self.var_turma = tk.StringVar()
        self.var_aluno = tk.StringVar()
        self.var_cpf = tk.StringVar()
        self.var_mae = tk.StringVar()
        
        # Acuidade Visual (Opções: 0.0 a 1.0 e Sem percepção luminosa)
        self.opcoes_visao = ["0.0", "0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0", "Sem percepção luminosa"]
        
        self.var_sem_oculos_dir = tk.StringVar(value=self.opcoes_visao[-2]) # Padrão 1.0
        self.var_sem_oculos_esq = tk.StringVar(value=self.opcoes_visao[-2])
        self.var_com_oculos_dir = tk.StringVar(value=self.opcoes_visao[-2])
        self.var_com_oculos_esq = tk.StringVar(value=self.opcoes_visao[-2])
        
        self.var_estrabismo = tk.StringVar(value="Não")
        self.var_pbf = tk.StringVar(value="Não") # Editável (trazido do cadastro)
        
        # Resultados automatizados
        self.var_resultado = tk.StringVar(value="Não Examinado")
        
        self.criar_interface()

    def criar_interface(self):
        # 1. Bloco de Identificação
        frame_id = ttk.LabelFrame(self.root, text=" 1. Bloco de Identificação (Dados do Aluno) ")
        frame_id.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame_id, text="Período/Ano (Ex: 1º, 2º...):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_id, textvariable=self.var_periodo, width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame_id, text="Turma:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_id, textvariable=self.var_turma, width=15).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame_id, text="Aluno:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_id, textvariable=self.var_aluno, width=40).grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame_id, text="CPF:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_id, textvariable=self.var_cpf, width=20).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame_id, text="Mãe do Aluno:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ttk.Entry(frame_id, textvariable=self.var_mae, width=30).grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # 2. Bloco de Avaliação Visual e Critérios Sociais
        frame_aval = ttk.LabelFrame(self.root, text=" 2. Avaliação de Acuidade Visual e Condições ")
        frame_aval.pack(fill="x", padx=10, pady=10)
        
        # 2.1 - Sem óculos
        ttk.Label(frame_aval, text="2.1 - Sem óculos [Direito]:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_sem_oculos_dir, values=self.opcoes_visao, width=22, state="readonly").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame_aval, text="[Esquerdo]:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_sem_oculos_esq, values=self.opcoes_visao, width=22, state="readonly").grid(row=0, column=3, padx=5, pady=5)
        
        # 2.2 - Com óculos
        ttk.Label(frame_aval, text="2.2 - Com óculos [Direito]:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_com_oculos_dir, values=self.opcoes_visao, width=22, state="readonly").grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame_aval, text="[Esquerdo]:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_com_oculos_esq, values=self.opcoes_visao, width=22, state="readonly").grid(row=1, column=3, padx=5, pady=5)
        
        # 2.3 - Possui (Estrabismo e PBF Editável)
        ttk.Label(frame_aval, text="2.3 - Estrabismo:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_estrabismo, values=["Sim", "Não"], width=10, state="readonly").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frame_aval, text="PBF (Bolsa Família):").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ttk.Combobox(frame_aval, textvariable=self.var_pbf, values=["Sim", "Não"], width=10, state="normal").grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # 3. Bloco de Resultados e Automatização
        frame_res = ttk.LabelFrame(self.root, text=" 3. Resultado e Encaminhamento (Automatizado) ")
        frame_res.pack(fill="x", padx=10, pady=10)
        
        btn_calcular = ttk.Button(frame_res, text="Processar Regras e Calcular Resultado", command=self.calcular_resultado)
        btn_calcular.pack(pady=5)
        
        ttk.Label(frame_res, text="Status Final Atribuído:").pack(anchor="w", padx=5)
        lbl_resultado_display = ttk.Label(frame_res, textvariable=self.var_resultado, font=("Arial", 11, "bold"), foreground="blue")
        lbl_resultado_display.pack(anchor="w", padx=5, pady=5)

        # Botão de Ação Geral
        btn_salvar = ttk.Button(self.root, text="Salvar Dados na Base", command=self.salvar_dados)
        btn_salvar.pack(pady=10)

    def converter_valor_visao(self, valor_str):
        """Converte o texto da combobox para float para fins de comparação lógica."""
        if valor_str == "Sem percepção luminosa":
            return 0.0
        try:
            return float(valor_str)
        except ValueError:
            return 1.0

    def calcular_resultado(self):
        """
        Aplica estritamente as regras de negócio definidas:
        - Sem alteração: Somente se não houver nenhuma ocorrência ou alteração abaixo de 1.0 (ou estrabismo).
        - Alteração Moderada: Se os valores de visão forem > 0.6.
        - Encaminhado: Se houver valores <= 0.6 nos campos do título 2.
        - Não Examinado: Se nenhum dos campos acima se encaixar por padrão vazio/não preenchido.
        """
        # Coleta os valores convertidos
        d_sem = self.converter_valor_visao(self.var_sem_oculos_dir.get())
        e_sem = self.converter_valor_visao(self.var_sem_oculos_esq.get())
        d_com = self.converter_valor_visao(self.var_com_oculos_dir.get())
        e_com = self.converter_valor_visao(self.var_com_oculos_esq.get())
        estrabismo = self.var_estrabismo.get()

        # Verifica se há qualquer indicação de alteração visual ou estrabismo
        tem_alteracao_geral = (d_sem < 1.0 or e_sem < 1.0 or d_com < 1.0 or e_com < 1.0 or estrabismo == "Sim")
        
        # Verifica se existe algum valor menor ou igual a 0.6 (Critério de Encaminhamento)
        tem_valor_critico = (d_sem <= 0.6 or e_sem <= 0.6 or d_com <= 0.6 or e_com <= 0.6)
        
        # Verifica se existe alteração moderada (> 0.6, mas menor que 1.0)
        tem_alteracao_moderada = ((d_sem > 0.6 and d_sem < 1.0) or (e_sem > 0.6 and e_sem < 1.0) or 
                                  (d_com > 0.6 and d_com < 1.0) or (e_com > 0.6 and e_com < 1.0))

        # Aplicação das regras sequenciais:
        if not tem_alteracao_geral:
            self.var_resultado.set("Sem alteração")
        elif tem_valor_critico:
            self.var_resultado.set("Encaminhado")
        elif tem_alteracao_moderada or estrabismo == "Sim":
            self.var_resultado.set("Alteração Moderada")
        else:
            self.var_resultado.set("Não Examinado")

    def salvar_dados(self):
        # Executa o cálculo antes de salvar para garantir consistência
        self.calcular_resultado()
        
        # Aqui entra a lógica de persistência conectada com a planilha unificada do ecossistema iPeC
        resultado_atual = self.var_resultado.get()
        aluno_nome = self.var_aluno.get()
        
        if not aluno_nome:
            messagebox.showwarning("Aviso", "O campo do Aluno é obrigatório para gravação!")
            return
            
        messagebox.showinfo("Sucesso", f"Dados do(a) aluno(a) {aluno_nome} processados com sucesso!\nStatus Definido: {resultado_atual}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MiguilimVisualApp(root)
    root.mainloop()
