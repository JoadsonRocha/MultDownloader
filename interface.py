import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkthemes import ThemedTk
from logica import BaixadorYouTube
import threading
import os
from PIL import Image, ImageTk  # Importação do Pillow

class InterfaceYouTube:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("MultDownloader")
        self.janela.geometry("800x250")
        self.janela.configure(bg='#252A34')
        self.janela.resizable(False, False)  # Impede o redimensionamento da janela

        try:
            # Caminho absoluto para o ícone
            
            caminho_icone = os.path.abspath("logo.ico")
            # Carrega a imagem usando Pillow
            icon_image = Image.open(caminho_icone)
            icon_photo = ImageTk.PhotoImage(icon_image)
            # Define o ícone da janela
            self.janela.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"Erro ao carregar o ícone: {e}")

        self.centralizar_janela()
        self.baixador = BaixadorYouTube(self.atualizar_interface)
        self.configurar_estilos()
        self.criar_widgets()

        # Variáveis para o spinner
        self.spinner_ativo = False
        self.spinner_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.spinner_index = 0

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configuração de cores principais
        self.style.configure('.', background='#252A34', foreground='#EAEAEA')
        self.style.configure('TFrame', background='#252A34')
        self.style.configure('TLabel', background='#252A34', foreground='#EAEAEA', font=('Arial', 12))
        self.style.configure('TEntry', fieldbackground='#393E46', foreground='#EAEAEA', bordercolor='#00ADB5', lightcolor='#252A34')
        self.style.configure('TCombobox', fieldbackground='#393E46', foreground='#00ADB5', background='#252A34', padding=5)
        self.style.map('TCombobox', fieldbackground=[('readonly', '#00ADB5')], foreground=[('readonly', 'black')])
        self.style.configure('TButton', background='#00ADB5', foreground='white', bordercolor='#EEEEEE', font=('Arial', 12, 'bold'))
        self.style.map('TButton',
                       background=[('active', '#008C9E'), ('pressed', '#005F6B')])

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
        label_title.grid(row=0, column=0, columnspan=4, pady=10)

        label_url = ttk.Label(self.frame, text="Cole a URL do vídeo:")
        label_url.grid(row=1, column=0, sticky="w", padx=15, pady=5)

        self.entry_url = ttk.Entry(self.frame, font=("Arial", 12), width=40)
        self.entry_url.grid(row=1, column=1, padx=(0, 10), pady=5, sticky="ew")
        self.criar_menu_contexto(self.entry_url)

        label_qualidade = ttk.Label(self.frame, text="Selecione a qualidade:")
        label_qualidade.grid(row=2, column=0, sticky="w", padx=10, pady=5)

        self.qualidade = tk.StringVar(value="best")
        opcoes_qualidade = ["Padrão", "1080p", "720p", "480p", "360p", "Áudio"]
        self.combo_qualidade = ttk.Combobox(self.frame, textvariable=self.qualidade, values=opcoes_qualidade, state="readonly", font=("Arial", 12))
        self.combo_qualidade.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=5)
        self.combo_qualidade.current(0)

        self.button_download = ttk.Button(self.frame, text="Baixar", command=self.iniciar_download)
        self.button_download.grid(row=1, column=2, pady=10, padx=10)

        # Label para o spinner
        self.label_spinner = ttk.Label(self.frame, text="", font=("Arial", 12))
        self.label_spinner.grid(row=1, column=3, padx=10, pady=10)

        self.label_status = ttk.Label(self.frame, text="", style='TLabel')
        self.label_status.grid(row=4, column=0, columnspan=4, pady=10)

        label_rodape = ttk.Label(self.frame, text="by Joadson copy 2025", style='TLabel', foreground="#B2B2B2")
        label_rodape.grid(row=5, column=0, columnspan=4, pady=10, sticky="s")

    def criar_menu_contexto(self, widget):
        menu_contexto = tk.Menu(widget, tearoff=0, bg='#393E46', fg='white', activebackground='#00ADB5', activeforeground='white')
        menu_contexto.add_command(label="Colar", command=lambda: widget.event_generate('<<Paste>>'))
        menu_contexto.add_command(label="Copiar", command=lambda: widget.event_generate('<<Copy>>'))
        menu_contexto.add_command(label="Recortar", command=lambda: widget.event_generate('<<Cut>>'))

        def mostrar_menu(event):
            menu_contexto.tk.call("tk_popup", menu_contexto, event.x_root, event.y_root)

        widget.bind("<Button-3>", mostrar_menu)

    def atualizar_interface(self, percentual, velocidade, tamanho):
        self.label_status.config(text=f"Baixando... {percentual} | Velocidade: {velocidade} | Tamanho: {tamanho}")

    def iniciar_spinner(self):
        """Inicia a animação do spinner."""
        if self.spinner_ativo:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            self.label_spinner.config(text=self.spinner_frames[self.spinner_index])
            self.janela.after(100, self.iniciar_spinner)  # Atualiza a cada 100ms

    def iniciar_download(self):
        url = self.entry_url.get()
        local_salvar = filedialog.askdirectory()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira uma URL válida.")
            return

        # Limpa a barra de progresso e desabilita o botão
        self.button_download.config(state=tk.DISABLED)

        # Inicia o spinner
        self.spinner_ativo = True
        self.iniciar_spinner()

        qualidade_selecionada = self.qualidade.get()
        qualidade_map = {
            "Padrão": "best",
            "1080p": "1080p",
            "720p": "720p",
            "480p": "480p",
            "360p": "360p",
            "Áudio": "somente áudio"
        }
        qualidade = qualidade_map.get(qualidade_selecionada, "best")

        threading.Thread(target=self.executar_download, args=(url, local_salvar, qualidade)).start()

    def parar_spinner(self):
        """Para a animação do spinner."""
        self.spinner_ativo = False
        self.label_spinner.config(text="")

    def executar_download(self, url, local_salvar, qualidade):
        if qualidade == "somente áudio":
            self.janela.after(0, self._mostrar_extracao_audio)
        resultado = self.baixador.baixar_video(url, local_salvar, qualidade)
        self.janela.after(0, self._finalizar_download, resultado)

    def _mostrar_extracao_audio(self):
        self.label_status.config(text="Extraindo áudio...")

    def _finalizar_download(self, resultado):
        # Para o spinner e reabilita o botão
        self.parar_spinner()
        self.label_status.config(text="")  # Limpa o status de extração
        messagebox.showinfo("Resultado", resultado)
        self.button_download.config(state=tk.NORMAL)

if __name__ == "__main__":
    janela = ThemedTk(theme="clam")
    app = InterfaceYouTube(janela)
    janela.mainloop()