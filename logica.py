# logica.py
from yt_dlp import YoutubeDL

class BaixadorYouTube:
    def __init__(self, atualizar_interface_callback):
        """
        Inicializa o baixador de vídeos.
        :param atualizar_interface_callback: Função para atualizar a interface.
        """
        self.atualizar_interface_callback = atualizar_interface_callback

    def atualizar_progresso(self, d):
        """
        Atualiza o progresso do download.
        :param d: Dicionário com informações do progresso.
        """
        if d['status'] == 'downloading':
            percentual = d.get('_percent_str', 'N/A')
            velocidade = d.get('_speed_str', 'N/A')
            tamanho = d.get('_total_bytes_str', 'N/A')
            self.atualizar_interface_callback(percentual, velocidade, tamanho)

    def baixar_video(self, url, local_salvar, qualidade):
        """
        Baixa o vídeo do YouTube.
        :param url: URL do vídeo.
        :param local_salvar: Diretório onde o vídeo será salvo.
        :param qualidade: Qualidade selecionada (ex: 'best', '137', '22', '18').
        :return: Mensagem de sucesso ou erro.
        """
        try:
            ydl_opts = {
                'format': qualidade,  # Usa a qualidade selecionada
                'outtmpl': f'{local_salvar}/%(title)s.%(ext)s',  # Define o local e nome do arquivo
                'noplaylist': True,  # Baixa apenas um vídeo, não uma playlist
                'progress_hooks': [self.atualizar_progresso],  # Atualiza o progresso
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self.atualizar_interface_callback("100%", "0 MB/s", "Concluído")
                return f"Vídeo '{info['title']}' baixado com sucesso!"
        except Exception as e:
            return f"Ocorreu um erro: {e}"