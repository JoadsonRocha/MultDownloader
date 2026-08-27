"""
Módulo de Interface Gráfica Moderna (MultDownloader)
===================================================
Interface visual moderna inspirada nas diretrizes de design do Bootstrap 5 Dark,
desenvolvida com CustomTkinter para proporcionar uma experiência de usuário (UX)
fluida, responsiva e com componentes visuais elegantes.

Autor: Joadson Rocha / MultDownloader Team
Licença: MIT
"""

import os
import sys
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Dict, Any

import customtkinter as ctk
from PIL import Image, ImageTk
from logica import BaixadorYouTube

# Configuração global de tema CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class InterfaceYouTube(ctk.CTk):
    """Janela principal da aplicação MultDownloader com estética Bootstrap 5 Dark."""

    # Paleta de cores Bootstrap 5 Dark
    BS_BG_ROOT = "#0F1216"        # Fundo da janela (Dark Canvas)
    BS_BG_CARD = "#181C22"        # Superfície dos cards (Card Surface)
    BS_BG_CARD_ALT = "#13161B"    # Superfície do card de prévia
    BS_BG_INPUT = "#21262D"       # Fundo dos inputs (Form Control)
    BS_BORDER_CARD = "#2E3440"    # Borda sutil de cards
    BS_BORDER_INPUT = "#3B4252"   # Borda de inputs
    BS_TEXT_WHITE = "#F8F9FA"     # Texto principal
    BS_TEXT_MUTED = "#9DA5B4"     # Texto secundário/muted
    
    # Cores de Ação do Bootstrap
    BS_PRIMARY = "#0D6EFD"        # Azul Bootstrap (btn-primary)
    BS_PRIMARY_HOVER = "#0B5ED7"
    BS_SECONDARY = "#343A40"      # Cinza escuro (btn-secondary)
    BS_SECONDARY_HOVER = "#495057"
    BS_SUCCESS = "#198754"        # Verde (badge-success)
    BS_DANGER = "#DC3545"         # Vermelho (btn-danger)
    BS_DANGER_HOVER = "#BB2D3B"
    BS_INFO = "#0DCAF0"           # Ciano (info)

    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("MultDownloader - Baixador Universal de Mídias")
        self.geometry("880x560")
        self.minsize(840, 520)
        self.configure(fg_color=self.BS_BG_ROOT)

        # Fila thread-safe de eventos de interface
        self.fila_gui: queue.Queue = queue.Queue()

        # Mecanismo de download
        self.baixador = BaixadorYouTube(callback_progresso=self._enfileirar_progresso)
        self.download_em_andamento = False
        self.thread_ativa: Optional[threading.Thread] = None

        # Pasta de download padrão (Downloads do usuário)
        self.pasta_padrao = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(self.pasta_padrao):
            self.pasta_padrao = os.getcwd()

        self._configurar_icone()
        self._centralizar_janela()
        self._criar_interface_bootstrap()
        self._iniciar_escuta_fila()

        # Intercepta evento de fechamento
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar_janela)

    def _configurar_icone(self):
        """Define o ícone oficial da janela com tratamento multiplataforma."""
        try:
            caminho_icone = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            if os.path.exists(caminho_icone):
                if sys.platform.startswith('win'):
                    self.iconbitmap(caminho_icone)
                else:
                    img = Image.open(caminho_icone)
                    self.iconphoto(True, ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"[Aviso] Ícone não carregado: {e}")

    def _centralizar_janela(self):
        """Centraliza a janela na tela do usuário."""
        self.update_idletasks()
        largura = 880
        altura = 560
        x = max(0, (self.winfo_screenwidth() // 2) - (largura // 2))
        y = max(0, (self.winfo_screenheight() // 2) - (altura // 2))
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _criar_interface_bootstrap(self):
        """Constrói a interface baseada em cards e componentes do Bootstrap 5."""
        
        # Conteiner Principal (Container fluid com padding)
        self.container_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.container_principal.pack(fill="both", expand=True, padx=20, pady=16)

        # ==========================================
        # 1. HEADER / NAVBAR (Logo, Título e Badge)
        # ==========================================
        frame_header = ctk.CTkFrame(self.container_principal, fg_color="transparent")
        frame_header.pack(fill="x", pady=(0, 12))

        # Título com Ícone
        frame_titulo = ctk.CTkFrame(frame_header, fg_color="transparent")
        frame_titulo.pack(side="left")

        lbl_logo = ctk.CTkLabel(
            frame_titulo,
            text="⚡ MultDownloader",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=self.BS_TEXT_WHITE
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            frame_titulo,
            text="Baixe vídeos e áudios de YouTube, Instagram, TikTok, Facebook e mais.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.BS_TEXT_MUTED
        )
        lbl_sub.pack(anchor="w")

        # Badge Pill do FFmpeg (Status)
        disponivel_ffmpeg, _ = self.baixador.verificar_ffmpeg()
        texto_badge = "✓ FFmpeg Ativo" if disponivel_ffmpeg else "⚠ FFmpeg Ausente"
        cor_badge = self.BS_SUCCESS if disponivel_ffmpeg else self.BS_DANGER

        self.badge_ffmpeg = ctk.CTkLabel(
            frame_header,
            text=texto_badge,
            fg_color=cor_badge,
            text_color="white",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=12,
            padx=12,
            pady=4
        )
        self.badge_ffmpeg.pack(side="right", pady=4)

        # ==========================================
        # 2. CARD DE ENTRADA DE URL (Input Group)
        # ==========================================
        card_url = ctk.CTkFrame(
            self.container_principal,
            fg_color=self.BS_BG_CARD,
            border_color=self.BS_BORDER_CARD,
            border_width=1,
            corner_radius=10
        )
        card_url.pack(fill="x", pady=(0, 12), padx=0)

        inner_url = ctk.CTkFrame(card_url, fg_color="transparent")
        inner_url.pack(fill="x", padx=14, pady=12)

        lbl_url = ctk.CTkLabel(
            inner_url,
            text="URL da Mídia (Vídeo / Áudio):",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.BS_TEXT_WHITE
        )
        lbl_url.pack(anchor="w", pady=(0, 6))

        # Input Row (Entry + Colar + Limpar)
        frame_input_row = ctk.CTkFrame(inner_url, fg_color="transparent")
        frame_input_row.pack(fill="x")

        self.var_url = tk.StringVar()
        self.entry_url = ctk.CTkEntry(
            frame_input_row,
            textvariable=self.var_url,
            placeholder_text="Cole o link aqui (ex: https://www.youtube.com/watch?v=...)",
            placeholder_text_color=self.BS_TEXT_MUTED,
            fg_color=self.BS_BG_INPUT,
            border_color=self.BS_BORDER_INPUT,
            border_width=1,
            text_color=self.BS_TEXT_WHITE,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            corner_radius=8,
            height=38
        )
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._criar_menu_contexto(self.entry_url)

        # Botão Colar (btn-primary outline ou sólido)
        self.btn_colar = ctk.CTkButton(
            frame_input_row,
            text="📋 Colar",
            command=self._acao_colar_url,
            fg_color=self.BS_PRIMARY,
            hover_color=self.BS_PRIMARY_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            corner_radius=8,
            height=38,
            width=90
        )
        self.btn_colar.pack(side="left", padx=(0, 6))

        # Botão Limpar (btn-secondary)
        self.btn_limpar = ctk.CTkButton(
            frame_input_row,
            text="✕",
            command=self._acao_limpar_url,
            fg_color=self.BS_SECONDARY,
            hover_color=self.BS_SECONDARY_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            corner_radius=8,
            height=38,
            width=40
        )
        self.btn_limpar.pack(side="left")

        # ==========================================
        # 3. CARD DE PRÉVIA DA MÍDIA (Media Box)
        # ==========================================
        self.card_preview = ctk.CTkFrame(
            self.container_principal,
            fg_color=self.BS_BG_CARD_ALT,
            border_color=self.BS_BORDER_CARD,
            border_width=1,
            corner_radius=8
        )
        self.card_preview.pack(fill="x", pady=(0, 12))

        inner_preview = ctk.CTkFrame(self.card_preview, fg_color="transparent")
        inner_preview.pack(fill="x", padx=14, pady=10)

        # Título da Mídia
        self.lbl_prev_titulo = ctk.CTkLabel(
            inner_preview,
            text="Cole um link acima para identificar a mídia...",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.BS_TEXT_WHITE,
            anchor="w",
            wraplength=800
        )
        self.lbl_prev_titulo.pack(fill="x", anchor="w")

        # Badges de Informações (Canal, Duração, Origem)
        self.frame_badges_info = ctk.CTkFrame(inner_preview, fg_color="transparent")
        self.frame_badges_info.pack(fill="x", anchor="w", pady=(6, 0))

        self.lbl_info_detalhes = ctk.CTkLabel(
            self.frame_badges_info,
            text="Suporta: YouTube, Instagram, Facebook, TikTok, Twitter/X, SoundCloud e mais.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.BS_TEXT_MUTED,
            anchor="w"
        )
        self.lbl_info_detalhes.pack(side="left")

        # ==========================================
        # 4. CARD DE CONFIGURAÇÕES (Form Controls)
        # ==========================================
        card_opcoes = ctk.CTkFrame(
            self.container_principal,
            fg_color=self.BS_BG_CARD,
            border_color=self.BS_BORDER_CARD,
            border_width=1,
            corner_radius=10
        )
        card_opcoes.pack(fill="x", pady=(0, 12))

        inner_opcoes = ctk.CTkFrame(card_opcoes, fg_color="transparent")
        inner_opcoes.pack(fill="x", padx=14, pady=12)

        # Grid com 2 Colunas: Qualidade e Destino
        inner_opcoes.columnconfigure(0, weight=1)
        inner_opcoes.columnconfigure(1, weight=2)

        # Coluna 1: Qualidade / Resolução
        frame_col_qualidade = ctk.CTkFrame(inner_opcoes, fg_color="transparent")
        frame_col_qualidade.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        lbl_qualidade = ctk.CTkLabel(
            frame_col_qualidade,
            text="Formato / Resolução:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.BS_TEXT_WHITE
        )
        lbl_qualidade.pack(anchor="w", pady=(0, 4))

        self.opcoes_qualidade = [
            "Melhor Qualidade (Auto)",
            "1080p Full HD",
            "720p HD",
            "480p SD",
            "360p",
            "Áudio MP3 (320 kbps)",
            "Áudio MP3 (192 kbps)",
            "Áudio M4A / AAC"
        ]
        self.var_qualidade = tk.StringVar(value=self.opcoes_qualidade[0])
        self.combo_qualidade = ctk.CTkOptionMenu(
            frame_col_qualidade,
            variable=self.var_qualidade,
            values=self.opcoes_qualidade,
            fg_color=self.BS_BG_INPUT,
            button_color=self.BS_SECONDARY,
            button_hover_color=self.BS_SECONDARY_HOVER,
            dropdown_fg_color=self.BS_BG_CARD,
            dropdown_hover_color=self.BS_PRIMARY,
            text_color=self.BS_TEXT_WHITE,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            corner_radius=8,
            height=36
        )
        self.combo_qualidade.pack(fill="x")

        # Coluna 2: Pasta de Destino
        frame_col_pasta = ctk.CTkFrame(inner_opcoes, fg_color="transparent")
        frame_col_pasta.grid(row=0, column=1, sticky="ew")

        lbl_pasta = ctk.CTkLabel(
            frame_col_pasta,
            text="Pasta de Destino:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.BS_TEXT_WHITE
        )
        lbl_pasta.pack(anchor="w", pady=(0, 4))

        frame_pasta_inputs = ctk.CTkFrame(frame_col_pasta, fg_color="transparent")
        frame_pasta_inputs.pack(fill="x")

        self.var_pasta = tk.StringVar(value=self.pasta_padrao)
        self.entry_pasta = ctk.CTkEntry(
            frame_pasta_inputs,
            textvariable=self.var_pasta,
            fg_color=self.BS_BG_INPUT,
            border_color=self.BS_BORDER_INPUT,
            border_width=1,
            text_color=self.BS_TEXT_WHITE,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=8,
            height=36
        )
        self.entry_pasta.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_procurar = ctk.CTkButton(
            frame_pasta_inputs,
            text="📁 Procurar",
            command=self._acao_selecionar_pasta,
            fg_color=self.BS_SECONDARY,
            hover_color=self.BS_SECONDARY_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8,
            height=36,
            width=85
        )
        self.btn_procurar.pack(side="left", padx=(0, 4))

        self.btn_abrir_pasta = ctk.CTkButton(
            frame_pasta_inputs,
            text="📂 Abrir",
            command=self._acao_abrir_pasta,
            fg_color=self.BS_SECONDARY,
            hover_color=self.BS_SECONDARY_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=8,
            height=36,
            width=75
        )
        self.btn_abrir_pasta.pack(side="left")

        # ==========================================
        # 5. CARD DE PROGRESSO & TELEMETRIA
        # ==========================================
        card_progresso = ctk.CTkFrame(
            self.container_principal,
            fg_color=self.BS_BG_CARD,
            border_color=self.BS_BORDER_CARD,
            border_width=1,
            corner_radius=10
        )
        card_progresso.pack(fill="x", pady=(0, 14))

        inner_progresso = ctk.CTkFrame(card_progresso, fg_color="transparent")
        inner_progresso.pack(fill="x", padx=14, pady=12)

        # Barra de Progresso Estilo Bootstrap
        self.barra_progresso = ctk.CTkProgressBar(
            inner_progresso,
            orientation="horizontal",
            mode="determinate",
            progress_color=self.BS_PRIMARY,
            fg_color="#2B303C",
            height=14,
            corner_radius=7
        )
        self.barra_progresso.pack(fill="x", pady=(0, 8))
        self.barra_progresso.set(0.0)

        # Telemetria em Grid / Pills
        frame_telemetria = ctk.CTkFrame(inner_progresso, fg_color="transparent")
        frame_telemetria.pack(fill="x")

        # Status
        self.lbl_status = ctk.CTkLabel(
            frame_telemetria,
            text="● Pronto para iniciar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.BS_TEXT_WHITE
        )
        self.lbl_status.pack(side="left")

        # ETA (à direita)
        self.lbl_eta = ctk.CTkLabel(
            frame_telemetria,
            text="⏳ Restante: --:--",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.BS_TEXT_MUTED
        )
        self.lbl_eta.pack(side="right")

        # Tamanho (centro-direita)
        self.lbl_tamanho = ctk.CTkLabel(
            frame_telemetria,
            text="📦 Tamanho: --",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.BS_TEXT_MUTED
        )
        self.lbl_tamanho.pack(side="right", padx=(0, 16))

        # Velocidade (centro-esquerda)
        self.lbl_velocidade = ctk.CTkLabel(
            frame_telemetria,
            text="⚡ Velocidade: --",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.BS_TEXT_MUTED
        )
        self.lbl_velocidade.pack(side="right", padx=(0, 16))

        # ==========================================
        # 6. FOOTER / BOTÕES DE AÇÃO PRINCIPAL
        # ==========================================
        frame_acoes = ctk.CTkFrame(self.container_principal, fg_color="transparent")
        frame_acoes.pack(fill="x")

        self.btn_download = ctk.CTkButton(
            frame_acoes,
            text="⬇  Iniciar Download",
            command=self._acao_iniciar_download,
            fg_color=self.BS_PRIMARY,
            hover_color=self.BS_PRIMARY_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=8,
            height=44
        )
        self.btn_download.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_cancelar = ctk.CTkButton(
            frame_acoes,
            text="⏹ Cancelar",
            command=self._acao_cancelar_download,
            fg_color=self.BS_DANGER,
            hover_color=self.BS_DANGER_HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=8,
            height=44,
            width=130,
            state="disabled"
        )
        self.btn_cancelar.pack(side="right")

    def _criar_menu_contexto(self, widget):
        """Adiciona menu de contexto com botão direito do mouse."""
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=self.BS_BG_INPUT,
            fg=self.BS_TEXT_WHITE,
            activebackground=self.BS_PRIMARY,
            activeforeground="white",
            borderwidth=1
        )
        menu.add_command(label="Colar", command=self._acao_colar_url)
        menu.add_command(label="Copiar", command=lambda: widget.event_generate('<<Copy>>'))
        menu.add_command(label="Recortar", command=lambda: widget.event_generate('<<Cut>>'))
        menu.add_separator()
        menu.add_command(label="Limpar", command=self._acao_limpar_url)

        def exibir_popup(event):
            menu.tk_popup(event.x_root, event.y_root)

        widget.bind("<Button-3>", exibir_popup)

    def _acao_colar_url(self):
        """Cola conteúdo da área de transferência e busca informações automaticamente."""
        try:
            conteudo = self.clipboard_get().strip()
            if conteudo:
                self.var_url.set(conteudo)
                self._buscar_metadados_assincrono(conteudo)
        except Exception:
            pass

    def _acao_limpar_url(self):
        """Limpa o campo de URL e reseta o card de prévia."""
        self.var_url.set("")
        self.lbl_prev_titulo.configure(text="Cole um link acima para identificar a mídia...")
        self.lbl_info_detalhes.configure(text="Suporta: YouTube, Instagram, Facebook, TikTok, Twitter/X, SoundCloud e mais.")

    def _buscar_metadados_assincrono(self, url: str):
        """Dispara busca assíncrona de informações do vídeo sem travar a interface."""
        valido, _ = BaixadorYouTube.validar_url(url)
        if not valido:
            return

        self.lbl_prev_titulo.configure(text="⏳ Identificando mídia e obtendo dados...")
        self.lbl_info_detalhes.configure(text="Aguarde um instante...")

        def tarefa():
            info = self.baixador.obter_info_video(url)
            self.fila_gui.put(('metadata', info))

        threading.Thread(target=tarefa, daemon=True).start()

    def _acao_selecionar_pasta(self):
        """Abre diálogo para seleção de pasta de destino."""
        pasta = filedialog.askdirectory(initialdir=self.var_pasta.get())
        if pasta:
            self.var_pasta.set(pasta)

    def _acao_abrir_pasta(self):
        """Abre a pasta de destino no Windows Explorer ou gerenciador padrão."""
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
        """Callback seguro para repassar dados da thread de download para a interface."""
        self.fila_gui.put(('progress', dados))

    def _iniciar_escuta_fila(self):
        """Consome eventos da fila de interface de forma contínua e não-bloqueante."""
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
            self.after(50, self._iniciar_escuta_fila)

    def _atualizar_ui_progresso(self, d: Dict[str, Any]):
        """Atualiza a barra de progresso e as métricas de telemetria."""
        status = d.get('status')
        percent_float = d.get('percent', 0.0)

        # CustomTkinter espera valores de 0.0 a 1.0
        self.barra_progresso.set(percent_float / 100.0)

        if status == 'downloading':
            self.lbl_status.configure(text=f"⬇ Baixando... {d.get('percent_str', '')}", text_color=self.BS_PRIMARY)
            self.lbl_velocidade.configure(text=f"⚡ Velocidade: {d.get('speed_str', '--')}")
            self.lbl_tamanho.configure(text=f"📦 Tamanho: {d.get('size_str', '--')}")
            self.lbl_eta.configure(text=f"⏳ Restante: {d.get('eta_str', '--')}")
        elif status == 'finished' or status == 'completed':
            self.lbl_status.configure(text="✓ Processamento Concluído!", text_color=self.BS_SUCCESS)
            self.lbl_velocidade.configure(text="⚡ Velocidade: Concluído")
            self.lbl_eta.configure(text="⏳ Restante: 00:00")

    def _atualizar_ui_metadata(self, info: Dict[str, Any]):
        """Atualiza o card de prévia com os metadados do vídeo identificado."""
        if 'erro' in info:
            self.lbl_prev_titulo.configure(text="Link detectado (Prévia indisponível)")
            self.lbl_info_detalhes.configure(text=f"Aviso: {info['erro']}")
        else:
            titulo = info.get('title', 'Vídeo sem título')
            autor = info.get('uploader', 'Desconhecido')
            duracao = info.get('duration_str', 'N/A')
            origem = info.get('extractor', 'Web')
            self.lbl_prev_titulo.configure(text=f"🎬 {titulo}")
            self.lbl_info_detalhes.configure(
                text=f"👤 Canal: {autor}   •   ⏱️ Duração: {duracao}   •   🌐 Plataforma: {origem}"
            )

    def _acao_iniciar_download(self):
        """Inicia o fluxo de download assíncrono."""
        url = self.var_url.get().strip()
        pasta = self.var_pasta.get().strip()
        qualidade = self.var_qualidade.get()

        valido, msg_url = BaixadorYouTube.validar_url(url)
        if not valido:
            messagebox.showerror("URL Inválida", msg_url)
            return

        if not pasta:
            messagebox.showerror("Erro de Destino", "Selecione uma pasta de destino válida.")
            return

        # Atualiza o estado da interface
        self.download_em_andamento = True
        self.btn_download.configure(state="disabled")
        self.btn_cancelar.configure(state="normal")
        self.barra_progresso.set(0.0)
        self.lbl_status.configure(text="● Conectando e baixando mídia...", text_color=self.BS_PRIMARY)
        self.lbl_velocidade.configure(text="⚡ Velocidade: Calculando...")
        self.lbl_tamanho.configure(text="📦 Tamanho: Conectando...")
        self.lbl_eta.configure(text="⏳ Restante: --:--")

        def worker():
            sucesso, resultado = self.baixador.baixar_video(url, pasta, qualidade)
            self.fila_gui.put(('completed', (sucesso, resultado)))

        self.thread_ativa = threading.Thread(target=worker, daemon=True)
        self.thread_ativa.start()

    def _acao_cancelar_download(self):
        """Solicita o cancelamento seguro do download."""
        if self.download_em_andamento:
            self.lbl_status.configure(text="⚠ Cancelando download...", text_color=self.BS_DANGER)
            self.baixador.cancelar_download()
            self.btn_cancelar.configure(state="disabled")

    def _finalizar_download(self, sucesso: bool, mensagem: str):
        """Restaura os botões da interface e exibe aviso de resultado."""
        self.download_em_andamento = False
        self.btn_download.configure(state="normal")
        self.btn_cancelar.configure(state="disabled")

        if sucesso:
            self.lbl_status.configure(text="✓ Download concluído com sucesso!", text_color=self.BS_SUCCESS)
            messagebox.showinfo("Download Concluído", mensagem)
        else:
            if "cancelado" in mensagem.lower():
                self.lbl_status.configure(text="⚠ Download cancelado pelo usuário.", text_color=self.BS_DANGER)
                messagebox.showwarning("Cancelado", mensagem)
            else:
                self.lbl_status.configure(text="✕ Falha no download.", text_color=self.BS_DANGER)
                messagebox.showerror("Erro no Download", mensagem)

    def _ao_fechar_janela(self):
        """Gerencia o fechamento seguro enquanto houver downloads em execução."""
        if self.download_em_andamento:
            resposta = messagebox.askyesno(
                "Download em Execução",
                "Existe um download em andamento. Deseja cancelar e fechar a aplicação?"
            )
            if resposta:
                self.baixador.cancelar_download()
                self.destroy()
        else:
            self.destroy()


def main():
    """Inicializa a interface moderna CustomTkinter."""
    app = InterfaceYouTube()
    app.mainloop()


if __name__ == "__main__":
    main()