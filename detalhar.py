# -*- coding: utf-8 -*-
"""
Detalhamento de punção: um DWG-TQS por pilar do projeto (mais PDF e DXF), pelo TQS, e o relatório do lote.

Uso:  python detalhar.py <projeto.json> [--saida PASTA] [--png] [--pilar TITULO] [--so-relatorio]
Saída padrão: saidas/<nome do projeto>/PUN_<pilar>.DWG e RELATORIO_<projeto>.txt / _pilares.csv / _ferros.csv.
Com --png, grava também a imagem de conferência (lida do DWG gravado). Imprime os ferros do núcleo e confere com os
comprimentos que o TQS calculou. Com --so-relatorio, não grava DWG (não precisa do TQS): só o relatório, com os
comprimentos do núcleo.
"""
import argparse
import json
import os
import pathlib
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from nucleo import relatorio as rel_lote                # noqa: E402
from nucleo.detalhe import detalhar, relatorio          # noqa: E402
from nucleo.parametros import ler_projeto               # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--saida")
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--pilar")
    ap.add_argument("--so-relatorio", action="store_true", help="só o relatório, sem gravar DWG (sem o TQS)")
    a = ap.parse_args()
    if not a.so_relatorio:
        from dwg_tqs import prancha                     # só aqui: precisa do TQS
    nome_proj = os.path.splitext(os.path.basename(a.projeto))[0]
    projeto = ler_projeto(a.projeto)
    pasta = a.saida or projeto.get("pasta_saida") or os.path.join(RAIZ, "saidas", nome_proj)
    itens = []
    for par in projeto["pilares"]:
        if a.pilar and str(par.get("titulo")) != a.pilar:
            continue
        res = detalhar(par)
        print(relatorio(res))
        if res["erros"] or a.so_relatorio:
            itens.append(rel_lote.item(res))
            continue
        g = prancha.gerar(res, pasta)
        itens.append(rel_lote.item(res, g))
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
    if not itens:
        print("Nenhum pilar processado.")
        return
    r = rel_lote.montar(itens, projeto=nome_proj, arquivo=os.path.abspath(a.projeto))
    arqs = rel_lote.gravar(r, pasta, nome_proj)
    print(f"Relatório do lote: {', '.join(os.path.basename(v) for v in arqs.values())} em {pasta}")


if __name__ == "__main__":
    main()
