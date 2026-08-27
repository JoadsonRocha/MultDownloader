"""
Testes Unitários Automatizados e Robustos para o MultDownloader
===============================================================
Cobre validações de segurança de URL, sanitização de diretórios,
formatação de grandezas, detecção de FFmpeg e comportamento de cancelamento.
"""
import unittest
import os
import sys
import tempfile
from logica import BaixadorYouTube, DownloadCancelledException


class TestMultDownloaderLogica(unittest.TestCase):

    def setUp(self):
        self.baixador = BaixadorYouTube()

    def test_validar_url_sucesso(self):
        urls_validas = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://www.instagram.com/reel/C123456789/",
            "https://www.tiktok.com/@user/video/123456789",
            "https://facebook.com/watch/?v=123456789",
            "https://x.com/user/status/123456789",
            "https://soundcloud.com/artist/track",
            "https://vimeo.com/123456789"
        ]
        for url in urls_validas:
            valido, res = self.baixador.validar_url(url)
            self.assertTrue(valido, f"Deveria ser válida: {url}")
            self.assertEqual(res, url.strip())

    def test_validar_url_insegura_e_invalida(self):
        urls_invalidas = [
            "",
            None,
            "   ",
            "file:///etc/passwd",
            "file:///C:/Windows/System32/calc.exe",
            "ftp://ftp.example.com/video.mp4",
            "javascript:alert(1)",
            "data:text/plain;base64,SGVsbG8=",
            "gopher://gopher.example.com",
            "http://",
            "https://",
            "apenas_texto_sem_protocolo",
            "www.youtube.com/watch?v=123"  # sem http:// ou https://
        ]
        for url in urls_invalidas:
            valido, msg = self.baixador.validar_url(url)
            self.assertFalse(valido, f"Deveria ser inválida ou insegura: {url}")
            self.assertTrue(isinstance(msg, str) and len(msg) > 0)

    def test_formatar_tamanho(self):
        self.assertEqual(self.baixador.formatar_tamanho(None), "N/A")
        self.assertEqual(self.baixador.formatar_tamanho(0), "N/A")
        self.assertEqual(self.baixador.formatar_tamanho(-100), "N/A")
        self.assertEqual(self.baixador.formatar_tamanho(500), "500.0 B")
        self.assertEqual(self.baixador.formatar_tamanho(1024), "1.0 KB")
        self.assertEqual(self.baixador.formatar_tamanho(1536), "1.5 KB")
        self.assertEqual(self.baixador.formatar_tamanho(1048576), "1.0 MB")
        self.assertEqual(self.baixador.formatar_tamanho(1073741824), "1.0 GB")

    def test_formatar_tempo(self):
        self.assertEqual(self.baixador.formatar_tempo(None), "--:--")
        self.assertEqual(self.baixador.formatar_tempo(-5), "--:--")
        self.assertEqual(self.baixador.formatar_tempo(0), "00:00")
        self.assertEqual(self.baixador.formatar_tempo(9), "00:09")
        self.assertEqual(self.baixador.formatar_tempo(65), "01:05")
        self.assertEqual(self.baixador.formatar_tempo(3600), "01:00:00")
        self.assertEqual(self.baixador.formatar_tempo(3665), "01:01:05")

    def test_detectar_ffmpeg(self):
        ffmpeg_res = self.baixador.detectar_ffmpeg()
        self.assertTrue(ffmpeg_res is None or isinstance(ffmpeg_res, str))
        
        status, msg = self.baixador.verificar_ffmpeg()
        self.assertIsInstance(status, bool)
        self.assertIsInstance(msg, str)

    def test_cancelamento_flag(self):
        self.assertFalse(self.baixador.cancelar_solicitado)
        self.baixador.cancelar_download()
        self.assertTrue(self.baixador.cancelar_solicitado)

    def test_obter_info_video_url_invalida(self):
        info = self.baixador.obter_info_video("invalido")
        self.assertIn('erro', info)

    def test_baixar_video_validacao_rejeicao_url(self):
        sucesso, msg = self.baixador.baixar_video("invalido", "", "Padrão")
        self.assertFalse(sucesso)
        self.assertIn("URL inválida", msg)

    def test_baixar_video_diretorio_invalido_auto_cria(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            novo_subdiretorio = os.path.join(tmpdir, "novo_downloads_pasta")
            # Chama com URL inválida propositalmente, mas verifica se a criação do diretório passa
            sucesso, msg = self.baixador.baixar_video("https://invalido.exemplo123.com/fake", novo_subdiretorio, "Melhor Qualidade (Auto)")
            self.assertTrue(os.path.exists(novo_subdiretorio))


if __name__ == "__main__":
    unittest.main()

