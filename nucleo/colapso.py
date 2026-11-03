# -*- coding: utf-8 -*-
"""
Armadura contra colapso progressivo: barras retas na face inferior, passando dentro do pilar e col_ext além das
faces. Em cada face, n barras distribuídas por igual, cada uma no meio da sua faixa: posição (i + 1/2)·L/n.
Nos dois modelos: 3 barras na face de 50 (8,33; 25; 41,67) e 8 na de 150 (a cada 18,75, a 1ª em 9,375).

A 1ª posição é a das barras que correm em x (atravessam as faces de comprimento by), como nos dois modelos
(conectores: N1 8 ø10 C=220; cobrinha: N3 3 ø10 C=320).
"""
import math


def detalhar(p):
    bx, by, ext = p["bx"], p["by"], p["col_ext"]
    nx, ny = p["col_n_face_by"], p["col_n_face_bx"]       # barras que correm em x / em y
    em_x = dict(direcao="x", quant=nx, pos=[round((i + 0.5) * by / nx, 4) for i in range(nx)],
                ini=-ext, fim=bx + ext, comp=math.ceil(round(bx + 2 * ext, 6)))
    em_y = dict(direcao="y", quant=ny, pos=[round((i + 0.5) * bx / ny, 4) for i in range(ny)],
                ini=-ext, fim=by + ext, comp=math.ceil(round(by + 2 * ext, 6)))
    return [em_x, em_y]
