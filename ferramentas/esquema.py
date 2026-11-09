# -*- coding: utf-8 -*-
"""
Esquema de conferência da geometria calculada pelo núcleo (não é a prancha). Vistas:
- cobrinha: planta da punção (peças com os trechos de cima tracejados e os de baixo contínuos, como no modelo;
  pernas; montagem; gabarito dos pentes mestres), planta do colapso e dois cortes ao longo das cobrinhas (uma linha
  diante da face do pilar e uma ao lado dele);
- conectores: planta dos pinos (pentes das faces em azul, inclinados em roxo, trilhos, contornos e as distâncias
  entre pinos de fora vizinhos nos cantos), planta do colapso e um pente em corte.

Uso:  python ferramentas/esquema.py <projeto.json> [--saida PASTA]     (padrão: saidas/e1)
Requer matplotlib (requirements-dev.txt).
"""
import argparse
import math
import os
import sys

try:
    import matplotlib
except ImportError:
    sys.exit("O esquema precisa do matplotlib: pip install -r requirements-dev.txt")
matplotlib.use("Agg")
import matplotlib.pyplot as plt                         # noqa: E402
from matplotlib.patches import Arc, Circle, Rectangle   # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)

from nucleo.detalhe import detalhar, relatorio          # noqa: E402
from nucleo.parametros import ler_projeto               # noqa: E402

COR = dict(pilar="#d9d9d9", borda="#404040", cob=("#1f5fbf", "#7b3fbf"), mont="#e07b00", col="#2e8b57",
           gab="#9a9a9a", laje="#bfbfbf")


def _xy(c, linha, u):
    """Ponto em planta: a cobrinha corre em c["direcao"] e fica na posição `linha` da outra direção."""
    return (linha, u) if c["direcao"] == "y" else (u, linha)


def _cor(peca):
    return COR["cob"][0] if peca["tipo"] == "extremidade" else COR["cob"][1]


def planta_puncao(ax, r):
    p, c = r["p"], r["cobrinha"]
    ax.add_patch(Rectangle((0, 0), p["bx"], p["by"], fc=COR["pilar"], ec=COR["borda"], lw=1.2, zorder=1))
    g = c["gabarito"]
    ax.add_patch(Rectangle((g[0], g[1]), g[2] - g[0], g[3] - g[1], fill=False, ec=COR["gab"], ls=(0, (4, 3)),
                           lw=0.8, zorder=2))
    rp = max(p["cob_bitola"] / 20.0, 0.6)
    for pc in c["pecas"]:
        for u0, u1, nivel in pc["trechos"]:
            (x0, y0), (x1, y1) = _xy(c, pc["linha"], u0), _xy(c, pc["linha"], u1)
            ax.plot([x0, x1], [y0, y1], color=_cor(pc), lw=1.4, zorder=3, ls=(0, (3, 2)) if nivel == "sup" else "-")
        for u in pc["pernas"]:
            ax.add_patch(Circle(_xy(c, pc["linha"], u), rp, fc="white", ec=_cor(pc), lw=0.8, zorder=4))
    for b in c["montagem"]:
        (x0, y0), (x1, y1) = _xy(c, b["ini"], b["pos"]), _xy(c, b["fim"], b["pos"])
        ax.plot([x0, x1], [y0, y1], color=COR["mont"], lw=0.9, zorder=2)
    ax.set_title(f"{p['titulo']}: planta da punção ({c['n_pecas']} peças de cobrinha; azul: da face para fora, "
                 f"roxo: inteiras ao lado do pilar)", fontsize=9)


def planta_colapso(ax, r):
    p = r["p"]
    ax.add_patch(Rectangle((0, 0), p["bx"], p["by"], fc=COR["pilar"], ec=COR["borda"], lw=1.2, zorder=1))
    for g in r["colapso"]:
        for v in g["pos"]:
            xs, ys = ([g["ini"], g["fim"]], [v, v]) if g["direcao"] == "x" else ([v, v], [g["ini"], g["fim"]])
            ax.plot(xs, ys, color=COR["col"], lw=1.4, zorder=2)
    ax.set_title("colapso progressivo (face inferior)", fontsize=9)


