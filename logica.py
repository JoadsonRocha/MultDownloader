from yt_dlp import YoutubeDL
import shutil

class BaixadorYouTube:
    def __init__(self, atualizar_interface_callback):
        self.atualizar_interface_callback = atualizar_interface_callback

    def verificar_ffmpeg(self):
        if shutil.which("ffmpeg") is None:
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

            # Mapeamento de qualidade para formatos suportados pelo yt-dlp
            qualidade_map = {
                "Padrão": "best",
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                "somente áudio": "bestaudio"
            }

            formato = qualidade_map.get(qualidade, "best")
            extensao = "mp3" if qualidade == "somente áudio" else "mp4"

            ydl_opts = {
                'format': formato,
                'outtmpl': f'{local_salvar}/%(title)s.{extensao}',
                'noplaylist': True,
                'progress_hooks': [self.atualizar_progresso],
                'merge_output_format': extensao,
                'ffmpeg_location': shutil.which("ffmpeg"),
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