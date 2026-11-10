# -*- coding: utf-8 -*-
"""
Visualização 3D do detalhamento de punção: uma página HTML por pilar do projeto (three.js embutido, abre sem
internet), sem o TQS. As propriedades são as da visualização do app de vigas protendidas (nucleo/vista3d.py).

Uso:  python visualizar_3d.py <projeto.json> [--saida PASTA] [--pilar TITULO] [--abrir]
Saída padrão: saidas/<nome do projeto>/PUN_<pilar>-3D.html (a mesma pasta dos DWG). Com --abrir, abre cada página
numa janela própria (modo aplicativo do Edge ou do Chrome) ou no navegador padrão.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from nucleo import vista3d                                # noqa: E402
from nucleo.detalhe import detalhar                       # noqa: E402
from nucleo.parametros import ler_projeto                 # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Visualização 3D do detalhamento de punção (HTML)")
    ap.add_argument("projeto")
    ap.add_argument("--saida", help="pasta de saída (padrão: a do projeto ou saidas/<projeto>)")
    ap.add_argument("--pilar", help="só o pilar com este título")
    ap.add_argument("--abrir", action="store_true", help="abre a página depois de gravar")
    a = ap.parse_args()
    nome_proj = os.path.splitext(os.path.basename(a.projeto))[0]
    projeto = ler_projeto(a.projeto)
    pasta = a.saida or projeto.get("pasta_saida") or os.path.join(RAIZ, "saidas", nome_proj)
    n = 0
    for par in projeto["pilares"]:
        if a.pilar and str(par.get("titulo")) != a.pilar:
            continue
        res = detalhar(par)
        if res["erros"]:
            print(f"{res['p']['titulo']}: não gravado, corrija antes:")
            for e in res["erros"]:
                print(f"   ERRO: {e}")
            continue
        caminho = vista3d.gravar(res, pasta, projeto=nome_proj)
        n += 1
        print(f"3D    {caminho}")
        if a.abrir:
            vista3d.abrir(caminho)
    if not n:
        print("Nenhum pilar gravado.")


if __name__ == "__main__":
    main()
