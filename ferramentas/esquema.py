# -*- coding: utf-8 -*-
"""
Esquema de conferência da geometria calculada pelo núcleo (não é a prancha: essa vem na E2). Três vistas:
planta da punção (cobrinhas com os trechos de cima tracejados e os de baixo contínuos, como no modelo; pernas;
montagem; gabarito dos pentes mestres), planta do colapso e corte ao longo de uma cobrinha.

Uso:  python ferramentas/esquema.py <projeto.json> [--saida PASTA]     (padrão: saidas/e1)
Requer matplotlib (requirements-dev.txt).
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from nucleo.detalhe import detalhar, relatorio          # noqa: E402
from nucleo.parametros import ler_projeto               # noqa: E402

COR = dict(pilar="#d9d9d9", borda="#404040", cob="#1f5fbf", mont="#e07b00", col="#2e8b57", gab="#9a9a9a",
           laje="#bfbfbf")


def _xy(c, linha, u):
    """Ponto em planta: a cobrinha corre em c["direcao"] e fica na posição `linha` da outra direção."""
    return (linha, u) if c["direcao"] == "y" else (u, linha)


def planta_puncao(ax, r):
    p, c = r["p"], r["cobrinha"]
    ax.add_patch(Rectangle((0, 0), p["bx"], p["by"], fc=COR["pilar"], ec=COR["borda"], lw=1.2, zorder=1))
    g = c["gabarito"]
    ax.add_patch(Rectangle((g[0], g[1]), g[2] - g[0], g[3] - g[1], fill=False, ec=COR["gab"], ls=(0, (4, 3)),
                           lw=0.8, zorder=2))
    rp = p["cob_bitola"] / 20.0
    for linha in c["linhas"]:
        for u0, u1, nivel in c["trechos"]:
            (x0, y0), (x1, y1) = _xy(c, linha, u0), _xy(c, linha, u1)
            ax.plot([x0, x1], [y0, y1], color=COR["cob"], lw=1.4, zorder=3,
                    ls=(0, (3, 2)) if nivel == "sup" else "-")
        for u in c["pernas"]:
            ax.add_patch(Circle(_xy(c, linha, u), max(rp, 0.6), fc="white", ec=COR["cob"], lw=0.8, zorder=4))
    for m in c["mont_pos"]:
        (x0, y0), (x1, y1) = _xy(c, c["mont_ini"], m), _xy(c, c["mont_fim"], m)
        ax.plot([x0, x1], [y0, y1], color=COR["mont"], lw=0.9, zorder=2)
    ax.set_title(f"{p['titulo']}: planta da punção  ({c['n_cobrinhas']} cobrinhas, {c['n_pernas']} pernas)",
                 fontsize=9)


def planta_colapso(ax, r):
    p = r["p"]
    ax.add_patch(Rectangle((0, 0), p["bx"], p["by"], fc=COR["pilar"], ec=COR["borda"], lw=1.2, zorder=1))
    for g in r["colapso"]:
        for v in g["pos"]:
            xs, ys = ([g["ini"], g["fim"]], [v, v]) if g["direcao"] == "x" else ([v, v], [g["ini"], g["fim"]])
            ax.plot(xs, ys, color=COR["col"], lw=1.4, zorder=2)
    ax.set_title("colapso progressivo (face inferior)", fontsize=9)


def corte(ax, r):
    p, c = r["p"], r["cobrinha"]
    h, H = p["h_laje"], c["altura_eixo"]
    L = p["by"] if c["direcao"] == "y" else p["bx"]
    u0, u1 = c["inicio"] - 20, c["fim"] + 20
    ax.add_patch(Rectangle((u0, 0), u1 - u0, h, fc="#f2f2f2", ec=COR["laje"], lw=0.8, zorder=0))
    ax.add_patch(Rectangle((0, -25), L, 25 + h + 25, fc=COR["pilar"], ec=COR["borda"], lw=1, zorder=1, alpha=0.6))
    for y in (p["c_inf"], h - p["c_sup"]):
        ax.axhline(y, color=COR["gab"], lw=0.5, ls=":", zorder=1)
    z_sup = h - p["c_sup"] - p["cob_bitola"] / 20.0
    z = {"sup": z_sup, "inf": z_sup - H}
    ax.plot([u for u, _ in c["pontos"]], [z[n] for _, n in c["pontos"]], color=COR["cob"], lw=2.2, zorder=3)
    rm = p["mont_bitola"] / 20.0
    for m in c["mont_pos"]:
        ax.add_patch(Circle((m, z["inf"] + p["cob_bitola"] / 20.0 + rm), rm, fc=COR["mont"], ec="none", zorder=4))
    ax.set_xlim(u0, u1)
    ax.set_ylim(-28, h + 28)
    ax.set_title(f"corte ao longo da cobrinha: altura {H:g} pelo eixo, C={round(c['comprimento'])}", fontsize=9)


def gerar(r, pasta):
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1.2], hspace=0.35)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    planta_puncao(a1, r)
    planta_colapso(a2, r)
    corte(a3, r)
    for a in (a1, a2, a3):
        a.set_aspect("equal")
        a.grid(True, lw=0.3, alpha=0.4)
    for a in (a1, a2):
        a.autoscale_view()
    fig.text(0.01, 0.005, relatorio(r), family="monospace", fontsize=6.5, va="bottom")
    fig.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.24, wspace=0.12)
    os.makedirs(pasta, exist_ok=True)
    arq = os.path.join(pasta, f"{r['p']['titulo']}_esquema.png")
    fig.savefig(arq, dpi=110)
    plt.close(fig)
    return arq


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("--saida", default=os.path.join(RAIZ, "saidas", "e1"))
    a = ap.parse_args()
    for par in ler_projeto(a.projeto)["pilares"]:
        r = detalhar(par)
        if r["erros"]:
            print(relatorio(r))
            continue
        print("gravado", gerar(r, a.saida))


if __name__ == "__main__":
    main()
