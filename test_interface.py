"""
Teste de Inicialização de Interface Tkinter
"""
import unittest
import tkinter as tk
from ttkthemes import ThemedTk
from interface import InterfaceYouTube

class TestInterfaceInit(unittest.TestCase):
    def test_gui_instantiation(self):
        try:
            janela = ThemedTk(theme="clam")
            app = InterfaceYouTube(janela)
            self.assertIsNotNone(app)
            self.assertEqual(app.var_url.get(), "")
            self.assertTrue(len(app.var_pasta.get()) > 0)
            janela.destroy()
        except tk.TclError as e:
            # Em ambientes headless sem display
            print(f"Skipping GUI display test: {e}")

if __name__ == "__main__":
    unittest.main()

