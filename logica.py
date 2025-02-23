# logica.py
from yt_dlp import YoutubeDL
import shutil
import os

class BaixadorYouTube:
    def __init__(self, atualizar_interface_callback):
        self.atualizar_interface_callback = atualizar_interface_callback
        self.ffmpeg_path = self.encontrar_ffmpeg()

    def encontrar_ffmpeg(self):
        """Verifica se o FFmpeg está disponível e retorna seu caminho."""
        caminho = shutil.which("ffmpeg")
        if caminho:
            return caminho
        return None

    def verificar_ffmpeg(self):
        """Retorna erro se o FFmpeg não for encontrado."""
        if not self.ffmpeg_path:
            return "Erro: FFmpeg não encontrado. Certifique-se de que está instalado e no PATH."
        return None

    def atualizar_progresso(self, d):
        if d['status'] == 'downloading':
            percentual = d.get('_percent_str', 'N/A')
            velocidade = d.get('_speed_str', 'N/A')
            tamanho = d.get('_total_bytes_str', 'N/A')
            self.atualizar_interface_callback(percentual, velocidade, tamanho)

    def baixar_video(self, url, local_salvar, qualidade):
        try:
            erro_ffmpeg = self.verificar_ffmpeg()
            if erro_ffmpeg:
                return erro_ffmpeg

            if qualidade == "somente áudio":
                formato = "bestaudio"
                extensao = "mp3"
            else:
                formato = f"{qualidade}+bestaudio/best"
                extensao = "mp4"

            ydl_opts = {
                'format': formato,
                'outtmpl': os.path.join(local_salvar, '%(title)s.' + extensao),
                'noplaylist': True,
                'progress_hooks': [self.atualizar_progresso],
                'merge_output_format': extensao,
                'ffmpeg_location': self.ffmpeg_path,  # Referência explícita ao FFmpeg
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }] if qualidade == "somente áudio" else []
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self.atualizar_interface_callback("100%", "0 MB/s", "Concluído")
                return f"{('Áudio' if qualidade == 'somente áudio' else 'Vídeo')} '{info['title']}' baixado com sucesso!"
        except Exception as e:
            return f"Erro: {str(e)}"
