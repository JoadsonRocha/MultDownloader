"""
Módulo de Interface Gráfica (MultDownloader)
============================================
Interface moderna desenvolvida em Tkinter com suporte a temas estilizados,
barra de progresso em tempo real, telemetria de download, prévia de vídeo,
seleção persistente de pasta e total segurança de threads.

Autor: Joadson Rocha / MultDownloader Team
Licença: MIT
"""

import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any

from PIL import Image, ImageTk
from ttkthemes import ThemedTk
from logica import BaixadorYouTube


class InterfaceYouTube:
    """Interface principal do aplicativo MultDownloader."""

    # Paleta de cores moderna (Dark Slate / Teal Theme)
    BG_DARK = "#1E222B"
    BG_CARD = "#282C34"
    BG_INPUT = "#323842"
    TEXT_PRIMARY = "#ECEFF4"
    TEXT_SECONDARY = "#ABB2BF"
    ACCENT_CYAN = "#00ADB5"
    ACCENT_HOVER = "#008B94"
    ACCENT_DANGER = "#E06C75"
    ACCENT_DANGER_HOVER = "#C6535C"
    ACCENT_SUCCESS = "#98C379"

    def __init__(self, janela: ThemedTk):
        self.janela = janela
        self.janela.title("MultDownloader - Baixador Universal de Mídias")
        self.janela.geometry("860x490")
        self.janela.minsize(800, 470)
        self.janela.configure(bg=self.BG_DARK)

        # Fila thread-safe para comunicação entre threads secundárias e a GUI
        self.fila_gui: queue.Queue = queue.Queue()

        # Instância do mecanismo de download
        self.baixador = BaixadorYouTube(callback_progresso=self._enfileirar_progresso)
        self.download_em_andamento = False
        self.thread_ativa: Optional[threading.Thread] = None

        # Pasta de download padrão (Downloads do usuário)
        self.pasta_padrao = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(self.pasta_padrao):
            self.pasta_padrao = os.getcwd()

        self._configurar_icone()
        self._centralizar_janela()
        self._configurar_estilos()
        self._criar_widgets()
        self._iniciar_escuta_fila()

        # Intercepta evento de fechar janela
        self.janela.protocol("WM_DELETE_WINDOW", self._ao_fechar_janela)

    def _configurar_icone(self):
        """Carrega o ícone da aplicação com suporte a Pillow e fallback gracioso."""
        try:
            caminho_icone = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            if os.path.exists(caminho_icone):
                if sys.platform.startswith('win'):
                    self.janela.iconbitmap(caminho_icone)
                else:
                    icon_image = Image.open(caminho_icone)
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    self.janela.iconphoto(True, icon_photo)
        except Exception as e:
            print(f"[Aviso] Não foi possível carregar o ícone: {e}")

    def _centralizar_janela(self):
        """Centraliza a janela na tela do usuário."""
        self.janela.update_idletasks()
        largura = 860
        altura = 490
        x = max(0, (self.janela.winfo_screenwidth() // 2) - (largura // 2))
        y = max(0, (self.janela.winfo_screenheight() // 2) - (altura // 2))
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")

    def _configurar_estilos(self):
        """Configura a estilização customizada dos componentes ttk."""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configurações globais
        self.style.configure('.', background=self.BG_DARK, foreground=self.TEXT_PRIMARY)
        self.style.configure('TFrame', background=self.BG_DARK)
        self.style.configure('Card.TFrame', background=self.BG_CARD)

        # Rótulos (Labels)
        self.style.configure('Header.TLabel', background=self.BG_DARK, foreground=self.TEXT_PRIMARY, font=('Helvetica', 16, 'bold'))
        self.style.configure('Subtitle.TLabel', background=self.BG_DARK, foreground=self.TEXT_SECONDARY, font=('Helvetica', 10))
        self.style.configure('Card.TLabel', background=self.BG_CARD, foreground=self.TEXT_PRIMARY, font=('Helvetica', 10))
        self.style.configure('CardBold.TLabel', background=self.BG_CARD, foreground=self.TEXT_PRIMARY, font=('Helvetica', 10, 'bold'))
        self.style.configure('CardMuted.TLabel', background=self.BG_CARD, foreground=self.TEXT_SECONDARY, font=('Helvetica', 9))
        self.style.configure('Telemetry.TLabel', background=self.BG_DARK, foreground=self.TEXT_SECONDARY, font=('Consolas', 9))
        self.style.configure('Status.TLabel', background=self.BG_DARK, foreground=self.ACCENT_CYAN, font=('Helvetica', 10, 'bold'))

        # Entradas (Entry)
        self.style.configure('TEntry', fieldbackground=self.BG_INPUT, foreground=self.TEXT_PRIMARY, insertcolor='white', borderwidth=1)

        # Combobox
        self.style.configure('TCombobox', fieldbackground=self.BG_INPUT, foreground=self.TEXT_PRIMARY, background=self.BG_CARD, arrowcolor=self.ACCENT_CYAN)
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', self.BG_INPUT)],
                       foreground=[('readonly', self.TEXT_PRIMARY)])

        # Botões Principais (Action Button)
        self.style.configure('Primary.TButton',
                             background=self.ACCENT_CYAN,
                             foreground='white',
                             font=('Helvetica', 10, 'bold'),
                             padding=6,
                             borderwidth=0)
        self.style.map('Primary.TButton',
                       background=[('active', self.ACCENT_HOVER), ('disabled', '#3E4451')],
                       foreground=[('disabled', '#6B7280')])

        # Botão Secundário / Utilitário
        self.style.configure('Secondary.TButton',
                             background=self.BG_INPUT,
                             foreground=self.TEXT_PRIMARY,
                             font=('Helvetica', 9),
                             padding=5,
                             borderwidth=0)
        self.style.map('Secondary.TButton',
                       background=[('active', '#434A56'), ('disabled', '#252A32')],
                       foreground=[('disabled', '#5C6370')])

        # Botão de Perigo / Cancelar
        self.style.configure('Danger.TButton',
                             background=self.ACCENT_DANGER,
                             foreground='white',
                             font=('Helvetica', 10, 'bold'),
                             padding=6,
                             borderwidth=0)
        self.style.map('Danger.TButton',
                       background=[('active', self.ACCENT_DANGER_HOVER), ('disabled', '#3E4451')],
                       foreground=[('disabled', '#6B7280')])

        # Barra de Progresso
        self.style.configure('Custom.Horizontal.TProgressbar',
                             troughcolor=self.BG_INPUT,
                             background=self.ACCENT_CYAN,
                             thickness=14,
                             borderwidth=0)

    def _criar_widgets(self):
        """Monta a estrutura visual e componentes da interface."""
        conteiner = ttk.Frame(self.janela, padding="16")
        conteiner.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # 1. CABEÇALHO (Header)
        # ==========================================
        frame_header = ttk.Frame(conteiner)
        frame_header.pack(fill=tk.X, pady=(0, 12))

        lbl_titulo = ttk.Label(frame_header, text="⚡ MultDownloader", style='Header.TLabel')
        lbl_titulo.pack(side=tk.LEFT)

        # Indicador de status do FFmpeg
        disponivel_ffmpeg, _ = self.baixador.verificar_ffmpeg()
        status_ffmpeg_texto = "✓ FFmpeg Ativo" if disponivel_ffmpeg else "⚠ FFmpeg Não Detectado"
        status_ffmpeg_cor = self.ACCENT_SUCCESS if disponivel_ffmpeg else self.ACCENT_DANGER
        self.lbl_ffmpeg = tk.Label(frame_header, text=status_ffmpeg_texto, bg=self.BG_DARK, fg=status_ffmpeg_cor, font=('Helvetica', 9, 'bold'))
        self.lbl_ffmpeg.pack(side=tk.RIGHT, pady=4)

        lbl_sub = ttk.Label(conteiner, text="Baixe vídeos e extraia áudios de YouTube, Instagram, Facebook, TikTok, Twitter/X e mais.", style='Subtitle.TLabel')
        lbl_sub.pack(anchor="w", pady=(0, 12))

        # ==========================================
        # 2. CAMPO DE URL COM AÇÕES RÁPIDAS
        # ==========================================
        frame_url = ttk.Frame(conteiner)
        frame_url.pack(fill=tk.X, pady=(0, 10))

        lbl_url = ttk.Label(frame_url, text="URL da Mídia:", style='TLabel', font=('Helvetica', 10, 'bold'))
        lbl_url.pack(anchor="w", pady=(0, 4))

        frame_url_input = ttk.Frame(frame_url)
        frame_url_input.pack(fill=tk.X)

        self.var_url = tk.StringVar()
        self.entry_url = ttk.Entry(frame_url_input, textvariable=self.var_url, font=("Helvetica", 11))
        self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), ipady=3)
        self._criar_menu_contexto(self.entry_url)

        self.btn_colar = ttk.Button(frame_url_input, text="📋 Colar", style='Secondary.TButton', command=self._acao_colar_url)
        self.btn_colar.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_limpar = ttk.Button(frame_url_input, text="✕", width=3, style='Secondary.TButton', command=self._acao_limpar_url)
        self.btn_limpar.pack(side=tk.LEFT)

        # ==========================================
        # 3. CARD DE PRÉVIA DA MÍDIA (Info Box)
        # ==========================================
        self.frame_preview = ttk.Frame(conteiner, style='Card.TFrame', padding="10")
        self.frame_preview.pack(fill=tk.X, pady=(0, 10))

        self.lbl_prev_titulo = ttk.Label(self.frame_preview, text="Cole um link acima para identificar a mídia...", style='CardBold.TLabel', wraplength=800)
        self.lbl_prev_titulo.pack(anchor="w")

        self.lbl_prev_detalhes = ttk.Label(self.frame_preview, text="Plataformas suportadas: YouTube, Instagram, Facebook, TikTok, etc.", style='CardMuted.TLabel')
        self.lbl_prev_detalhes.pack(anchor="w", pady=(2, 0))

        # ==========================================
        # 4. OPÇÕES: QUALIDADE E PASTA DE DESTINO
        # ==========================================
        frame_opcoes = ttk.Frame(conteiner)
        frame_opcoes.pack(fill=tk.X, pady=(0, 12))

        # Coluna Qualidade
        frame_qualidade = ttk.Frame(frame_opcoes)
        frame_qualidade.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        lbl_qualidade = ttk.Label(frame_qualidade, text="Formato / Resolução:", font=('Helvetica', 10, 'bold'))
        lbl_qualidade.pack(anchor="w", pady=(0, 4))

        opcoes_qualidade = [
            "Melhor Qualidade (Auto)",
            "1080p Full HD",
            "720p HD",
            "480p SD",
            "360p",
            "Áudio MP3 (320 kbps)",
            "Áudio MP3 (192 kbps)",
            "Áudio M4A / AAC"
        ]
        self.var_qualidade = tk.StringVar(value=opcoes_qualidade[0])
        self.combo_qualidade = ttk.Combobox(frame_qualidade, textvariable=self.var_qualidade, values=opcoes_qualidade, state="readonly", font=("Helvetica", 10))
        self.combo_qualidade.pack(fill=tk.X, ipady=3)

        # Coluna Pasta de Destino
        frame_pasta = ttk.Frame(frame_opcoes)
        frame_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_pasta = ttk.Label(frame_pasta, text="Salvar em:", font=('Helvetica', 10, 'bold'))
        lbl_pasta.pack(anchor="w", pady=(0, 4))

        frame_pasta_input = ttk.Frame(frame_pasta)
        frame_pasta_input.pack(fill=tk.X)

        self.var_pasta = tk.StringVar(value=self.pasta_padrao)
        self.entry_pasta = ttk.Entry(frame_pasta_input, textvariable=self.var_pasta, font=("Helvetica", 9))
        self.entry_pasta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4), ipady=3)

        self.btn_pasta = ttk.Button(frame_pasta_input, text="📁 Procurar", style='Secondary.TButton', command=self._acao_selecionar_pasta)
        self.btn_pasta.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_abrir_pasta = ttk.Button(frame_pasta_input, text="📂 Abrir", style='Secondary.TButton', command=self._acao_abrir_pasta)
        self.btn_abrir_pasta.pack(side=tk.LEFT)

        # ==========================================
        # 5. BARRA DE PROGRESSO E TELEMETRIA
        # ==========================================
        frame_progresso = ttk.Frame(conteiner)
        frame_progresso.pack(fill=tk.X, pady=(0, 12))

        self.barra_progresso = ttk.Progressbar(frame_progresso, style='Custom.Horizontal.TProgressbar', mode='determinate', maximum=100.0)
        self.barra_progresso.pack(fill=tk.X, pady=(0, 4))

        frame_telemetria = ttk.Frame(frame_progresso)
        frame_telemetria.pack(fill=tk.X)

        self.lbl_status = ttk.Label(frame_telemetria, text="Pronto para iniciar.", style='Status.TLabel')
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_tamanho = ttk.Label(frame_telemetria, text="Tamanho: --", style='Telemetry.TLabel')
        self.lbl_tamanho.pack(side=tk.LEFT, padx=(16, 0))

        self.lbl_velocidade = ttk.Label(frame_telemetria, text="Velocidade: --", style='Telemetry.TLabel')
        self.lbl_velocidade.pack(side=tk.LEFT, padx=(16, 0))

        self.lbl_eta = ttk.Label(frame_telemetria, text="ETA: --", style='Telemetry.TLabel')
        self.lbl_eta.pack(side=tk.RIGHT)

        # ==========================================
        # 6. BOTÕES DE AÇÃO (Iniciar / Cancelar)
        # ==========================================
        frame_acoes = ttk.Frame(conteiner)
        frame_acoes.pack(fill=tk.X, pady=(4, 0))

        self.btn_download = ttk.Button(frame_acoes, text="⬇  Iniciar Download", style='Primary.TButton', command=self._acao_iniciar_download)
        self.btn_download.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)

        self.btn_cancelar = ttk.Button(frame_acoes, text="⏹ Cancelar", style='Danger.TButton', command=self._acao_cancelar_download, state=tk.DISABLED)
        self.btn_cancelar.pack(side=tk.RIGHT, ipady=4)

    def _criar_menu_contexto(self, widget: tk.Widget):
        """Cria menu de contexto com botão direito do mouse."""
        menu = tk.Menu(widget, tearoff=0, bg=self.BG_INPUT, fg=self.TEXT_PRIMARY,
                       activebackground=self.ACCENT_CYAN, activeforeground='white', borderwidth=1)
        menu.add_command(label="Colar", command=self._acao_colar_url)
        menu.add_command(label="Copiar", command=lambda: widget.event_generate('<<Copy>>'))
        menu.add_command(label="Recortar", command=lambda: widget.event_generate('<<Cut>>'))
        menu.add_separator()
        menu.add_command(label="Limpar", command=self._acao_limpar_url)

        def exibir_popup(event):
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", exibir_popup)

    def _acao_colar_url(self):
        """Cola conteúdo da área de transferência e busca metadados automaticamente."""
        try:
            conteudo = self.janela.clipboard_get().strip()
            if conteudo:
                self.var_url.set(conteudo)
                self._buscar_metadados_assincrono(conteudo)
        except Exception:
            pass

    def _acao_limpar_url(self):
        """Limpa campo de URL e reseta a prévia."""
        self.var_url.set("")
        self.lbl_prev_titulo.config(text="Cole um link acima para identificar a mídia...")
        self.lbl_prev_detalhes.config(text="Plataformas suportadas: YouTube, Instagram, Facebook, TikTok, etc.")

    def _buscar_metadados_assincrono(self, url: str):
        """Dispara busca assíncrona de informações do vídeo."""
        valido, _ = BaixadorYouTube.validar_url(url)
        if not valido:
            return

        self.lbl_prev_titulo.config(text="Buscando informações da mídia...")
        self.lbl_prev_detalhes.config(text="Aguarde...")

        def tarefa():
            info = self.baixador.obter_info_video(url)
            self.fila_gui.put(('metadata', info))

        threading.Thread(target=tarefa, daemon=True).start()

    def _acao_selecionar_pasta(self):
        """Abre diálogo para seleção da pasta de destino."""
        pasta = filedialog.askdirectory(initialdir=self.var_pasta.get())
        if pasta:
            self.var_pasta.set(pasta)

    def _acao_abrir_pasta(self):
        """Abre a pasta de destino no gerenciador de arquivos do sistema operacional."""
        caminho = self.var_pasta.get()
        if not os.path.exists(caminho):
            os.makedirs(caminho, exist_ok=True)
        try:
            if sys.platform.startswith('win'):
                os.startfile(caminho)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', caminho])
            else:
                subprocess.Popen(['xdg-open', caminho])
        except Exception as e:
            messagebox.showwarning("Aviso", f"Não foi possível abrir a pasta:\n{e}")

    def _enfileirar_progresso(self, dados: Dict[str, Any]):
        """Callback thread-safe para enfileirar atualizações de progresso."""
        self.fila_gui.put(('progress', dados))

    def _iniciar_escuta_fila(self):
        """Loop contínuo no thread principal para processar mensagens da GUI."""
        try:
            while not self.fila_gui.empty():
                tipo, dados = self.fila_gui.get_nowait()

                if tipo == 'progress':
                    self._atualizar_ui_progresso(dados)
                elif tipo == 'metadata':
                    self._atualizar_ui_metadata(dados)
                elif tipo == 'completed':
                    sucesso, mensagem = dados
                    self._finalizar_download(sucesso, mensagem)

        except queue.Empty:
            pass
        finally:
            self.janela.after(50, self._iniciar_escuta_fila)

    def _atualizar_ui_progresso(self, d: Dict[str, Any]):
        """Atualiza a barra de progresso e rótulos de telemetria na interface gráfica."""
        status = d.get('status')
        percent = d.get('percent', 0.0)

        self.barra_progresso['value'] = percent

        if status == 'downloading':
            self.lbl_status.config(text=f"Baixando... {d.get('percent_str', '')}")
            self.lbl_velocidade.config(text=f"Velocidade: {d.get('speed_str', '--')}")
            self.lbl_tamanho.config(text=f"Tamanho: {d.get('size_str', '--')}")
            self.lbl_eta.config(text=f"ETA: {d.get('eta_str', '--')}")
        elif status == 'finished' or status == 'completed':
            self.lbl_status.config(text="Processando / Concluído!")
            self.lbl_velocidade.config(text="Velocidade: --")
            self.lbl_eta.config(text="ETA: 00:00")

    def _atualizar_ui_metadata(self, info: Dict[str, Any]):
        """Atualiza o card de prévia com os metadados recebidos."""
        if 'erro' in info:
            self.lbl_prev_titulo.config(text="Link detectado (Prévia indisponível)")
            self.lbl_prev_detalhes.config(text=f"Aviso: {info['erro']}")
        else:
            titulo = info.get('title', 'Vídeo sem título')
            autor = info.get('uploader', 'Desconhecido')
            duracao = info.get('duration_str', 'N/A')
            origem = info.get('extractor', 'Web')
            self.lbl_prev_titulo.config(text=f"🎬 {titulo}")
            self.lbl_prev_detalhes.config(text=f"👤 Canal: {autor}   |   ⏱️ Duração: {duracao}   |   🌐 Origem: {origem}")

    def _acao_iniciar_download(self):
        """Inicia o processo de download em uma thread secundária."""
        url = self.var_url.get().strip()
        pasta = self.var_pasta.get().strip()
        qualidade = self.var_qualidade.get()

        valido, msg_url = BaixadorYouTube.validar_url(url)
        if not valido:
            messagebox.showerror("URL Inválida", msg_url)
            return

        if not pasta:
            messagebox.showerror("Erro de Destino", "Selecione uma pasta para salvar o arquivo.")
            return

        # Bloqueia UI e habilita botão de cancelamento
        self.download_em_andamento = True
        self.btn_download.config(state=tk.DISABLED)
        self.btn_cancelar.config(state=tk.NORMAL)
        self.barra_progresso['value'] = 0
        self.lbl_status.config(text="Iniciando download...")
        self.lbl_velocidade.config(text="Velocidade: Calculando...")
        self.lbl_tamanho.config(text="Tamanho: Conectando...")
        self.lbl_eta.config(text="ETA: --")

        def worker():
            sucesso, resultado = self.baixador.baixar_video(url, pasta, qualidade)
            self.fila_gui.put(('completed', (sucesso, resultado)))

        self.thread_ativa = threading.Thread(target=worker, daemon=True)
        self.thread_ativa.start()

    def _acao_cancelar_download(self):
        """Solicita o cancelamento seguro do download em andamento."""
        if self.download_em_andamento:
            self.lbl_status.config(text="Cancelando download...")
            self.baixador.cancelar_download()
            self.btn_cancelar.config(state=tk.DISABLED)

    def _finalizar_download(self, sucesso: bool, mensagem: str):
        """Restaura o estado da UI e exibe o resultado do download."""
        self.download_em_andamento = False
        self.btn_download.config(state=tk.NORMAL)
        self.btn_cancelar.config(state=tk.DISABLED)

        if sucesso:
            self.lbl_status.config(text="Download concluído com sucesso!")
            messagebox.showinfo("Sucesso", mensagem)
        else:
            self.lbl_status.config(text="Falha ou cancelamento.")
            if "cancelado" in mensagem.lower():
                messagebox.showwarning("Cancelado", mensagem)
            else:
                messagebox.showerror("Erro no Download", mensagem)

    def _ao_fechar_janela(self):
        """Gerencia o encerramento seguro caso haja download em execução."""
        if self.download_em_andamento:
            resposta = messagebox.askyesno(
                "Download em Execução",
                "Existe um download em andamento. Deseja realmente cancelar e sair?"
            )
            if resposta:
                self.baixador.cancelar_download()
                self.janela.destroy()
        else:
            self.janela.destroy()


def main():
    """Função de entrada da aplicação."""
    janela = ThemedTk(theme="clam")
    app = InterfaceYouTube(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()