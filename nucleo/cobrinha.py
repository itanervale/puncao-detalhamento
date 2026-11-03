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
- Peças de cada linha, todas começando numa face (u = 0 ou u = L) pelo trecho de baixo:
  "extremidade": da face para fora, com as pernas de fora e uma ponta de s além da última (todas as linhas);
  "lateral": só nas linhas ao lado do pilar (fora da faixa dele), de u = 0 a u = L, com as pernas entre as faces.
  Cortar também as linhas ao lado do pilar mantém as dobras de baixo do mesmo lado em cada fileira, e a montagem,
  reta, encosta nelas.
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
    u_fim. Pontos pelo eixo: (u, "inf" | "sup")."""
    nivel = "inf"
    pontos = [(u_ini, nivel)]
    for u in pernas:
        pontos.append((u, nivel))
        nivel = "sup" if nivel == "inf" else "inf"
        pontos.append((u, nivel))
    pontos.append((u_fim, nivel))
    trechos = [(pontos[i][0], pontos[i + 1][0], pontos[i][1]) for i in range(0, len(pontos), 2)]
    comp = abs(u_fim - u_ini) + len(pernas) * H
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


def detalhar(p):
    """Geometria e quantidades das cobrinhas e da montagem (ver as chaves no fim)."""
    ax = direcao_cobrinhas(p)                     # as cobrinhas correm ao longo de ax (u)
    tr = "y" if ax == "x" else "x"                # e ficam em linhas ao longo de tr (t)
    Ld = {"x": p["bx"], "y": p["by"]}
    s = {"x": p["cob_s_x"], "y": p["cob_s_y"]}
    n = {"x": p["cob_linhas_x"], "y": p["cob_linhas_y"]}
    L, Lt = Ld[ax], Ld[tr]
    pernas, esp_pernas = posicoes_malha(L, p["cob_s0"], s[ax], n[ax])
    linhas, esp_linhas = posicoes_malha(Lt, p["cob_s0"], s[tr], n[tr])
    H = altura_eixo_cobrinha(p)
    ponta = s[ax]

    antes = sorted((u for u in pernas if u < 0), reverse=True)          # da face u = 0 para fora
    depois = sorted(u for u in pernas if u > L)                         # da face u = L para fora
    meio = sorted(u for u in pernas if 0 < u < L)                       # entre as faces (linhas ao lado do pilar)
    ext_a = _peca(0.0, antes, antes[-1] - ponta, H)
    ext_d = _peca(L, depois, depois[-1] + ponta, H)
    lat = _peca(0.0, meio, L, H) if meio else None

    pecas = []
    for t in linhas:
        pecas.append(dict(ext_a, linha=t, tipo="extremidade"))
        pecas.append(dict(ext_d, linha=t, tipo="extremidade"))
        if lat and not (0 < t < Lt):                                   # só as linhas ao lado do pilar
            pecas.append(dict(lat, linha=t, tipo="lateral"))

    # Posições: peças iguais (mesma forma a partir da face) formam uma posição.
    grupos = {}
    for pc in pecas:
        g = grupos.setdefault(pc["forma"], dict(tipo=pc["tipo"], comp=pc["comp"], quant=0, pontos=pc["pontos"],
                                                n_pernas=len(pc["pernas"])))
        g["quant"] += 1
    posicoes = sorted(grupos.values(), key=lambda g: (g["tipo"] != "extremidade", -g["comp"]))

    # Montagem: uma barra por fileira de pernas, na dobra de baixo.
    fc, fm = p["cob_bitola"] / 10.0, p["mont_bitola"] / 10.0
    afast = (fc + fm) / 2
    t0, t1 = linhas[0] - p["mont_ext"], linhas[-1] + p["mont_ext"]
    barras = []
    for peca, fileira in ((ext_a, antes), (ext_d, depois), (lat, meio)):
        if not peca:
            continue
        lados = _lado_de_baixo(peca)
        for u in fileira:
            pos = round(u + lados[u] * afast, 4)
            if peca is lat:                                           # ao lado do pilar: interrompida nas faces
                barras.append(dict(fileira=u, pos=pos, ini=t0, fim=0.0, tipo="lateral"))
                barras.append(dict(fileira=u, pos=pos, ini=Lt, fim=t1, tipo="lateral"))
            else:
                barras.append(dict(fileira=u, pos=pos, ini=t0, fim=t1, tipo="continua"))
    for b in barras:
        b["comp"] = arred_cima(b["fim"] - b["ini"], p["mont_arred"])
    grupos_m = {}
    for b in barras:
        g = grupos_m.setdefault(b["comp"], dict(comp=b["comp"], quant=0, tipo=b["tipo"]))
        g["quant"] += 1
    mont_posicoes = sorted(grupos_m.values(), key=lambda g: -g["comp"])

    # Maior espaçamento tangencial (entre linhas vizinhas e entre pernas vizinhas ao lado das faces).
    tang = max(esp_linhas + esp_pernas)
    return dict(
        direcao=ax, transversal=tr,
        pernas=pernas, esp_pernas=esp_pernas, linhas=linhas, esp_linhas=esp_linhas,
        n_linhas=len(linhas), altura_eixo=H, ponta=ponta,
        pecas=pecas, posicoes=posicoes,
        n_pecas=len(pecas),
        montagem=barras, mont_posicoes=mont_posicoes, mont_afast=afast,
        esp_tangencial_max=tang,
        gabarito=(-p["cob_s0"], -p["cob_s0"], p["bx"] + p["cob_s0"], p["by"] + p["cob_s0"]),
    )
