# -*- coding: utf-8 -*-
"""
Cobrinha em malha ortogonal (pilar interno). Ponto de partida: o desenho de referência PUN_P02-R01
(PADRAO_desenho.md, seção 1.2), com as mudanças pedidas pelo usuário em 03/11/2026 (PLANO, E1):
- nada passa por cima do pilar (interferência com a armadura do pilar);
- toda cobrinha começa na face do pilar (ou no prolongamento dela) pelo trecho de baixo, na face inferior da laje;
- a montagem é interrompida nas faces do pilar e vai mont_ext (30 cm) além da última linha de cobrinhas.

Coordenadas relativas ao canto inferior esquerdo do pilar, em cm; o pilar ocupa [0, bx] x [0, by]. As cobrinhas
correm ao longo de um eixo (u; o do lado menor do pilar, decisão P6) e ficam em linhas do outro (t).
- Malha: linhas a s0 de cada face e mais (n - 1) a cada s para fora; entre as linhas de s0, n = parte inteira do
  vão / s espaços, com a sobra no(s) espaço(s) do meio (o modelo: 172 = 8 x 17 + 2 x 18; 72 = 17 + 19 + 19 + 17).
- Peças:
  "extremidade" (linhas diante das faces, as que cruzariam o pilar): duas por linha, cada uma da face (u = 0 ou
  u = L) para fora, começando pelo trecho de baixo, com uma ponta de s além da última perna;
  "continua" (linhas ao lado do pilar): uma peça inteira, que começa na ponta de fora pelo trecho de baixo. Entre
  as pernas de s0, o número de espaços é ímpar (o menor que deixa cada um <= s, pernas arredondadas a 0,5 cm e
  simétricas; no P2, 5 espaços de 14,5/14,5/14/14,5/14,5): assim as dobras de baixo ficam do mesmo lado que as
  das peças da face em cada fileira, e a montagem, reta, encosta em todas (decisão do usuário em 03/11/2026, Q6).
- Montagem: uma barra por fileira de pernas, perpendicular às cobrinhas, dentro da dobra de baixo (encostada na
  perna, do lado do trecho de baixo). Fileiras fora da faixa do pilar: contínuas; fileiras ao lado do pilar: duas
  barras, da face do pilar até mont_ext além da última linha. Comprimentos arredondados para cima.
"""
import math

from .parametros import altura_eixo_cobrinha, arred_cima


