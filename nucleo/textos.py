# -*- coding: utf-8 -*-
"""Textos e nomes de arquivo aceitos pelo TQS. Copiado de _apps/EstacaEscavada/estaca_core.py (txt_tqs e
limpar_nome), em 03/11/2026, para este repositório não depender de outras pastas."""
import re

# As fontes do TQS não têm estes caracteres; "{" é o símbolo de bitola nas fontes do TQS.
_TROCA_TQS = {"—": "-", "–": "-", "−": "-", "≥": ">=", "≤": "<=", "³": "3", "²": "2", "º": "o", "ª": "a", "“": '"',
              "”": '"', "‘": "'", "’": "'", "…": "...", "•": "-", "×": "x", "·": ".", "ø": "{", "Ø": "{"}


def txt_tqs(s):
    """Texto que o TQS consegue gravar: troca os caracteres acima e o que sobrar fora do latin-1 vira "?"
    (a interface grava em latin-1, e um caractere fora dele derruba a gravação)."""
    s = "".join(_TROCA_TQS.get(ch, ch) for ch in str(s))
    return s.encode("latin-1", "replace").decode("latin-1")


def limpar_nome(nome, padrao="PUN"):
    """Nome de arquivo válido. Sem ponto: com ponto no nome, a plotagem em PDF do TQS falha."""
    return re.sub(r'[\\/:*?"<>|.]+', "_", str(nome)).strip() or padrao
