# -*- coding: utf-8 -*-
"""
Cobrinha em malha ortogonal (pilar interno), pelo desenho de referência PUN_P02-R01 (PADRAO_desenho.md, seção 1.2).

Coordenadas relativas ao canto inferior esquerdo do pilar, em cm; o pilar ocupa [0, bx] x [0, by].
- Linhas da malha: a 1ª a s0 de cada face e mais (n - 1) a cada s para fora. Entre as linhas de s0 (por cima do
  pilar, decisão P5), n = parte inteira do vão / s espaços, e a sobra vai para o(s) espaço(s) do meio: 172 = 8 x 17
  + 2 x 18 e 72 = 17 + 19 + 19 + 17 no modelo.
- Cada cobrinha corre numa direção (a do lado menor do pilar, decisão P6) e fica numa linha da malha da outra.
  As pernas ficam nas linhas da direção em que ela corre; começa (na ponta de coordenada menor) por um trecho de
  cima e alterna; as pontas têm o comprimento do espaçamento. Pontos do ferro pelo eixo (o TQS soma os trechos).
- Montagem positiva: uma barra por linha de pernas, perpendicular às cobrinhas, dentro da dobra de baixo (encostada
  na perna, do lado do trecho de baixo), mont_ext além da 1ª e da última cobrinha, comprimento arredondado para cima.
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


def detalhar(p):
    """Geometria e quantidades da cobrinha e da montagem. Devolve um dicionário (ver as chaves no fim)."""
    ax = direcao_cobrinhas(p)                     # as cobrinhas correm ao longo de ax
    tr = "y" if ax == "x" else "x"                # e se repetem ao longo de tr
    L = {"x": p["bx"], "y": p["by"]}
    s = {"x": p["cob_s_x"], "y": p["cob_s_y"]}
    n = {"x": p["cob_linhas_x"], "y": p["cob_linhas_y"]}
    pernas, esp_pernas = posicoes_malha(L[ax], p["cob_s0"], s[ax], n[ax])
    linhas, esp_linhas = posicoes_malha(L[tr], p["cob_s0"], s[tr], n[tr])
    H = altura_eixo_cobrinha(p)
    ponta = s[ax]
    u0, u1 = pernas[0] - ponta, pernas[-1] + ponta

    # Pontos pelo eixo, ao longo da cobrinha: (u, "sup" | "inf"); começa por cima.
    pontos = [(u0, "sup")]
    nivel = "sup"
    for u in pernas:
        pontos.append((u, nivel))
        nivel = "inf" if nivel == "sup" else "sup"
        pontos.append((u, nivel))
    pontos.append((u1, nivel))
    trechos = [(pontos[i][0], pontos[i + 1][0], pontos[i][1]) for i in range(0, len(pontos), 2)]
    comp = (u1 - u0) + len(pernas) * H

    # Montagem: dentro da dobra de baixo de cada perna (perna i entre os trechos i e i+1; os de baixo são ímpares).
    fc, fm = p["cob_bitola"] / 10.0, p["mont_bitola"] / 10.0
    afast = (fc + fm) / 2
    mont_pos = [round(u + afast if i % 2 == 0 else u - afast, 4) for i, u in enumerate(pernas)]
    mont_ini, mont_fim = linhas[0] - p["mont_ext"], linhas[-1] + p["mont_ext"]
    mont_comp = arred_cima(mont_fim - mont_ini, p["mont_arred"])

    return dict(
        direcao=ax, transversal=tr,
        pernas=pernas, esp_pernas=esp_pernas,        # ao longo de ax (relativo ao pilar)
        linhas=linhas, esp_linhas=esp_linhas,        # posição de cada cobrinha ao longo de tr
        n_cobrinhas=len(linhas), n_pernas=len(pernas),
        altura_eixo=H, ponta=ponta, inicio=u0, fim=u1,
        pontos=pontos, trechos=trechos, comprimento=round(comp, 2),
        mont_pos=mont_pos, mont_ini=mont_ini, mont_fim=mont_fim, mont_comp=mont_comp,
        mont_afast=afast,
        gabarito=(-p["cob_s0"], -p["cob_s0"], p["bx"] + p["cob_s0"], p["by"] + p["cob_s0"]),
    )
