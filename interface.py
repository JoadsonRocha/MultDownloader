# interface.py
from ttkthemes import ThemedTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from logica import BaixadorYouTube
import threading

class InterfaceYouTube:
    def __init__(self, janela):
        """
        Inicializa a interface gráfica.
        :param janela: Janela principal do Tkinter.
        """
        self.janela = janela
        self.janela.title("MultDownloader")
        self.janela.geometry("800x250")  # Aumentamos a altura para acomodar o menu de qualidade

        # Define o ícone da janela
        try:
            self.janela.iconbitmap("logo.ico")  # Substitua "logo.ico" pelo caminho da sua imagem
        except Exception as e:
            print(f"Erro ao carregar o ícone: {e}")

        # Centraliza a janela na tela
        self.centralizar_janela()

        # Inicializa o baixador de vídeos
        self.baixador = BaixadorYouTube(self.atualizar_interface)

        # Cria os widgets
        self.criar_widgets()

    def centralizar_janela(self):
        """
        Centraliza a janela na tela.
        """
        largura_janela = 800
        altura_janela = 250

        # Obtém as dimensões da tela
        largura_tela = self.janela.winfo_screenwidth()
        altura_tela = self.janela.winfo_screenheight()

        # Calcula as coordenadas para centralizar a janela
        x = (largura_tela // 2) - (largura_janela // 2)
        y = (altura_tela // 2) - (altura_janela // 2)

        # Define a posição da janela
        self.janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

    def criar_widgets(self):
        """
        Cria e organiza os widgets na interface.
        """
        self.frame = ttk.Frame(self.janela, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Título
        label_title = ttk.Label(self.frame, text="Baixe vídeos do YouTube, Instagran e facebook", font=("Arial", 14, "bold"))
        label_title.grid(row=0, column=1, columnspan=3, pady=10)

        # URL do vídeo
        label_url = ttk.Label(self.frame, text="Cole a URL do vídeo:", font=("Arial", 12))
        label_url.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        # Entrada URL
        self.entry_url = ttk.Entry(self.frame, font=("Arial", 12), width=40)
        self.entry_url.grid(row=1, column=1, padx=(0, 10), pady=5)

        # Menu de seleção de qualidade
        label_qualidade = ttk.Label(self.frame, text="Selecione a qualidade:", font=("Arial", 12))
        label_qualidade.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        # Caixa de seleção (Combobox) para qualidade
        self.qualidade = tk.StringVar(value="best")  # Valor padrão: melhor qualidade
        opcoes_qualidade = [
            "Melhor qualidade (best)",
            "1080p (137)",
            "720p (22)",
            "480p (135)",
            "360p (18)",
        ]

        self.combo_qualidade = ttk.Combobox(
            self.frame, textvariable=self.qualidade, values=opcoes_qualidade, state="readonly", font=("Arial", 12)
        )
        self.combo_qualidade.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=5)
        self.combo_qualidade.current(0)  # Define a primeira opção como selecionada por padrão

        # Botão de download
        self.button_download = ttk.Button(self.frame, text="Baixar", command=self.iniciar_download)
        self.button_download.grid(row=1, column=2, columnspan=2, pady=10)

        # Status do download
        self.label_status = ttk.Label(self.frame, text="", font=("Arial", 10))
        self.label_status.grid(row=4, column=0, columnspan=2)

        # Rodapé
        label_rodape = ttk.Label(self.frame, text="by Joadson copy 2025", font=("Arial", 10), foreground="gray")
        label_rodape.grid(row=5, column=1, columnspan=2, pady=10, sticky="s")

    def atualizar_interface(self, percentual, velocidade, tamanho):
        """
        Atualiza a interface com o progresso do download.
        :param percentual: Percentual de conclusão.
        :param velocidade: Velocidade de download.
        :param tamanho: Tamanho total do vídeo.
        """
        self.label_status.config(text=f"Baixando... {percentual} | Velocidade: {velocidade} | Tamanho: {tamanho}")

    def iniciar_download(self):
        """
        Inicia o download do vídeo em um thread separado.
        """
        url = self.entry_url.get()
        local_salvar = filedialog.askdirectory()

        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return

        # Desabilita o botão durante o download
        self.button_download.config(state=tk.DISABLED)

        # Obtém a qualidade selecionada
        qualidade_selecionada = self.qualidade.get()
        qualidade = qualidade_selecionada.split("(")[-1].replace(")", "").strip()  # Extrai o valor da qualidade

        # Inicia o download em um thread separado
        threading.Thread(target=self.executar_download, args=(url, local_salvar, qualidade)).start()

    def executar_download(self, url, local_salvar, qualidade):
        """
        Executa o download do vídeo e atualiza a interface ao finalizar.
        :param url: URL do vídeo.
        :param local_salvar: Diretório onde o vídeo será salvo.
        :param qualidade: Qualidade selecionada.
        """
        resultado = self.baixador.baixar_video(url, local_salvar, qualidade)
        messagebox.showinfo("Resultado", resultado)
        self.button_download.config(state=tk.NORMAL)  # Reabilita o botão
        

if __name__ == "__main__":
    janela = ThemedTk(theme="arc")  # Aplica o tema "arc"
    app = InterfaceYouTube(janela)
    janela.mainloop()