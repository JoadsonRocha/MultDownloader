"""
Módulo de Lógica e Mecanismo de Download (MultDownloader)
=========================================================
Responsável pelo gerenciamento de downloads, extração de metadados,
validação de URLs, detecção de dependências (FFmpeg) e controle de fluxo.

Autor: Joadson Rocha / MultDownloader Team
Licença: MIT
"""

import os
import sys
import shutil
import glob
import re
import time
import urllib.parse
from typing import Callable, Optional, Dict, Any, Tuple
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError


class DownloadCancelledException(Exception):
    """Exceção levantada quando o usuário solicita o cancelamento do download."""
    pass


class BaixadorYouTube:
    """
    Controlador central para downloads de mídias de múltiplas plataformas
    (YouTube, Instagram, Facebook, TikTok, Twitter/X, etc.) utilizando yt-dlp.
    """

    def __init__(self, callback_progresso: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        Inicializa a instância do baixador.

        :param callback_progresso: Função de retorno para emitir atualizações de progresso
                                   com dados estruturados (percentual, velocidade, tamanho, ETA).
        """
        self.callback_progresso = callback_progresso
        self.cancelar_solicitado = False
        self._ultimo_envio_tempo = 0.0
        self.ffmpeg_path = self.detectar_ffmpeg()

    @staticmethod
    def detectar_ffmpeg() -> Optional[str]:
        """
        Detecta a localização do executável FFmpeg no sistema ou em pastas locais do projeto.

        Ordem de busca:
        1. Variável de ambiente PATH do sistema (`shutil.which`).
        2. Subdiretório local `ffmpeg/bin/ffmpeg.exe` ou `ffmpeg/ffmpeg.exe`.
        3. Diretórios comuns do Windows (C:\\ffmpeg, WinGet, Chocolatey).

        :return: Caminho do executável FFmpeg ou None se não encontrado.
        """
        # 1. Busca no PATH do sistema
        caminho_sistema = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if caminho_sistema:
            return caminho_sistema

        # 2. Busca na pasta relativa ao executável / script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidatos_locais = [
            os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(base_dir, "ffmpeg", "bin", "ffmpeg"),
            os.path.join(base_dir, "ffmpeg", "ffmpeg.exe"),
            os.path.join(base_dir, "ffmpeg", "ffmpeg"),
            os.path.join(base_dir, "bin", "ffmpeg.exe"),
            os.path.join(base_dir, "bin", "ffmpeg"),
            os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(os.getcwd(), "ffmpeg", "ffmpeg.exe"),
        ]

        for cand in candidatos_locais:
            if os.path.isfile(cand) and os.access(cand, os.X_OK if hasattr(os, 'X_OK') else os.F_OK):
                return cand

        # 3. Busca em diretórios típicos do Windows
        candidatos_windows = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        ]
        for cand in candidatos_windows:
            if os.path.isfile(cand):
                return cand

        # 4. Busca em pacotes WinGet no AppData do usuário
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            padrao_winget = os.path.join(
                local_app_data, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "**", "ffmpeg.exe"
            )
            encontrados = glob.glob(padrao_winget, recursive=True)
            if encontrados:
                return encontrados[0]

        return None

    def verificar_ffmpeg(self) -> Tuple[bool, str]:
        """
        Verifica se o FFmpeg está disponível.

        :return: Tupla (disponível: bool, mensagem: str)
        """
        self.ffmpeg_path = self.detectar_ffmpeg()
        if not self.ffmpeg_path:
            return False, (
                "FFmpeg não foi detectado no sistema nem na pasta local.\n"
                "Downloads de alta resolução (1080p+) e extração de áudio necessitam do FFmpeg.\n\n"
                "Para instalar no Windows:\n"
                "Execute no terminal: winget install Gyan.FFmpeg\n"
                "Ou baixe em https://ffmpeg.org e adicione ao PATH."
            )
        return True, self.ffmpeg_path

    @staticmethod
    def validar_url(url: str) -> Tuple[bool, str]:
        """
        Valida a URL fornecida pelo usuário, garantindo formato seguro e protocolos permitidos.

        :param url: URL a ser verificada.
        :return: Tupla (valido: bool, mensagem_ou_url_limpa: str)
        """
        if not url or not isinstance(url, str):
            return False, "A URL não pode estar vazia."

        url = url.strip()
        parsed = urllib.parse.urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, "A URL deve começar com 'http://' ou 'https://'."

        if not parsed.netloc:
            return False, "Formato de URL inválido. Domínio não encontrado."

        # Rejeita esquemas locais ou maliciosos
        if parsed.scheme in ("file", "ftp", "gopher", "data", "javascript"):
            return False, f"Protocolo inseguro '{parsed.scheme}' não é permitido."

        return True, url

    @staticmethod
    def formatar_tamanho(bytes_total: Optional[int]) -> str:
        """Formata quantidade de bytes em formato legível (KB, MB, GB)."""
        if not bytes_total or bytes_total <= 0:
            return "N/A"
        for unidade in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_total < 1024.0:
                return f"{bytes_total:.1f} {unidade}"
            bytes_total /= 1024.0
        return f"{bytes_total:.1f} PB"

    @staticmethod
    def formatar_tempo(segundos: Optional[int]) -> str:
        """Formata segundos para o formato MM:SS ou HH:MM:SS."""
        if segundos is None or segundos < 0:
            return "--:--"
        segundos = int(segundos)
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segs = segundos % 60
        if horas > 0:
            return f"{horas:02d}:{minutos:02d}:{segs:02d}"
        return f"{minutos:02d}:{segs:02d}"

    def cancelar_download(self):
        """Sinaliza pedido de cancelamento do download ativo."""
        self.cancelar_solicitado = True

    def _progresso_hook(self, d: Dict[str, Any]):
        """
        Hook de progresso executado internamente pelo yt-dlp.
        Calcula percentual numérico, velocidade e tempo estimado com throttling.
        """
        if self.cancelar_solicitado:
            raise DownloadCancelledException("Download cancelado pelo usuário.")

        if not self.callback_progresso:
            return

        agora = time.time()
        status = d.get('status', '')

        # Throttling: emite progresso a cada 100ms no máximo durante o download
        if status == 'downloading':
            if agora - self._ultimo_envio_tempo < 0.10:
                return
            self._ultimo_envio_tempo = agora

            baixado = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            velocidade_bytes = d.get('speed') or 0
            eta_segundos = d.get('eta')

            if total > 0:
                percentual_float = min(100.0, (baixado / total) * 100.0)
                percentual_str = f"{percentual_float:.1f}%"
                tamanho_str = f"{self.formatar_tamanho(baixado)} / {self.formatar_tamanho(total)}"
            else:
                percentual_float = 0.0
                percentual_str = "Baixando..."
                tamanho_str = self.formatar_tamanho(baixado)

            velocidade_str = f"{self.formatar_tamanho(velocidade_bytes)}/s" if velocidade_bytes else "Calculando..."
            eta_str = self.formatar_tempo(eta_segundos) if eta_segundos is not None else "--:--"

            dados = {
                'status': 'downloading',
                'percent': percentual_float,
                'percent_str': percentual_str,
                'speed_str': velocidade_str,
                'size_str': tamanho_str,
                'eta_str': eta_str,
                'filename': os.path.basename(d.get('filename', ''))
            }
            self.callback_progresso(dados)

        elif status == 'finished':
            self._ultimo_envio_tempo = agora
            dados = {
                'status': 'finished',
                'percent': 100.0,
                'percent_str': '100%',
                'speed_str': '0 KB/s',
                'size_str': 'Download concluído',
                'eta_str': '00:00',
                'filename': os.path.basename(d.get('filename', ''))
            }
            self.callback_progresso(dados)

    def obter_info_video(self, url: str) -> Dict[str, Any]:
        """
        Extrai metadados do vídeo sem realizar o download (título, autor, duração, thumbnail).

        :param url: URL da mídia.
        :return: Dicionário com informações ou 'erro'.
        """
        valido, res = self.validar_url(url)
        if not valido:
            return {'erro': res}

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 15,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return {'erro': 'Não foi possível obter dados para este link.'}

                titulo = info.get('title', 'Vídeo sem título')
                autor = info.get('uploader') or info.get('channel') or info.get('creator') or 'Desconhecido'
                duracao = info.get('duration')
                duracao_str = self.formatar_tempo(duracao) if duracao else 'N/A'
                thumbnail = info.get('thumbnail') or ''
                extrator = info.get('extractor_key') or 'Web'

                return {
                    'sucesso': True,
                    'title': titulo,
                    'uploader': autor,
                    'duration_str': duracao_str,
                    'thumbnail': thumbnail,
                    'extractor': extrator,
                    'id': info.get('id', '')
                }
        except DownloadError as e:
            msg = str(e)
            if "Video unavailable" in msg:
                return {'erro': 'Vídeo indisponível ou excluído.'}
            if "Private video" in msg:
                return {'erro': 'Este vídeo é privado.'}
            return {'erro': f'Erro ao obter metadados: {msg.split(";")[-1].strip()}'}
        except Exception as e:
            return {'erro': f'Falha ao processar link: {str(e)}'}

    def baixar_video(self, url: str, local_salvar: str, opcao_qualidade: str) -> Tuple[bool, str]:
        """
        Executa o download da mídia para o diretório especificado na qualidade selecionada.

        :param url: URL do vídeo/mídia.
        :param local_salvar: Diretório de destino no disco.
        :param opcao_qualidade: Rótulo da qualidade selecionada na interface.
        :return: Tupla (sucesso: bool, mensagem_resultado: str)
        """
        self.cancelar_solicitado = False
        self._ultimo_envio_tempo = 0.0

        # 1. Validação da URL
        valido, res_url = self.validar_url(url)
        if not valido:
            return False, f"URL inválida: {res_url}"

        # 2. Validação e criação do diretório de destino
        if not local_salvar or not os.path.exists(local_salvar):
            try:
                local_salvar = local_salvar or os.path.join(os.path.expanduser("~"), "Downloads")
                os.makedirs(local_salvar, exist_ok=True)
            except Exception as e:
                return False, f"Diretório de destino inválido ou sem permissão de escrita: {e}"

        # 3. Detecção e verificação do FFmpeg
        self.ffmpeg_path = self.detectar_ffmpeg()
        is_audio = "Áudio" in opcao_qualidade or "somente áudio" in opcao_qualidade.lower()

        # Mapeamento de formatos otimizados para evitar re-encoding lento
        mapa_formatos = {
            "Melhor Qualidade (Auto)": (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                "mp4"
            ),
            "1080p Full HD": (
                "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                "mp4"
            ),
            "720p HD": (
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "mp4"
            ),
            "480p SD": (
                "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
                "mp4"
            ),
            "360p": (
                "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best",
                "mp4"
            ),
            "Áudio MP3 (192 kbps)": ("bestaudio/best", "mp3"),
            "Áudio MP3 (320 kbps)": ("bestaudio/best", "mp3"),
            "Áudio M4A / AAC": ("bestaudio[ext=m4a]/bestaudio/best", "m4a"),
        }

        formato, extensao_padrao = mapa_formatos.get(opcao_qualidade, ("best", "mp4"))

        # Configurações de pós-processamento de áudio se solicitado
        postprocessors = []
        if is_audio:
            if "M4A" in opcao_qualidade:
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '192',
                })
            else:
                qualidade_kbps = '320' if '320' in opcao_qualidade else '192'
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': qualidade_kbps,
                })

        # Template de saída seguro (sanitiza caracteres inválidos no Windows)
        outtmpl_path = os.path.join(local_salvar, '%(title).200B [%(id)s].%(ext)s')

        ydl_opts = {
            'format': formato,
            'outtmpl': outtmpl_path,
            'noplaylist': True,
            'progress_hooks': [self._progresso_hook],
            'windowsfilenames': True,
            'socket_timeout': 20,
            'retries': 10,
            'fragment_retries': 10,
            'quiet': True,
            'no_warnings': True,
        }

        if self.ffmpeg_path:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path
            if not is_audio:
                ydl_opts['merge_output_format'] = 'mp4'

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                titulo = info.get('title', 'Mídia') if info else 'Mídia'

                if self.callback_progresso:
                    self.callback_progresso({
                        'status': 'completed',
                        'percent': 100.0,
                        'percent_str': '100%',
                        'speed_str': 'Concluído',
                        'size_str': 'Salvo com sucesso',
                        'eta_str': '00:00',
                        'filename': titulo
                    })

                tipo_str = "Áudio" if is_audio else "Vídeo"
                return True, f"{tipo_str} '{titulo}' baixado com sucesso em:\n{local_salvar}"

        except DownloadCancelledException:
            return False, "Download cancelado pelo usuário."
        except DownloadError as e:
            msg_erro = str(e)
            if "FFmpeg" in msg_erro or "ffmpeg" in msg_erro:
                return False, (
                    "Erro relacionado ao FFmpeg: O FFmpeg é necessário para mesclar vídeo/áudio ou converter formatos.\n"
                    "Instale o FFmpeg ou escolha outra qualidade."
                )
            if "HTTP Error 403" in msg_erro or "Private video" in msg_erro:
                return False, "Erro 403: Acesso negado. O vídeo pode ser privado ou ter restrições regionais."
            if "Video unavailable" in msg_erro:
                return False, "O vídeo requisitado está indisponível ou foi removido."
            return False, f"Falha no download: {msg_erro.split('ERROR:')[-1].strip()}"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"