def corte(ax, r, linha, titulo):
    p, c = r["p"], r["cobrinha"]
    h, H = p["h_laje"], c["altura_eixo"]
    L = p["by"] if c["direcao"] == "y" else p["bx"]
    pecas = [pc for pc in c["pecas"] if abs(pc["linha"] - linha) < 1e-6]
    us = [u for pc in pecas for u, _ in pc["pontos"]]
    u0, u1 = min(us) - 15, max(us) + 15
    ax.add_patch(Rectangle((u0, 0), u1 - u0, h, fc="#f2f2f2", ec=COR["laje"], lw=0.8, zorder=0))
    sobre = 0 <= linha <= (p["bx"] if c["direcao"] == "y" else p["by"])
    ax.add_patch(Rectangle((0, -25), L, 25 + h + 25, fc=COR["pilar"] if sobre else "none", ec=COR["borda"], lw=1,
                           ls="-" if sobre else (0, (4, 3)), zorder=1, alpha=0.7))
    for y in (p["c_inf"], h - p["c_sup"]):
        ax.axhline(y, color=COR["gab"], lw=0.5, ls=":", zorder=1)
    z_sup = h - p["c_sup"] - p["cob_bitola"] / 20.0
    z = {"sup": z_sup, "inf": z_sup - H}
    for pc in pecas:
        ax.plot([u for u, _ in pc["pontos"]], [z[n] for _, n in pc["pontos"]], color=_cor(pc), lw=2.2, zorder=3)
    rm = p["mont_bitola"] / 20.0
    for b in c["montagem"]:
        if b["ini"] - 1e-6 <= linha <= b["fim"] + 1e-6:
            ax.add_patch(Circle((b["pos"], z["inf"] + p["cob_bitola"] / 20.0 + rm), rm, fc=COR["mont"], ec="none",
                                zorder=4))
    ax.set_xlim(u0, u1)
    ax.set_ylim(-28, h + 28)
    ax.set_title(titulo, fontsize=9)


def _esp_txt(esp):
    return " / ".join(f"{e:g}".replace(".", ",") for e in esp)


def _contorno(ax, bx, by, a, **kw):
    """Retângulo de cantos arredondados afastado `a` do pilar (os contornos do nível 200 do modelo)."""
    for (x0, y0), (x1, y1) in (((0, -a), (bx, -a)), ((bx + a, 0), (bx + a, by)), ((bx, by + a), (0, by + a)),
                               ((-a, by), (-a, 0))):
        ax.plot([x0, x1], [y0, y1], **kw)
    for (cx, cy), t1 in (((bx, 0), 270), ((bx, by), 0), ((0, by), 90), ((0, 0), 180)):
        ax.add_patch(Arc((cx, cy), 2 * a, 2 * a, theta1=t1, theta2=t1 + 90, color=kw.get("color"),
                         lw=kw.get("lw", 0.6), ls=kw.get("ls", "-")))