def posicoes_malha(L, s0, s, n):
    """Linhas da malha numa direção: devolve (posições, espaços). L = dimensão do pilar nessa direção."""
    fora = [s0 + k * s for k in range(n)]
    vao = L + 2 * s0
    nesp = max(1, int(math.floor(vao / s + 1e-9)))
    esp = [s] * nesp
    sobra = vao - nesp * s
    if nesp == 1:
        esp = [vao]
    elif nesp % 2:
        esp[nesp // 2] += sobra
    else:
        esp[nesp // 2 - 1] += sobra / 2
        esp[nesp // 2] += sobra / 2
    dentro = [-s0]
    for e in esp:
        dentro.append(dentro[-1] + e)
    pos = [-x for x in reversed(fora[1:])] + dentro + [L + x for x in fora[1:]]
    pos = [round(x, 4) for x in pos]
    return pos, [round(b - a, 4) for a, b in zip(pos, pos[1:])]


def _arred(v):
    """Arredondamento ao centímetro, meio para cima (como o TQS arredonda cada trecho do ferro genérico)."""
    return math.floor(v + 0.5 + 1e-9)


def pernas_ao_lado(L, s0, s):
    """Pernas entre as linhas de s0 (-s0 e L + s0), ao lado do pilar: número ímpar de espaços, o menor que deixa
    cada um <= s; posições em centímetros inteiros (a dobra é medida em cm) e espelhadas (simétricas). Devolve só
    as pernas de dentro. Com meio centímetro, o TQS arredondava cada trecho e o C ficava 2 cm maior (E2)."""
    vao = L + 2 * s0
    n = max(1, math.ceil(vao / s - 1e-9))
    if n % 2 == 0:
        n += 1
    meia = [float(_arred(-s0 + vao * i / n)) for i in range(1, (n + 1) // 2)]
    return meia + [round(L - u, 4) for u in reversed(meia)]


def direcao_cobrinhas(p):
    """Eixo ao longo do qual as cobrinhas correm ("x" ou "y")."""
    d = p["cob_direcao"]
    if d in ("x", "y"):
        return d
    menor_em_x = p["bx"] < p["by"]                # o lado menor do pilar está na direção x
    if d == "menor":
        return "x" if menor_em_x else "y"
    return "y" if menor_em_x else "x"


def _peca(u_ini, pernas, u_fim, H):
    """Peça que começa em u_ini pelo trecho de baixo, passa pelas pernas (em ordem, a partir da face) e termina em
    u_fim. Pontos pelo eixo: (u, "inf" | "sup"). u_fim None (ou igual à última perna): a peça termina na perna, sem
    ponta (a perna junto da borda livre)."""
    nivel = "inf"
    pontos = [(u_ini, nivel)]
    for u in pernas:
        pontos.append((u, nivel))
        nivel = "sup" if nivel == "inf" else "inf"
        pontos.append((u, nivel))
    if u_fim is not None and abs(u_fim - pernas[-1]) > 1e-9:
        pontos.append((u_fim, nivel))
    trechos = [(pontos[i][0], pontos[i + 1][0], pontos[i][1]) for i in range(0, len(pontos) - 1, 2)]
    # C como o TQS: soma dos trechos pelo eixo, cada um arredondado ao centímetro
    comp = sum(_arred(abs(b - a)) for a, b, _ in trechos) + len(pernas) * _arred(H)
    # Forma a partir da face (igual para a peça de um lado e a espelhada do outro): agrupa as posições.
    forma = tuple((round(abs(u - u_ini), 3), n) for u, n in pontos)
    return dict(pontos=pontos, trechos=trechos, pernas=list(pernas), comp=round(comp, 2), forma=forma,
                ini=u_ini, fim=u_fim)


def _lado_de_baixo(peca):
    """Para cada perna da peça: +1 se o trecho de baixo vizinho fica do lado de u maior, -1 se do lado de u menor."""
    lados = {}
    for (a, b, nivel) in peca["trechos"]:
        if nivel != "inf":
            continue
        for perna in peca["pernas"]:
            if abs(perna - a) < 1e-6 and b != a:
                lados[perna] = 1 if b > a else -1
            elif abs(perna - b) < 1e-6 and a != b:
                lados[perna] = 1 if a > b else -1
    return lados


TOL_BORDA = 3.0            # cm: a perna junto da borda só entra se ficar a mais disso da última perna regular
PONTA_BORDA = 5.0          # cm: ponta da peça além da perna junto da borda, até o cobrimento (como as do LPUNC);
                           # assim toda perna tem trecho horizontal dos dois lados (vértices de cima e de baixo)
ORDEM_TIPOS = ("extremidade", "extremidade_borda", "continua", "continua_borda", "recuada")


def limites_borda(p, ax=None):
    """Lados com borda livre em coordenadas locais (u ao longo da cobrinha, t transversal): {"u-", "u+", "t-", "t+"}
    -> None (laje contínua) ou dict(a = distância da face à borda, lim = distância da face ao eixo da perna ou da
    linha mais afastada que cabe: a - c - ø/2, com c o cobrimento da laje, Q15)."""
    from .parametros import cobrimento_borda
    ax = ax or direcao_cobrinhas(p)
    tr = "y" if ax == "x" else "x"
    lados = {"x": ("esquerda", "direita"), "y": ("baixo", "cima")}
    c, fc = cobrimento_borda(p), p["cob_bitola"] / 10.0
    out = {}
    for loc, eixo in (("u", ax), ("t", tr)):
        borda, a = p.get(f"borda_{eixo}") or "", p.get(f"dist_borda_{eixo}") or 0.0
        for sinal, nome in zip("-+", lados[eixo]):
            out[loc + sinal] = dict(a=a, lim=a - c - fc / 2) if borda == nome else None
    return out


def _lado(s0, s, n, borda, junto):
    """Um lado de uma direção: (b, alem). b = distância da face à linha (ou perna) de contorno, s0 ou, com a borda a
    menos de s0, a da borda; alem = distâncias das que ficam além dela (n - 1 a cada s; com borda, só as que cabem e,
    se junto, mais uma junto da borda: Q11)."""
    alem = [s0 + k * s for k in range(1, n)]
    if borda is None:
        return s0, alem
    lim = borda["lim"] - (PONTA_BORDA if junto else 0.0)     # pernas: a ponta vai da última até o cobrimento
    if lim < s0 - 1e-9:
        return lim, []
    alem = [x for x in alem if x <= lim + 1e-9]
    ultima = alem[-1] if alem else s0
    if junto and lim - ultima >= TOL_BORDA:
        alem.append(round(lim, 4))
    return s0, alem


def _malha(L, s0, s, n, b_neg, b_pos, junto):
    """Posições numa direção com borda: como posicoes_malha, com o vão entre os contornos dos dois lados (s0 ou a
    borda) e, além deles, só o que cabe até a borda. Sem borda, é a posicoes_malha."""
    if b_neg is None and b_pos is None:
        return posicoes_malha(L, s0, s, n)
    (bn, an), (bp, ap) = _lado(s0, s, n, b_neg, junto), _lado(s0, s, n, b_pos, junto)
    vao = L + bn + bp
    nesp = max(1, int(math.floor(vao / s + 1e-9)))
    esp = [s] * nesp
    sobra = vao - nesp * s
    if nesp == 1:
        esp = [vao]
    elif nesp % 2:
        esp[nesp // 2] += sobra
    else:
        esp[nesp // 2 - 1] += sobra / 2
        esp[nesp // 2] += sobra / 2
    dentro = [-bn]
    for e in esp:
        dentro.append(dentro[-1] + e)
    pos = [-x for x in reversed(an)] + dentro + [L + x for x in ap]
    pos = [round(x, 4) for x in pos]
    return pos, [round(b - a, 4) for a, b in zip(pos, pos[1:])]


def _pernas_entre(a, b, s, impar):
    """Pernas entre a e b (exclusive), ao lado do pilar: o menor nº de espaços (ímpar, se pedido) com cada um <= s,
    em centímetros inteiros. Com a e b simétricos, é a pernas_ao_lado."""
    vao = b - a
    n = max(1, math.ceil(vao / s - 1e-9))
    if impar and n % 2 == 0:
        n += 1
    return [float(_arred(a + vao * i / n)) for i in range(1, n)]


def detalhar(p):
    """Geometria e quantidades das cobrinhas e da montagem (ver as chaves no fim). Com borda livre (E9), cada lado
    é livre (como no pilar interno) ou de borda, e o lado da borda segue as opções (pedido do usuário em 09/11/2026,
    por região, como nos conectores):
    - sem opção: nada passa da linha da face voltada para a borda (as peças ao lado do pilar param nela, como com a
      borda faceando);
    - cob_face_recuada: as peças diante dessa face, até a borda (no cobrimento), com a última perna junto dela (Q11);
    - cob_construtivas: além dos cantos, as peças ao lado do pilar seguem até a borda.
    Com a borda ao longo das linhas, a linha além da face voltada para a borda vira, conforme as opções, a peça inteira
    (as duas), as duas peças das faces para fora (só as construtivas) ou a peça entre os prolongamentos das faces (só
    a face recuada: "recuada", com as pernas de PONTA_BORDA a L - PONTA_BORDA, como os pentes de con_dist_canto)."""
    from .parametros import cobrimento_borda
    ax = direcao_cobrinhas(p)                     # as cobrinhas correm ao longo de ax (u)
    tr = "y" if ax == "x" else "x"                # e ficam em linhas ao longo de tr (t)
    Ld = {"x": p["bx"], "y": p["by"]}
    s = {"x": p["cob_s_x"], "y": p["cob_s_y"]}
    n = {"x": p["cob_linhas_x"], "y": p["cob_linhas_y"]}
    L, Lt, s0 = Ld[ax], Ld[tr], p["cob_s0"]
    bd = limites_borda(p, ax)
    recuada, construtivas = bool(p.get("cob_face_recuada")), bool(p.get("cob_construtivas"))
    c_b, fc = cobrimento_borda(p), p["cob_bitola"] / 10.0
    # o lado de borda como se ela estivesse na linha da face: nada passa da face
    rente = lambda k: None if bd[k] is None else dict(a=0.0, lim=-c_b - fc / 2)        # noqa: E731
    bdc = {k: (bd[k] if construtivas else rente(k)) for k in ("u-", "u+")}             # peças inteiras
    bdl = {k: (bd[k] if (construtivas or recuada) else rente(k)) for k in ("t-", "t+")}  # linhas
    pernas, esp_pernas = _malha(L, s0, s[ax], n[ax], bdc["u-"], bdc["u+"], junto=True)
    linhas, esp_linhas = _malha(Lt, s0, s[tr], n[tr], bdl["t-"], bdl["t+"], junto=False)
    H = altura_eixo_cobrinha(p)
    ponta = s[ax]

    # Peças da face para fora (diante das faces), com a borda verdadeira: pernas além das faces (u < 0 e u > L).
    (bn, an), (bp, ap) = (_lado(s0, s[ax], n[ax], bd["u-"], True), _lado(s0, s[ax], n[ax], bd["u+"], True))
    antes = [-x for x in [bn] + an] if bn == s0 else []                # da face u = 0 para fora
    depois = [L + x for x in [bp] + ap] if bp == s0 else []            # da face u = L para fora
    # Fim das peças do lado da borda: no cobrimento (u = -lim ou L + lim), com a ponta de PONTA_BORDA.
    fim_a = -bd["u-"]["lim"] if bd["u-"] is not None else None
    fim_d = L + bd["u+"]["lim"] if bd["u+"] is not None else None
    pecas_tipo = {}
    if antes:
        fim = antes[-1] - ponta if bd["u-"] is None else fim_a
        pecas_tipo["a"] = dict(_peca(0.0, antes, fim, H), tipo="extremidade" if bd["u-"] is None else
                               "extremidade_borda")
    if depois:
        fim = depois[-1] + ponta if bd["u+"] is None else fim_d
        pecas_tipo["d"] = dict(_peca(L, depois, fim, H), tipo="extremidade" if bd["u+"] is None else
                               "extremidade_borda")

    # Peça inteira ao lado do pilar: do lado de uma borda, até ela só com as linhas construtivas.
    (bnc, anc), (bpc, apc) = (_lado(s0, s[ax], n[ax], bdc["u-"], True), _lado(s0, s[ax], n[ax], bdc["u+"], True))
    antes_c = [-x for x in [bnc] + anc] if bnc == s0 else []
    depois_c = [L + x for x in [bpc] + apc] if bpc == s0 else []
    contorno_a, contorno_d = -bnc, L + bpc
    if bdc["u-"] is None and bdc["u+"] is None:
        meio = pernas_ao_lado(L, s0, s[ax])                             # ao lado do pilar, entre as linhas de s0
    else:
        meio = _pernas_entre(contorno_a, contorno_d, s[ax], impar=bnc == s0 and bpc == s0)
    lado_a = antes_c if antes_c else [contorno_a]
    lado_d = depois_c if depois_c else [contorno_d]
    todas = list(reversed(lado_a)) + meio + lado_d
    fim_ac = -bdc["u-"]["lim"] if bdc["u-"] is not None else None
    fim_dc = L + bdc["u+"]["lim"] if bdc["u+"] is not None else None
    if bdc["u-"] is not None:                      # borda do lado u < 0: começa na ponta do lado livre, por baixo
        cont = _peca(todas[-1] + ponta, list(reversed(todas)), fim_ac, H)
    elif bdc["u+"] is not None:
        cont = _peca(todas[0] - ponta, todas, fim_dc, H)
    else:
        cont = _peca(todas[0] - ponta, todas, todas[-1] + ponta, H)      # começa na ponta de fora, por baixo
    cont["tipo"] = "continua" if bdc["u-"] is None and bdc["u+"] is None else "continua_borda"
    esp_lado = [round(b - a, 4) for a, b in zip(todas, todas[1:])]

    # Peça diante da face recuada, entre os prolongamentos das faces (linhas além da face voltada para a borda).
    rec = None
    if recuada and (bd["t-"] is not None or bd["t+"] is not None):
        e = PONTA_BORDA
        pr = [e] + _pernas_entre(e, L - e, s[ax], impar=False) + [L - e] if L - 2 * e >= 1.0 else [L / 2.0]
        rec = dict(_peca(0.0, pr, L, H), tipo="recuada")

    pecas = []
    for t in linhas:
        if 0 < t < Lt:             # diante das faces: da face para fora; do lado de uma borda, com a face recuada
            for k, lado in (("a", "u-"), ("d", "u+")):
                if k in pecas_tipo and (bd[lado] is None or recuada):
                    pecas.append(dict(pecas_tipo[k], linha=t))
        else:
            lado_t = "t-" if t < 0 else "t+"
            if bd[lado_t] is None or (recuada and construtivas):
                pecas.append(dict(cont, linha=t))                      # ao lado do pilar: inteira
            else:                                                      # além da face voltada para a borda
                if construtivas:                                       # além dos cantos: das faces para fora
                    for k in ("a", "d"):
                        if k in pecas_tipo:
                            pecas.append(dict(pecas_tipo[k], linha=t))
                if rec:                                                # diante da face recuada
                    pecas.append(dict(rec, linha=t))

    # Posições: peças iguais (mesma forma a partir da face) formam uma posição.
    grupos = {}
    for pc in pecas:
        g = grupos.setdefault(pc["forma"], dict(tipo=pc["tipo"], comp=pc["comp"], quant=0, pontos=pc["pontos"],
                                                n_pernas=len(pc["pernas"])))
        g["quant"] += 1
    posicoes = sorted(grupos.values(), key=lambda g: (ORDEM_TIPOS.index(g["tipo"]) // 2, -g["comp"]))

    # Montagem: uma barra por fileira de pernas, na dobra de baixo, só nas linhas que têm perna nela, mont_ext além
    # da última e a cobrimento da borda nas pontas. Ao lado do pilar, interrompida nas faces.
    fm = p["mont_bitola"] / 10.0
    afast = (fc + fm) / 2
    ext = p["mont_ext"]
    lim0 = -bd["t-"]["a"] + c_b if bd["t-"] is not None else None
    lim1 = Lt + bd["t+"]["a"] - c_b if bd["t+"] is not None else None
    t0, t1 = linhas[0] - ext, linhas[-1] + ext
    if lim0 is not None:
        t0 = max(t0, lim0)
    if lim1 is not None:
        t1 = min(t1, lim1)
    lados = {}
    for pc in [cont, *([rec] if rec else []), *pecas_tipo.values()]:   # nas fileiras de fora valem as peças da face
        lados.update(_lado_de_baixo(pc))
    nas_linhas = {}                                                    # fileira -> linhas que têm perna nela
    for pc in pecas:
        for u in pc["pernas"]:
            nas_linhas.setdefault(u, set()).add(pc["linha"])
    fileiras_a = sorted((u for u in nas_linhas if u < 0), reverse=True)
    fileiras_d = sorted(u for u in nas_linhas if u > L)
    fileiras_m = sorted(u for u in nas_linhas if 0 <= u <= L)
    barras, omitidas = [], {}
    for fileira in (fileiras_a, fileiras_d, fileiras_m):
        for u in fileira:
            pos = round(u + lados[u] * afast, 4)
            ts = sorted(nas_linhas[u])
            if fileira is fileiras_m:                                 # ao lado do pilar: interrompida nas faces
                neg, pos_t = [t for t in ts if t < 0], [t for t in ts if t > Lt]
                lados_m = []
                if neg:
                    lados_m.append((max(neg[0] - ext, lim0) if lim0 is not None else neg[0] - ext, 0.0, "t-"))
                if pos_t:
                    lados_m.append((Lt, min(pos_t[-1] + ext, lim1) if lim1 is not None else pos_t[-1] + ext, "t+"))
                for ini, fim, lado in lados_m:
                    if fim - ini <= 1e-6:
                        continue
                    if bd[lado] is not None and fim - ini < p["mont_min_borda"] - 1e-9:
                        # borda curta: sem montagem entre a face e a borda (os vértices ficam na armadura da laje)
                        omitidas[lado] = round(fim - ini, 2)
                        continue
                    barras.append(dict(fileira=u, pos=pos, ini=ini, fim=fim, tipo="lateral"))
            else:
                ini = max(ts[0] - ext, lim0) if lim0 is not None else ts[0] - ext
                fim = min(ts[-1] + ext, lim1) if lim1 is not None else ts[-1] + ext
                barras.append(dict(fileira=u, pos=pos, ini=ini, fim=fim, tipo="continua"))
    for b in barras:
        b["comp"] = arred_cima(b["fim"] - b["ini"], p["mont_arred"])
    grupos_m = {}
    for b in barras:
        g = grupos_m.setdefault(b["comp"], dict(comp=b["comp"], quant=0, tipo=b["tipo"]))
        g["quant"] += 1
    mont_posicoes = sorted(grupos_m.values(), key=lambda g: -g["comp"])

    # Maior espaçamento entre pernas vizinhas: entre as linhas e, ao longo delas, nas linhas ao lado do pilar.
    tang = max(esp_linhas + esp_lado)
    # Alcance da armadura além de cada face livre (para o C''); nos lados de borda, None.
    alcance = {"u-": -min(todas), "u+": max(todas) - L, "t-": -min(linhas), "t+": max(linhas) - Lt}
    alcance = {k: (None if bd[k] is not None else round(v, 4)) for k, v in alcance.items()}
    # Distância da face à linha (ou perna) de contorno de cada lado: s0 (pente mestre) ou, sem ela do lado da borda,
    # a da borda verdadeira ou a da linha da face (pode ser negativa).
    (btn, _), (btp, _) = _lado(s0, s[tr], n[tr], bdl["t-"], False), _lado(s0, s[tr], n[tr], bdl["t+"], False)

    def contorno_u(k, b_face, b_cont):
        if bd[k] is None or (recuada and b_face == s0):
            return b_face
        return b_cont
    contorno = {"u-": contorno_u("u-", bn, bnc), "u+": contorno_u("u+", bp, bpc), "t-": btn, "t+": btp}
    return dict(
        direcao=ax, transversal=tr,
        pernas=pernas, esp_pernas=esp_pernas, linhas=linhas, esp_linhas=esp_linhas,
        pernas_lado=todas, esp_lado=esp_lado,
        n_linhas=len(linhas), altura_eixo=H, ponta=ponta,
        pecas=pecas, posicoes=posicoes,
        n_pecas=len(pecas),
        montagem=barras, mont_posicoes=mont_posicoes, mont_afast=afast,
        esp_tangencial_max=tang,
        bordas=bd, alcance=alcance, t_mont=(t0, t1), contorno=contorno, mont_omitidas=omitidas,
        opcoes=dict(face_recuada=recuada, construtivas=construtivas),
        gabarito=(-p["cob_s0"], -p["cob_s0"], p["bx"] + p["cob_s0"], p["by"] + p["cob_s0"]),
    )
