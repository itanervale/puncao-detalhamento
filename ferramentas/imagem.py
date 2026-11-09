# -*- coding: utf-8 -*-
"""
Imagem de conferência (PNG) de um despejo JSON (ferramentas/ler_modelo.py) ou de uma prancha em primitivas no mesmo
formato. Dois modos:
- "plot" (padrão): fundo branco, cor e espessura da pena de cada nível (nucleo/niveis.json), papel em tamanho real;
- "tela": fundo preto, cor de tela de cada entidade (paleta do TQS), como no editor.

Uso:  python ferramentas/imagem.py <despejo.json> [--modo plot|tela] [--janela x1,y1,x2,y2] [--saida arq.png] [--dpi N]
Requer matplotlib (requirements-dev.txt).
"""
import argparse
import json
import math
import os
import pathlib
import sys

try:
    import matplotlib
except ImportError as e:                                # também importado pelo detalhar.py --png
    raise ImportError("A imagem de conferência precisa do matplotlib: pip install -r requirements-dev.txt") from e
matplotlib.use("Agg")
import matplotlib.pyplot as plt                         # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon     # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
NIVEIS = json.loads(pathlib.Path(os.path.join(RAIZ, "nucleo", "niveis.json")).read_text(encoding="utf-8"))
ESTILOS = {0: "-", 1: (0, (6, 3)), 2: (0, (1, 2)), 3: (0, (8, 2, 1, 2)), 4: (0, (8, 2, 1, 2, 1, 2)), 5: (0, (4, 2))}
PT_MM = 72 / 25.4


def _misturar(cor, pct):
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    f = pct / 100.0
    return "#%02x%02x%02x" % tuple(round(255 - (255 - c) * f) for c in (r, g, b))


def _extensao(ents):
    xs, ys = [], []
    for e in ents:
        if e.get("xy"):
            xs += [p[0] for p in e["xy"]]
            ys += [p[1] for p in e["xy"]]
        elif "r" in e:
            xs += [e["x"] - e["r"], e["x"] + e["r"]]
            ys += [e["y"] - e["r"], e["y"] + e["r"]]
        elif e["t"] == "Texto":
            xs.append(e["x"])
            ys.append(e["y"])
    return min(xs), min(ys), max(xs), max(ys)


def desenhar(d, png, modo="plot", janela=None, dpi=150):
    ents = [e for e in d["ents"] if e["t"] in ("Linha", "Polyline", "Curva", "Circulo", "Arco", "Texto")]
    esc = float(d.get("info", {}).get("escala") or 1.0)
    x1, y1, x2, y2 = janela or _extensao(ents)
    mx, my = (x2 - x1) * 0.02, (y2 - y1) * 0.02
    x1, y1, x2, y2 = x1 - mx, y1 - my, x2 + mx, y2 + my
    larg_pol = (x2 - x1) / esc / 2.54                 # papel em tamanho real (cm do desenho / escala)
    alt_pol = (y2 - y1) / esc / 2.54
    k = min(1.0, 40.0 / max(larg_pol, alt_pol))       # limita a imagem a 40 polegadas
    fig = plt.figure(figsize=(larg_pol * k, alt_pol * k))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x1, x2)
    ax.set_ylim(y1, y2)
    ax.set_aspect("equal")
    ax.axis("off")
    fundo = "#000000" if modo == "tela" else "#ffffff"
    fig.patch.set_facecolor(fundo)
    pt_por_unidade = larg_pol * k * 72 / (x2 - x1)
    pal = NIVEIS["paleta_tela"]
    for e in ents:
        n = e["n"] if isinstance(e["n"], int) else 0
        nv = NIVEIS["niveis"].get(str(n), {})
        if modo == "tela":
            c = e.get("c", 7)
            cor = pal.get(str(c), "#ffffff") if isinstance(c, int) and c > 0 else "#ffffff"
            lw = 0.6
        else:
            cor = nv.get("cor_plot", "#000000")
            if cor.lower() == "#ffffff" and not nv.get("hachura"):
                cor = "#d0d0d0"
            lw = max(0.15, nv.get("espessura", 0.2) * PT_MM * k)
        s = e.get("s", 0)
        if s is None or s < 0:
            s = nv.get("estilo_tela", 0) if modo == "tela" else nv.get("estilo_plot", 0)
        ls = ESTILOS.get(s, "-")
        if e["t"] in ("Linha", "Polyline", "Curva") and e.get("xy"):
            xy = e["xy"]
            fechada = len(xy) > 2 and abs(xy[0][0] - xy[-1][0]) < 1e-6 and abs(xy[0][1] - xy[-1][1]) < 1e-6
            hd = nv.get("hachura_def")
            if e.get("fill") or (modo == "plot" and fechada and hd and hd["tipo"] == 4):
                pct = 100 if e.get("fill") else hd["parametro"]
                base = cor if modo == "tela" else nv.get("cor_plot", "#000000")
                if base.lower() == "#ffffff":
                    base = "#000000"
                ax.add_patch(Polygon(xy, closed=True, facecolor=_misturar(base, pct), edgecolor="none", zorder=1))
            ax.plot([p[0] for p in xy], [p[1] for p in xy], color=cor, lw=lw, ls=ls, zorder=2,
                    solid_capstyle="round")
        elif e["t"] == "Circulo":
            ax.add_patch(Circle((e["x"], e["y"]), e["r"], fill=False, color=cor, lw=lw, ls=ls, zorder=2))
        elif e["t"] == "Arco":
            ax.add_patch(Arc((e["x"], e["y"]), 2 * e["r"], 2 * e["r"], theta1=e["a1"], theta2=e["a2"],
                             color=cor, lw=lw, ls=ls, zorder=2))
        elif e["t"] == "Texto" and e["txt"].strip():
            if not (x1 <= e["x"] <= x2 and y1 <= e["y"] <= y2):
                continue
            tam = e["h"] / 0.72 * pt_por_unidade         # altura da maiúscula ~ 0,72 do corpo da fonte
            ax.text(e["x"], e["y"], e["txt"].replace("{", "ø").strip("\r\n"), fontsize=max(tam, 0.5),
                    rotation=e.get("a", 0), color=cor, ha="left", va="baseline", rotation_mode="anchor",
                    family="DejaVu Sans", zorder=3)
    fig.savefig(png, dpi=dpi, facecolor=fundo)
    plt.close(fig)
    return png


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("despejo")
    ap.add_argument("--modo", default="plot", choices=("plot", "tela"))
    ap.add_argument("--janela")
    ap.add_argument("--saida")
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()
    d = json.loads(pathlib.Path(a.despejo).read_text(encoding="utf-8"))
    jan = [float(v) for v in a.janela.split(",")] if a.janela else None
    png = a.saida or os.path.splitext(a.despejo)[0] + ("_tela" if a.modo == "tela" else "") + ".png"
    print("gravado", desenhar(d, png, a.modo, jan, a.dpi))


if __name__ == "__main__":
    main()
