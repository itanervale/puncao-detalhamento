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
    tang = cob["esp_tangencial_max"]
    checa(tang <= 2 * d + 1e-9, f"maior espaçamento entre pernas vizinhas = {_f(tang)} <= 2d = {_f(2 * d)}",
          f"espaçamento de {_f(tang)} entre pernas vizinhas passa de 2d = {_f(2 * d)}",
          f"{ORDEM_ITEM}, 19.5.3.4 e Figura 19.8")
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


def conectores(p, con):
    d = con["d"]
    out = []

    def checa(cond, ok, ruim, ref):
        out.append(("ok" if cond else "aviso", ok if cond else ruim, ref))

    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    checa(s0 <= 0.5 * d + 1e-9, f"s0 = {_f(s0)} <= 0,5d = {_f(0.5 * d)}",
          f"s0 = {_f(s0)} passa de 0,5d = {_f(0.5 * d)} (d = {_f(d)})", f"{ORDEM_ITEM}, 19.5.3.3 e Figura 19.9")
    checa(sr <= 0.75 * d + 1e-9, f"sr = {_f(sr)} <= 0,75d = {_f(0.75 * d)}",
          f"sr = {_f(sr)} passa de 0,75d = {_f(0.75 * d)} (d = {_f(d)})", f"{ORDEM_ITEM}, 19.5.3.3 e Figura 19.9")
    checa(n >= 3, f"{n} pinos por pente (linhas de pinos)",
          f"só {n} pino(s) por pente; a norma recomenda três linhas ou mais", f"{ORDEM_ITEM}, 19.5.3.3")
    k = con["inclinados"]
    canto, face = con["esp_canto_max"], con["esp_face_max"]
    txt_k = "sem pentes inclinados (cruz)" if k == 0 else f"{k} pente(s) inclinado(s) por canto"
    checa(canto <= 2 * d + 1e-9,
          f"{txt_k}: pinos de fora vizinhos nos cantos a {_f(canto)} <= 2d = {_f(2 * d)}",
          f"{txt_k}: pinos de fora vizinhos nos cantos a {_f(canto)}, mais que 2d = {_f(2 * d)}; o contorno C'' "
          f"fica interrompido nos cantos (arranjo em cruz)", f"{ORDEM_ITEM}, 19.5.3.4 e Figura 19.8")
    if face:
        checa(face <= 2 * d + 1e-9, f"pentes vizinhos ao longo das faces a {_f(face)} <= 2d = {_f(2 * d)}",
              f"pentes vizinhos ao longo das faces a {_f(face)}, mais que 2d = {_f(2 * d)}: aumente o nº de pentes "
              f"na face", f"{ORDEM_ITEM}, 19.5.3.4 e Figura 19.8")
    pino = con["pino"]
    checa(pino["no_catalogo"], f"pino ø{_f(pino['bitola'])} do catálogo Trejor (cabeça de {pino['cabeca_mm']} mm)",
          f"pino ø{_f(pino['bitola'])} fora do catálogo Trejor (ø6,3 a ø32); a cabeça foi desenhada com "
          f"{pino['cabeca_mm']} mm", "catálogo Trejor, p. 3")
    checa(pino["comprimento_mm"] >= pino["minimo_mm"],
          f"pino de {_f(pino['comprimento_mm'])} mm >= {pino['minimo_mm']} mm",
          f"pino de {_f(pino['comprimento_mm'])} mm, abaixo do mínimo de {pino['minimo_mm']} mm do fabricante",
          "catálogo Trejor, p. 3")
    if p["con_montagem"]:
        out.append(("ok", "montagem positiva nos conectores ligada (opcional; o padrão do escritório aproveita as "
                    "barras de flexão da laje, nota 1)", "PLANO, P7 e Q7"))
    out.append(("ok", f"d = {_f(d)} cm (negativa abaixo da cabeça do pino de {_f(p['con_cabeca_esp'])} cm)",
                f"{ORDEM_ITEM}, 19.5.2.1"))
    return out


def avisos(lista):
    return [v for v in lista if v[0] == "aviso"]
