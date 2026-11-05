# -*- coding: utf-8 -*-
"""
Detalhamento de punção: um DWG-TQS por pilar do projeto (mais PDF e DXF), pelo TQS.

Uso:  python detalhar.py <projeto.json> [--saida PASTA] [--png] [--pilar TITULO]
Saída padrão: saidas/<nome do projeto>/PUN_<pilar>.DWG. Com --png, grava também a imagem de conferência
(lida do DWG gravado). Imprime os ferros do núcleo e confere com os comprimentos que o TQS calculou.
"""
import argparse
import json
import os
import pathlib
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from nucleo.detalhe import detalhar, relatorio          # noqa: E402
from nucleo.parametros import ler_projeto               # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--saida")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--pilar")
    a = ap.parse_args()
    from dwg_tqs import prancha                         # só aqui: precisa do TQS
    nome_proj = os.path.splitext(os.path.basename(a.projeto))[0]
    pasta = a.saida or os.path.join(RAIZ, "saidas", nome_proj)
    for par in ler_projeto(a.projeto)["pilares"]:
        if a.pilar and str(par.get("titulo")) != a.pilar:
            continue
        res = detalhar(par)
        print(relatorio(res))
        if res["erros"]:
            continue
        g = prancha.gerar(res, pasta)
        print(f"   gravado: {', '.join(os.path.basename(v) for k, v in g['arquivos'].items() if k != 'aviso')}")
        if g["arquivos"].get("aviso"):
            print("   AVISO:", g["arquivos"]["aviso"])
        print(f"   ferros pelo TQS: {g['tabela_tqs']} -> {'confere com o núcleo' if g['confere'] else 'DIFERE'}")
        if a.png:
            from ferramentas import ler_modelo, imagem
            d = ler_modelo.ler(g["arquivos"]["dwg"])
            base = os.path.splitext(g["arquivos"]["dwg"])[0]
            pathlib.Path(base + ".json").write_text(json.dumps(d, ensure_ascii=False, default=str), encoding="utf-8")
            print("   imagem:", imagem.desenhar(d, base + ".png"))


if __name__ == "__main__":
    main()
