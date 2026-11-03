# -*- coding: utf-8 -*-
"""
Verificações geométricas do detalhamento pela NBR 6118:2026, sem dimensionamento. Geram avisos e não impedem o
desenho (PLANO, seção 6.3). Cada aviso: (tipo, texto, referência); tipo "aviso" ou "ok".
"""
from .parametros import altura_util

ORDEM_ITEM = "NBR 6118:2026"


def _f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def cobrinha(p, cob):
    d = altura_util(p)
    out = []

    def checa(cond, ok, ruim, ref):
        out.append(("ok" if cond else "aviso", ok if cond else ruim, ref))

    s0 = p["cob_s0"]
    checa(s0 <= 0.5 * d + 1e-9, f"s0 = {_f(s0)} <= 0,5d = {_f(0.5 * d)}",
          f"s0 = {_f(s0)} passa de 0,5d = {_f(0.5 * d)} (d = {_f(d)})", f"{ORDEM_ITEM}, 19.5.3.3 e Figura 19.9")
    for eixo in ("x", "y"):
        s = p[f"cob_s_{eixo}"]
        checa(s <= 0.75 * d + 1e-9, f"espaçamento em {eixo} = {_f(s)} <= 0,75d = {_f(0.75 * d)}",
              f"espaçamento em {eixo} = {_f(s)} passa de 0,75d = {_f(0.75 * d)} (d = {_f(d)})",
              f"{ORDEM_ITEM}, 19.5.3.3 e Figura 19.9")
        n = p[f"cob_linhas_{eixo}"]
        checa(n >= 3, f"{n} linhas de pernas além das faces perpendiculares a {eixo}",
              f"só {n} linha(s) de pernas além das faces perpendiculares a {eixo}; a norma recomenda três ou mais",
              f"{ORDEM_ITEM}, 19.5.3.3")
    h20 = p["h_laje"] * 10 / 20
    checa(p["cob_bitola"] <= h20 + 1e-9, f"bitola da cobrinha {_f(p['cob_bitola'])} mm <= h/20 = {_f(h20)} mm",
          f"bitola da cobrinha {_f(p['cob_bitola'])} mm passa de h/20 = {_f(h20)} mm", f"{ORDEM_ITEM}, 20.4")
    checa(p["mont_bitola"] >= p["cob_bitola"],
          f"montagem ø{_f(p['mont_bitola'])} >= ø{_f(p['cob_bitola'])} da cobrinha nos vértices de baixo",
          f"montagem ø{_f(p['mont_bitola'])} menor que a cobrinha ø{_f(p['cob_bitola'])}: a barra no vértice deve "
          f"ter pelo menos a bitola da cobrinha", f"{ORDEM_ITEM}, 20.4")
    checa(p["neg_bitola_ext"] >= p["cob_bitola"],
          f"negativa ø{_f(p['neg_bitola_ext'])} >= ø{_f(p['cob_bitola'])} da cobrinha nos vértices de cima",
          f"negativa ø{_f(p['neg_bitola_ext'])} menor que a cobrinha ø{_f(p['cob_bitola'])}: use barras "
          f"adicionais nos vértices com pelo menos a bitola da cobrinha", f"{ORDEM_ITEM}, 20.4")
    out.append(("ok", f"d = {_f(d)} cm (negativa abaixo do trecho de cima da cobrinha)", f"{ORDEM_ITEM}, 19.5.2.1"))
    return out


def avisos(lista):
    return [v for v in lista if v[0] == "aviso"]
