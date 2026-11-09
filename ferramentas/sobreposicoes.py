# -*- coding: utf-8 -*-
"""
Sobreposições numa folha (primitivas, sem o TQS): texto com texto, inclusive os das cotas (onde o TQS os escreve:
acima da linha de cota, ou à esquerda dela, de pé, nas verticais), e texto com as linhas de chamada e as marcas dos
cortes (níveis 253 e 210). Feito em 09/11/2026, quando o usuário achou o "PENTE MESTRE" sobre a marca do corte A e a
chamada da NOTA 2 sobre o texto de uma cota.

Uso:  python -m ferramentas.sobreposicoes <projeto.json> [...]
"""
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

LARG = 0.80                  # largura média do caractere / altura (as fontes do TQS saem em Arial no PDF)
DIMTXT, GAP = 0.18, 0.06     # altura do texto da cota (dwg_tqs.arquivo.COTA) e afastamento da linha (cm de papel)
NIVEIS_CHAMADA = (253, 210)


def _ret(x, y, w, h, a):
    t = math.radians(a)
    ux, uy, vx, vy = math.cos(t), math.sin(t), -math.sin(t), math.cos(t)
    return [(x, y), (x + w * ux, y + w * uy), (x + w * ux + h * vx, y + w * uy + h * vy), (x + h * vx, y + h * vy)]


def _texto_cota(p, E):
    (x1, y1), (x2, y2), (x3, y3) = p["p1"], p["p2"], p["p3"]
    th = DIMTXT * E
    if p["modo"] not in ("h", "v"):
        return None, None
    med = (abs(x2 - x1) if p["modo"] == "h" else abs(y2 - y1)) * p["fator"]
    txt = p["txt"] if p["txt"] is not None else f"{med:.4g}"
    w = len(txt.strip()) * th * LARG
    if p["modo"] == "h":
        return txt, _ret((x1 + x2) / 2 - w / 2, y3 + GAP * E, w, th, 0)
    return txt, _ret(x3 - GAP * E, (y1 + y2) / 2 - w / 2, w, th, 90)


def _eixos(poly):
    out = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if abs(x2 - x1) + abs(y2 - y1) > 1e-9:
            out.append((-(y2 - y1), x2 - x1))
    return out


def _sobrepoe(a, b, folga=0.0):
    """Polígonos convexos que se cruzam (eixos separadores)."""
    for ax, ay in _eixos(a) + _eixos(b):
        n = math.hypot(ax, ay)
        pa = [(x * ax + y * ay) / n for x, y in a]
        pb = [(x * ax + y * ay) / n for x, y in b]
        if max(pa) <= min(pb) + folga or max(pb) <= min(pa) + folga:
            return False
    return True


def textos(folha):
    """[(texto, retângulo)] dos textos e dos textos das cotas da folha."""
    E, out = folha.E, []
    for p in folha.prims:
        if p["t"] == "Texto" and p["txt"].strip():
            esp = len(p["txt"]) - len(p["txt"].lstrip())          # as linhas das notas começam com espaços
            t = math.radians(p["a"])
            x0 = p["x"] + esp * p["h"] * LARG * math.cos(t)
            y0 = p["y"] + esp * p["h"] * LARG * math.sin(t)
            out.append((p["txt"].strip(), _ret(x0, y0, len(p["txt"].strip()) * p["h"] * LARG, p["h"], p["a"])))
        elif p["t"] == "Cota":
            t, r = _texto_cota(p, E)
            if r:
                out.append((f"cota {t}", r))
    return out


def verificar(folha):
    """Sobreposições da folha: lista de textos ("texto x texto: ...", "linha 253 x texto ...")."""
    E = folha.E
    tx = textos(folha)
    probs = set()
    for i in range(len(tx)):
        for j in range(i + 1, len(tx)):
            if _sobrepoe(tx[i][1], tx[j][1], folga=0.02 * E):
                probs.add(f"texto x texto: {tx[i][0]!r} / {tx[j][0]!r}")
    for p in folha.prims:
        if p["t"] in ("Linha", "Polyline") and p["n"] in NIVEIS_CHAMADA:
            for a, b in zip(p["xy"], p["xy"][1:]):
                if tuple(a) == tuple(b):
                    continue
                seg = [tuple(a), tuple(b), tuple(b), tuple(a)]
                for t, r in tx:
                    if _sobrepoe(seg, r, 1e-6):
                        probs.add(f"linha {p['n']} x texto {t!r}")
    return sorted(probs)


def folha_do_pilar(par):
    from nucleo import prancha_cobrinha, prancha_conectores
    from nucleo.detalhe import detalhar
    r = detalhar(par)
    if r["erros"]:
        return None
    return (prancha_cobrinha if r["p"]["solucao"] == "cobrinha" else prancha_conectores).montar(r)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from nucleo.parametros import ler_projeto
    total = 0
    for arq in sys.argv[1:]:
        for par in ler_projeto(arq)["pilares"]:
            f = folha_do_pilar(par)
            if f is None:
                continue
            probs = verificar(f)
            total += len(probs)
            print(f"{par['titulo']}: {len(probs)}")
            for x in probs:
                print("   ", x)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
