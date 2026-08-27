"""
Teste de Inicialização de Interface Moderna CustomTkinter
"""
import unittest
import tkinter as tk
from interface import InterfaceYouTube


class TestInterfaceInit(unittest.TestCase):
    def test_gui_instantiation(self):
        try:
            app = InterfaceYouTube()
            self.assertIsNotNone(app)
            self.assertEqual(app.var_url.get(), "")
            self.assertTrue(len(app.var_pasta.get()) > 0)
            app.destroy()
        except tk.TclError as e:
            print(f"Skipping GUI display test: {e}")


if __name__ == "__main__":
    unittest.main()
