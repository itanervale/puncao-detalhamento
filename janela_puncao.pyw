# -*- coding: utf-8 -*-
"""Abre a janela do detalhamento de punção: pythonw janela_puncao.pyw [projeto.json] (ou "Detalhar Punção.bat")."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from janela.app import main  # noqa: E402

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