def planta_pinos(ax, r):
    p, c = r["p"], r["conectores"]
    ax.add_patch(Rectangle((0, 0), p["bx"], p["by"], fc=COR["pilar"], ec=COR["borda"], lw=1.2, zorder=1))
    for a in c["contornos"]:
        _contorno(ax, p["bx"], p["by"], a, color=COR["gab"], lw=0.6, ls=(0, (1, 2)), zorder=1)
    rc, rf, t = c["pino"]["cabeca_mm"] / 20.0, c["pino"]["bitola"] / 20.0, c["trilhos"]
    for pt in c["pentes"]:
        cor = COR["cob"][1] if pt["face"].startswith("canto") else COR["cob"][0]
        a = math.radians(pt["ang"])
        u, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        (x0, y0), (x1, y1) = pt["pinos"][0], pt["pinos"][-1]
        for lado in (1, -1):                           # trilhos com a largura real, ao lado das cabeças
            off = lado * t["afast"]
            ax.plot([x0 + n[0] * off - u[0] * rc, x1 + n[0] * off + u[0] * rc],
                    [y0 + n[1] * off - u[1] * rc, y1 + n[1] * off + u[1] * rc],
                    color=COR["mont"], lw=t["bitola"] / 10.0, zorder=2, solid_capstyle="butt")
        for x, y in pt["pinos"]:
            ax.add_patch(Circle((x, y), rc, fc="white", ec=cor, lw=0.9, zorder=3))
            ax.add_patch(Circle((x, y), rf, fc=cor, ec="none", zorder=4))
    for v in c["vizinhos"]:
        if not v["canto"]:
            continue
        pa, pb = c["pentes"][v["i"]]["pinos"][-1], c["pentes"][v["j"]]["pinos"][-1]
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], color="#c0392b", lw=0.6, ls=(0, (2, 2)), zorder=2)
        ax.text((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2, f"{v['dist']:.1f}", fontsize=6.5, color="#c0392b",
                ha="center", va="center", zorder=5, bbox=dict(fc="white", ec="none", pad=0.4))
    ax.set_title(f"{p['titulo']}: planta dos pinos ({c['n_pentes']} pentes {c['nome_bloco']}, "
                 f"{c['inclinados']} inclinado(s) por canto; vermelho: pinos de fora vizinhos nos cantos, "
                 f"2d = {2 * c['d']:.1f})", fontsize=9)


def corte_pente(ax, r):
    """Um pente em corte, como a A-A do modelo: laje, pinos de face a face pelos cobrimentos, cabeças, trilhos."""
    p, c = r["p"], r["conectores"]
    h, L = p["h_laje"], c["pino"]["comprimento_mm"] / 10.0
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    u1 = s0 + (n - 1) * sr + 15
    ax.add_patch(Rectangle((-15, 0), u1 + 15, h, fc="#f2f2f2", ec=COR["laje"], lw=0.8, zorder=0))
    ax.add_patch(Rectangle((-15, -25), 15, 25 + h + 25, fc=COR["pilar"], ec=COR["borda"], lw=1, zorder=1))
    for y in (p["c_inf"], h - p["c_sup"]):
        ax.axhline(y, color=COR["gab"], lw=0.5, ls=":", zorder=1)
    rc, rf, esp = c["pino"]["cabeca_mm"] / 20.0, c["pino"]["bitola"] / 20.0, p["con_cabeca_esp"]
    z0 = p["c_inf"]
    for i in range(n):
        u = s0 + i * sr
        ax.add_patch(Rectangle((u - rf, z0), 2 * rf, L, fc=COR["cob"][0], ec="none", zorder=3))
        for zc in (z0, z0 + L - esp):
            ax.add_patch(Rectangle((u - rc, zc), 2 * rc, esp, fc=COR["cob"][0], ec="none", zorder=3))
    rt = c["trilhos"]["bitola"] / 20.0
    ax.add_patch(Rectangle((s0 - rc, z0 + esp), (n - 1) * sr + 2 * rc, 2 * rt, fc=COR["mont"], ec="none", zorder=2))
    d = c["d"]                                         # da face inferior (comprimida) ao centro da negativa
    ax.axhline(d, color="#c0392b", lw=0.6, ls=(0, (4, 2)), zorder=2)
    ax.text(u1, d, f"  negativa (centro): d = {d:g} da face inferior".replace(".", ","), fontsize=7,
            color="#c0392b", va="center")
    ax.set_xlim(-15, u1 + 25)
    ax.set_ylim(-10, h + 10)
    ax.set_title(f"pente em corte: pinos de {c['pino']['comprimento_mm']:g} mm (livre {c['pino']['livre_mm']:g}), "
                 f"cabeça ø{c['pino']['cabeca_mm']} mm x {esp:g} cm, s0 = {s0:g}, sr = {sr:g}", fontsize=9)


def gerar_conectores(r, pasta):
    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(2, 2, height_ratios=[3, 1], hspace=0.25)
    a1, a2, a3 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])
    planta_pinos(a1, r)
    planta_colapso(a2, r)
    corte_pente(a3, r)
    for a in (a1, a2, a3):
        a.set_aspect("equal")
        a.grid(True, lw=0.3, alpha=0.4)
    for a in (a1, a2):
        a.autoscale_view()
    fig.text(0.01, 0.005, relatorio(r), family="monospace", fontsize=6.5, va="bottom")
    fig.subplots_adjust(left=0.05, right=0.98, top=0.97, bottom=0.2, wspace=0.12)
    os.makedirs(pasta, exist_ok=True)
    arq = os.path.join(pasta, f"{r['p']['titulo']}_esquema.png")
    fig.savefig(arq, dpi=110)
    plt.close(fig)
    return arq


def gerar(r, pasta):
    if "conectores" in r:
        return gerar_conectores(r, pasta)
    c = r["cobrinha"]
    Lt = r["p"]["bx"] if c["direcao"] == "y" else r["p"]["by"]
    diante = min((t for t in c["linhas"] if 0 < t < Lt), default=c["linhas"][0])
    ao_lado = max(t for t in c["linhas"] if t < 0)
    fig = plt.figure(figsize=(16, 14))
    gs = fig.add_gridspec(3, 2, height_ratios=[3, 1.1, 1.1], hspace=0.35)
    a1, a2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    a3, a4 = fig.add_subplot(gs[1, :]), fig.add_subplot(gs[2, :])
    planta_puncao(a1, r)
    planta_colapso(a2, r)
    pos = {p["pos"]: p for p in r["ferros"]}
    corte(a3, r, diante, f"corte na linha {c['transversal']} = {diante:g} (diante da face): duas peças que começam "
                         f"na face pelo trecho de baixo; altura {c['altura_eixo']:g} pelo eixo")
    corte(a4, r, ao_lado, f"corte na linha {c['transversal']} = {ao_lado:g} (ao lado do pilar): uma peça inteira, "
                          f"número ímpar de espaços ao lado da face ({_esp_txt(c['esp_lado'])})")
    for a in (a1, a2, a3, a4):
        a.set_aspect("equal")
        a.grid(True, lw=0.3, alpha=0.4)
    for a in (a1, a2):
        a.autoscale_view()
    fig.text(0.01, 0.005, relatorio(r), family="monospace", fontsize=6.5, va="bottom")
    fig.subplots_adjust(left=0.05, right=0.98, top=0.97, bottom=0.17, wspace=0.12)
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
