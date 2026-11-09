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
    out += _bordas(p, d)
    for lado, comp in (cob.get("mont_omitidas") or {}).items():
        out.append(("ok", f"borda curta: sem montagem entre a face do pilar e a borda ({_f(comp)} cm, menos de "
                    f"{_f(p['mont_min_borda'])}); os vértices de baixo dessas linhas ficam na armadura positiva da "
                    f"laje", "decisão do usuário, 09/11/2026"))
    out.append(("ok", f"d = {_f(d)} cm (negativa abaixo do trecho de cima da cobrinha)", f"{ORDEM_ITEM}, 19.5.2.1"))
    return out


def _bordas(p, d):
    """Pilar de borda ou de canto (E9): onde fica a borda livre e um aviso se ela estiver a 2d ou mais da face."""
    from .parametros import cobrimento_borda, posicao
    pos = posicao(p)
    if pos == "interno":
        return []
    out, lados = [], []
    for eixo in ("x", "y"):
        lado, a = p[f"borda_{eixo}"], p[f"dist_borda_{eixo}"]
        if not lado:
            continue
        lados.append(f"{lado} ({'faceando' if a == 0 else _f(a) + ' cm da face'})")
        if a >= 2 * d - 1e-9:
            out.append(("aviso", f"borda livre {lado} a {_f(a)} cm da face, 2d = {_f(2 * d)} ou mais: o contorno C' não "
                        f"é cortado, e o pilar pode ser tratado como interno", f"{ORDEM_ITEM}, 19.5.2.3"))
    out.insert(0, ("ok", f"pilar de {pos}: borda livre {' e '.join(lados)}; armadura de punção, montagem e colapso até "
                   f"o cobrimento da borda ({_f(cobrimento_borda(p))} cm)", f"{ORDEM_ITEM}, 19.5.2.3 e 19.5.2.4"))
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


def colapso(res):
    """Armadura contra colapso progressivo (19.5.4): ancoragem além de C'' (com armadura de punção, regra do usuário de
    09/11/2026) e, com as cargas do TQS, As·fyd >= 1,5·FSd."""
    from . import colapso as col
    p, out = res["p"], []
    anc = col.ancoragem(res)
    iguais = abs(anc["x"]["a"] - anc["y"]["a"]) < 1e-6
    for direcao, v in (("x e y", anc["x"]),) if iguais else tuple(anc.items()):
        base = (f"C'' a {_f(v['a'])} cm da face (última linha a {_f(v['ult'])} cm + 2d); lb = {_f(v['lb'])} cm "
                f"(ø{_f(p['col_bitola'])}, fck {_f(p['fck'])} MPa)")
        if v["ok"]:
            out.append(("ok", f"colapso em {direcao}: {_f(v['disponivel'])} cm além de C'' >= lb; {base}",
                        f"{ORDEM_ITEM}, 19.5.4 e 9.4.2.4"))
        else:
            falta = "termina antes de C''" if v["disponivel"] < 0 else f"só {_f(v['disponivel'])} cm além de C''"
            out.append(("aviso", f"colapso em {direcao}: a barra {falta}; {base}; use pelo menos {_f(v['minimo'])} cm "
                        f"além da face (hoje {_f(p['col_ext'])})", f"{ORDEM_ITEM}, 19.5.4 e 9.4.2.4"))
    if p["col_gancho_borda"] and any(any(b["ganchos"]) for b in res["colapso"]):
        alt, vao = col.altura_gancho(p["col_bitola"]), p["h_laje"] - p["c_sup"] - p["c_inf"]
        txt = (f"colapso: gancho de 90° na borda com {_f(alt)} cm de altura (ponta de 8ø e pino de "
               f"{_f(col.pino(p['col_bitola']))} cm)")
        out.append(("ok", f"{txt} <= {_f(vao)} cm entre os cobrimentos", f"{ORDEM_ITEM}, 9.4.2.3 e Tabela 9.1")
                   if alt <= vao + 1e-9 else
                   ("aviso", f"{txt}: não cabe nos {_f(vao)} cm entre os cobrimentos", f"{ORDEM_ITEM}, 9.4.2.3"))
    cap = col.capacidade(p)
    if cap:
        txt = (f"colapso: As = {_f(cap['as_ef'])} cm2 (barras que cruzam cada face) e 1,5·FSd/fyd = "
               f"{_f(cap['as_nec'])} cm2, FSd = 1,2 x {_f(cap['fk'] / col.TF_KN)} tf (comb. {cap['n']}, do TQS)")
        out.append(("ok" if cap["ok"] else "aviso", txt if cap["ok"] else txt + ": aumente as barras ou a bitola",
                    f"{ORDEM_ITEM}, 19.5.4"))
    return out


def avisos(lista):
    return [v for v in lista if v[0] == "aviso"]
