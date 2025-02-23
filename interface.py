from ttkthemes import ThemedTk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from logica import BaixadorYouTube
import threading

class InterfaceYouTube:
    def __init__(self, janela):
        """
        Inicializa a interface gráfica.
        """
        self.janela = janela
        self.janela.title("MultDownloader")
        self.janela.geometry("800x250")

        try:
            self.janela.iconbitmap("logo.ico")
        except Exception as e:
            print(f"Erro ao carregar o ícone: {e}")

        self.centralizar_janela()
        self.baixador = BaixadorYouTube(self.atualizar_interface)
        self.criar_widgets()

    def centralizar_janela(self):
        largura_janela = 800
        altura_janela = 250
        largura_tela = self.janela.winfo_screenwidth()
        altura_tela = self.janela.winfo_screenheight()
        x = (largura_tela // 2) - (largura_janela // 2)
        y = (altura_tela // 2) - (altura_janela // 2)
        self.janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

    def criar_widgets(self):
        self.frame = ttk.Frame(self.janela, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        label_title = ttk.Label(self.frame, text="Baixe vídeos do YouTube, Instagram e Facebook", font=("Arial", 14, "bold"))
        label_title.grid(row=0, column=1, columnspan=3, pady=10)

        label_url = ttk.Label(self.frame, text="Cole a URL do vídeo:", font=("Arial", 12))
        label_url.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        self.entry_url = ttk.Entry(self.frame, font=("Arial", 12), width=40)
        self.entry_url.grid(row=1, column=1, padx=(0, 10), pady=5)

        label_qualidade = ttk.Label(self.frame, text="Selecione a qualidade:", font=("Arial", 12))
        label_qualidade.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.qualidade = tk.StringVar(value="best")
        opcoes_qualidade = ["Padrão", "1080p", "720p", "480p", "360p", "Somente Áudio"]
        self.combo_qualidade = ttk.Combobox(self.frame, textvariable=self.qualidade, values=opcoes_qualidade, state="readonly", font=("Arial", 12))
        self.combo_qualidade.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=5)
        self.combo_qualidade.current(0)

        self.button_download = ttk.Button(self.frame, text="Baixar", command=self.iniciar_download)
        self.button_download.grid(row=1, column=2, columnspan=2, pady=10)

        self.label_status = ttk.Label(self.frame, text="", font=("Arial", 10))
        self.label_status.grid(row=4, column=0, columnspan=2)

        label_rodape = ttk.Label(self.frame, text="by Joadson copy 2025", font=("Arial", 10), foreground="gray")
        label_rodape.grid(row=5, column=1, columnspan=2, pady=10, sticky="s")

    def atualizar_interface(self, percentual, velocidade, tamanho):
        self.label_status.config(text=f"Baixando... {percentual} | Velocidade: {velocidade} | Tamanho: {tamanho}")

    def iniciar_download(self):
        url = self.entry_url.get()
        local_salvar = filedialog.askdirectory()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return

        self.button_download.config(state=tk.DISABLED)

        # Mapeamento das opções de qualidade
        qualidade_selecionada = self.qualidade.get()
        if qualidade_selecionada == "Padrão":
            qualidade = "best"
        elif qualidade_selecionada == "1080p":
            qualidade = "1080p"
        elif qualidade_selecionada == "720p":
            qualidade = "720p"
        elif qualidade_selecionada == "480p":
            qualidade = "480p"
        elif qualidade_selecionada == "360p":
            qualidade = "360p"
        elif qualidade_selecionada == "Somente Áudio":
            qualidade = "somente áudio"
        else:
            qualidade = "best"  # Padrão para o melhor formato

        threading.Thread(target=self.executar_download, args=(url, local_salvar, qualidade)).start()

    def executar_download(self, url, local_salvar, qualidade):
        resultado = self.baixador.baixar_video(url, local_salvar, qualidade)
        messagebox.showinfo("Resultado", resultado)
        self.button_download.config(state=tk.NORMAL)

if __name__ == "__main__":
    janela = ThemedTk(theme="arc")
    app = InterfaceYouTube(janela)
    janela.mainloop()
