# -*- coding: utf-8 -*-
"""
Prancha da cobrinha (pilar interno) em primitivas, no padrão do desenho de referência PUN_P02-R01
(PADRAO_desenho.md), com as regras do usuário de 03/11/2026 (PLANO, E1). Sem o TQS.

Vistas (cobrinhas ao longo de y; coordenadas com a origem no canto inferior esquerdo do pilar na planta):
- à esquerda da planta, alinhados com ela: SEÇÃO A-A (linha diante da face, peças N1 e o pilar cortado) e SEÇÃO B-B
  (linha ao lado do pilar, peça N2), giradas como no modelo (face superior da laje à esquerda); para cada cobrinha,
  o ferro inteligente com os comprimentos entre eixos (NOTA 3) e o desenho pelas faces, com as barras nos vértices
  e as cotas entre faces (NOTA 4);
- VISTA EM PLANTA (ARM. PUNÇÃO): cobrinhas (blocos, bitola real, trechos de cima tracejados), montagem, cotas,
  "PENTE MESTRE P/ LOCAÇÃO", marcas dos cortes e, embaixo, as barras de montagem identificadas;
- VISTA EM PLANTA (COLAPSO PROGRESSIVO), DET. PLANTA (gabarito dos pentes mestres, 1:25), NOTAS IMPORTANTES e
  título (nome, "Nx" e dimensões).
"""
import math

from .folha import (Folha, H_CHAMADA, H_ESCALA, H_LETRA, H_NOTA, H_NOTAS_TIT, H_NX, H_TITULO, H_VISTA,
                    contorno_barra, quebra)

NOTAS = [
    "CADA VÉRTICE DA ARM. DE PUNÇÃO DEVERÁ CONTER UMA BARRA SUPERIOR CONFORME ARMADURA NEGATIVA. CASO A ARMADURA "
    "NÃO COINCIDA COM O VÉRTICE UTILIZAR BARRAS ADICIONAIS DA MESMA BITOLA DA ARMADURA SUPERIOR (NEGATIVA).",
    "LOCAR NA FORMA A POSIÇÃO DO PINO MESTRE DE PUNÇÃO CONFORME SEÇÃO A-A.",
    "ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS ENTRE EIXOS DAS BARRAS.",
    "ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS DE DOBRAS ENTRE FACES DAS BARRAS.",
]


def _quebrar(txt, n):
    linhas, atual = [], ""
    for p in txt.split():
        if atual and len(atual) + 1 + len(p) > n:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    return linhas + [atual] if atual else linhas


def _fmt(v):
    return f"{v:g}".replace(".", ",")


class Prancha:
    def __init__(self, res):
        if res["cobrinha"]["direcao"] != "y":
            raise NotImplementedError("prancha com as cobrinhas em x: ainda não implementada (E2)")
        self.r, self.p, self.c = res, res["p"], res["cobrinha"]
        p = self.p
        self.f = Folha(p["escala"])
        self.E = p["escala"]
        self.L, self.Lt = p["by"], p["bx"]
        self.h, self.cs, self.ci = p["h_laje"], p["c_sup"], p["c_inf"]
        self.fc, self.fm, self.fcol = p["cob_bitola"] / 10, p["mont_bitola"] / 10, p["col_bitola"] / 10
        self.f1, self.f2 = p["neg_bitola_ext"] / 10, p["neg_bitola_int"] / 10
        self.H = self.c["altura_eixo"]
        self.pos = {}
        for fe in res["ferros"]:
            self.pos[(fe["tipo"], fe.get("subtipo") or fe.get("direcao"))] = fe
        pc = self.c["pecas"]
        self.ext = next(x for x in pc if x["tipo"] == "extremidade" and x["ini"] == 0)
        self.cont = next((x for x in pc if x["tipo"] == "continua"), None)
        self.u0 = min(u for x in pc for u, _ in x["pontos"])
        self.u1 = max(u for x in pc for u, _ in x["pontos"])
        lin = self.c["linhas"]
        self.t0 = lin[0] - p["mont_ext"]
        self.t1 = lin[-1] + p["mont_ext"]
        # corte A-A na linha diante da face mais perto do meio (afasta as marcas A e B na planta)
        self.t_frente = min((t for t in lin if 0 < t < self.Lt), key=lambda t: abs(t - self.Lt / 2))
        self.t_lado = max(t for t in lin if t < 0)
        self.y_tit = max(self.u1 + 3.6 * self.E, self.L + p["col_ext"] + 2.2 * self.E)

    # ------------------------------------------------------------------ utilidades
    def _texto_largura(self, txt, h_papel):
        return len(txt) * h_papel * self.E * 0.92

    def _chamada(self, n, pts, seta=True):
        """Linha de chamada com flecha na ponta (polilinha comum, como o DimNote grava)."""
        f, E = self.f, self.E
        f.poli(n, pts)
        if seta:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            a = math.atan2(y2 - y1, x2 - x1)
            L = 0.22 * E
            for da in (0.35, -0.35):
                f.linha(n, (x2, y2), (x2 - L * math.cos(a + da), y2 - L * math.sin(a + da)))

    def _marca_corte(self, x, y, sentido_y, letra, olhar=-1):
        """Marca de corte do modelo R01: haste ao longo da linha de corte, bandeira triangular hachurada apontando
        para o lado de onde se olha (olhar = -1: para -x) e a letra."""
        f, E = self.f, self.E
        L, b = 0.9 * E, 0.41 * E
        y2 = y + sentido_y * L
        f.linha(253, (x, y), (x, y2))
        tri = [(x, y2), (x + olhar * b, y2 - sentido_y * b / 2), (x, y2 - sentido_y * b)]
        f.poli(253, tri, fechar=True)
        for i in range(1, 12):
            k = i / 12
            xx = x + olhar * b * k
            f.linha(253, (xx, y2 - sentido_y * b * k / 2), (xx, y2 - sentido_y * b * (1 - k / 2)))
        f.texto(253, x + olhar * (b + 0.15 * E) - (0.35 * E if olhar < 0 else 0), y2 - sentido_y * b,
                H_LETRA, letra)

    # ------------------------------------------------------------------ cortes
    def _xy_corte(self, Xb):
        return lambda u, z: (Xb - z, u)

    def _barras_vertices(self, pc, T, nivel_sup=254, nivel_inf=243):
        """Barras nos vértices: negativa dentro das dobras de cima, montagem dentro das dobras de baixo."""
        f = self.f
        r1, rm = self.f1 / 2, self.fm / 2
        z_sup = self.h - self.cs - self.fc - r1
        z_inf = self.ci + self.fc + rm
        pts = pc["pontos"]
        for i in range(1, len(pts) - 1, 2):
            u = pts[i][0]
            for j in (i - 1, i + 2):                      # vizinhos horizontais da perna
                if 0 <= j < len(pts):
                    lado = 1 if pts[j][0] > u else -1
                    nivel = pts[j][1] if j < i else pts[i + 1][1]
                    if nivel == "sup":
                        f.circ(nivel_sup, *T(u + lado * (self.fc / 2 + r1), z_sup), r1)
                    else:
                        f.circ(nivel_inf, *T(u + lado * (self.fc / 2 + rm), z_inf), rm)

    def _cobrinha_corte(self, pc, T):
        f = self.f
        z = {"sup": self.h - self.cs - self.fc / 2, "inf": self.ci + self.fc / 2}
        eixo = [T(u, z[n]) for u, n in pc["pontos"]]
        cont = contorno_barra(eixo, self.fc)
        f.poli(224, cont)
        f.poli(233, cont)
        f.poli(0, eixo, s=3)

    def corte(self, Xb, linha, letra, nota1=False):
        """Seção ao longo de uma linha de cobrinhas. Xb = x da face inferior da laje (a superior fica à esquerda)."""
        f, E, h, L = self.f, self.E, self.h, self.L
        T = self._xy_corte(Xb)
        p = self.p
        sobre = 0 < linha < self.Lt
        ua, ub = self.u0 - 1.2 * E, self.u1 + 1.2 * E
        zp = 1.3 * E
        amp = 0.67 * E
        if sobre:                                         # pilar cortado
            uz = [(ua, 0), (0, 0), (0, -zp)] + quebra((0, -zp), (L, -zp), amp)[1:-1] + [(L, -zp), (L, 0), (ub, 0)]
            uz += quebra((ub, 0), (ub, h), amp * 0.45)[1:-1] + [(ub, h), (L, h), (L, h + zp)]
            uz += quebra((L, h + zp), (0, h + zp), amp)[1:-1] + [(0, h + zp), (0, h), (ua, h)]
            uz += quebra((ua, h), (ua, 0), amp * 0.45)[1:-1]
        else:                                             # pilar além do corte, tracejado
            uz = [(ua, 0), (ub, 0)] + quebra((ub, 0), (ub, h), amp * 0.45)[1:-1] + [(ub, h), (ua, h)]
            uz += quebra((ua, h), (ua, 0), amp * 0.45)[1:-1]
            f.poli(203, [T(0, -zp), T(L, -zp), T(L, h + zp), T(0, h + zp)], s=1, fechar=True)
        contorno = [T(u, z) for u, z in uz]
        f.poli(0, contorno, fechar=True)
        f.poli(240, contorno, fechar=True)
        # barras de flexão de referência (traço-ponto): 2ª camada da negativa e positiva sobre a montagem
        for z1, z2 in ((h - self.cs - self.fc - self.f1 - self.f2, h - self.cs - self.fc - self.f1),
                       (self.ci + self.fc + self.fm, self.ci + self.fc + 2 * self.fm)):
            for zz in (z1, z2):
                f.linha(0, T(ua + 0.3 * E, zz), T(ub - 0.3 * E, zz), s=3)
        pecas = [x for x in self.c["pecas"] if abs(x["linha"] - linha) < 1e-6]
        for pc in pecas:
            self._cobrinha_corte(pc, T)
            self._barras_vertices(pc, T)
        # colapso: as barras em x cruzam o corte (círculos); as em y, só no corte diante da face (linha, como o modelo)
        rcol = self.fcol / 2
        col_x, col_y = self.r["colapso"]
        if col_x["ini"] <= linha <= col_x["fim"]:
            for u in col_x["pos"]:
                f.circ(245, *T(u, self.ci + self.fc + rcol), rcol)
        if sobre:
            baixo = sorted((min(a, b), max(a, b)) for x in pecas for a, b, n in x["trechos"] if n == "inf")
            livres, u = [], col_y["ini"]
            for a, b in baixo:
                if a > u:
                    livres.append((u, a))
                u = max(u, b)
            livres.append((u, col_y["fim"]))
            for a, b in livres:
                if b - a > 0.5:
                    f.linha(245, T(a, self.ci), T(b, self.ci))
                    f.linha(245, T(a, self.ci + self.fcol), T(b, self.ci + self.fcol))
        f.texto(221, Xb - h - 0.35 * E, L + (self.u1 - L) * 0.25, H_CHAMADA, "TOPO LAJE", a=90)
        f.texto(226, Xb - h - zp, self.y_tit, H_VISTA, f"SEÇÃO {letra}-{letra}")
        f.texto(0, Xb - h - zp + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{self.E:g}")
        if nota1:
            bx = Xb - h - zp - 0.6 * E
            meio = L / 2
            f.retangulo(225, bx - 0.63 * E, meio - 0.97 * E, bx, meio + 0.97 * E)
            f.texto(227, bx - 0.2 * E, meio - 0.55 * E, H_CHAMADA, "NOTA 1", a=90)
            r1 = self.f1 / 2
            for c_ in [q for q in self.f.prims if q["t"] == "Circulo" and q["n"] == 254 and abs(q["r"] - r1) < 1e-9
                       and Xb - h - 1 <= q["x"] <= Xb]:
                self.f.linha(210, (bx, meio), (c_["x"] - r1 * 0.7, c_["y"]))
        return Xb - h - zp, Xb + zp                       # extensão em x

    # ------------------------------------------------------------------ detalhes das cobrinhas
    def detalhe_eixos(self, X, pc, fe):
        """Ferro inteligente com os comprimentos entre eixos (o TQS escreve os trechos). X = eixo do trecho de baixo."""
        f, E, H = self.f, self.E, self.H
        pts = [(-H if n == "sup" else 0.0, u) for u, n in pc["pontos"]]
        us = [u for u, _ in pc["pontos"]]
        f.ferro(dict(tipo="gen", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], pontos=pts,
                     ins=[dict(x=X, y=0.0, ang=0.0, nivel=242, ident=1, idobra=1, ipatas=0)],
                     texto=dict(x=X + 0.75 * E, y=min(us) + 0.15 * E, ang=90.0)))
        # cotas em relação às faces do pilar
        marcos = sorted({min(us), max(us)} | {u for u in (-self.p["cob_s0"], 0.0, self.L, self.L + self.p["cob_s0"])
                                               if min(us) <= u <= max(us)})
        xc = X - H - 0.9 * E
        for a, b in zip(marcos, marcos[1:]):
            f.cota((X - H, a), (X - H, b), (xc, a), modo="v")
        f.texto(221, X + 0.2 * E, max(us) + 0.5 * E, H_CHAMADA, "NOTA 3")
        return xc - 0.6 * E, X + 1.4 * E

    def detalhe_faces(self, X, pc):
        """A cobrinha pelas faces, com as barras nos vértices e as cotas entre faces. X = eixo do trecho de baixo."""
        f, E, H, fc = self.f, self.E, self.H, self.fc
        z_inf = self.ci + fc / 2                          # o eixo de baixo fica em X
        T = lambda u, z: (X - (z - z_inf), u)             # noqa: E731
        self._cobrinha_corte(pc, T)
        self._barras_vertices(pc, T)
        x_sup = X - H - fc / 2                            # face externa de cima
        x_inf = X + fc / 2                                # face externa de baixo
        pts = pc["pontos"]
        for nivel, xf, xc in (("sup", x_sup, x_sup - 0.7 * E), ("inf", x_inf, x_inf + 0.7 * E)):
            marcas = []
            for a, b, n in pc["trechos"]:
                if n != nivel:
                    continue
                lo, hi = min(a, b), max(a, b)
                pernas = pc["pernas"]
                lo_f = lo - fc / 2 if any(abs(lo - q) < 1e-6 for q in pernas) else lo
                hi_f = hi + fc / 2 if any(abs(hi - q) < 1e-6 for q in pernas) else hi
                marcas += [lo_f, hi_f]
            marcas = sorted(set(round(m, 4) for m in marcas))
            for a, b in zip(marcas, marcas[1:]):
                f.cota((xf, a), (xf, b), (xc, a), modo="v")
        u_min = min(u for u, _ in pts)
        perna = pc["pernas"][0]
        f.cota((x_sup, perna), (x_inf, perna), (x_sup, u_min - 0.9 * E), modo="h")
        f.texto(221, X + 0.2 * E, max(u for u, _ in pts) + 0.5 * E, H_CHAMADA, "NOTA 4")
        return x_sup - 1.1 * E, x_inf + 1.1 * E

    # ------------------------------------------------------------------ planta
    def _blocos_cobrinha(self):
        f, fc = self.f, self.fc
        nomes = {}
        for chave, pc in (("ext", self.ext), ("cont", self.cont)):
            if pc is None:
                continue
            fe = self.pos[("cobrinha", "extremidade" if chave == "ext" else "continua")]
            nome = f"COBRINHA N{fe['pos']} {_fmt(self.p['cob_bitola'])}"
            b = f.novo_bloco(nome)
            for a, z, nivel in pc["trechos"]:
                for dx in (-fc / 2, fc / 2):
                    b.linha(241, (dx, a), (dx, z), s=1 if nivel == "sup" else 0)
            for u in pc["pernas"]:
                b.circ(241, 0.0, u, fc / 2)
                b.circ(233, 0.0, u, fc / 2)
            nomes[chave] = nome
        return nomes

    def planta(self):
        f, E, p, c = self.f, self.E, self.p, self.c
        L, Lt, s0 = self.L, self.Lt, p["cob_s0"]
        f.retangulo(227, 0, 0, Lt, L)
        f.linha(204, (Lt / 2, -0.6 * E), (Lt / 2, L + 0.6 * E), s=3)
        f.linha(204, (-0.6 * E, L / 2), (Lt + 0.6 * E, L / 2), s=3)
        nomes = self._blocos_cobrinha()
        for pc in c["pecas"]:
            if pc["tipo"] == "extremidade":
                inferior = pc["ini"] == 0
                if inferior:
                    f.bloco(nomes["ext"], pc["linha"], 0.0, n=241)
                else:
                    f.bloco(nomes["ext"], pc["linha"], L, sy=-1.0, n=241)
            else:
                f.bloco(nomes["cont"], pc["linha"], 0.0, n=241)
        for b in c["montagem"]:
            f.linha(243, (b["ini"], b["pos"]), (b["fim"], b["pos"]))
        # cotas: linhas de cobrinha (em cima), fileiras diante das faces (à direita) e ao lado do pilar (à esquerda)
        lin = c["linhas"]
        yc = self.u1 + 0.9 * E
        for a, b in zip(lin, lin[1:]):
            f.cota((a, self.u1), (b, self.u1), (a, yc), modo="h")
        fil = sorted(set(self.ext["pernas"]) | {L - u for u in self.ext["pernas"]} | {0.0, L})
        xc = lin[-1] + 0.9 * E
        for a, b in zip(fil, fil[1:]):
            f.cota((lin[-1], a), (lin[-1], b), (xc, a), modo="v")
        if self.cont:
            lado = [u for u in self.cont["pernas"] if -s0 - 1e-6 <= u <= L + s0 + 1e-6]
            xl = lin[0] - 0.9 * E
            for a, b in zip(lado, lado[1:]):
                f.cota((lin[0], a), (lin[0], b), (xl, a), modo="v")
        f.cota((-s0, L), (0, L), (-s0, L + s0 / 2), modo="h")
        f.cota((Lt, L), (Lt, L + s0), (Lt + s0 / 2, L), modo="v")
        # pente mestre (entre a cadeia de cotas e o título) e marcas dos cortes (além das cotas)
        tx, ty = self.t0 + 0.2 * E, self.u1 + 2.3 * E
        f.texto(253, tx, ty, H_CHAMADA, "PENTE MESTRE")
        f.texto(253, tx + 0.5 * E, ty - 0.45 * E, H_CHAMADA, "P/ LOCAÇÃO")
        larg = self._texto_largura("PENTE MESTRE", H_CHAMADA)
        self._chamada(253, [(tx, ty - 0.1 * E), (tx + larg + 0.3 * E, ty - 0.1 * E), (-s0, self.u1 + 0.05 * E)])
        for t, letra in ((self.t_frente, "A"), (self.t_lado, "B")):
            self._marca_corte(t, self.u1 + 1.6 * E, 1, letra)
            self._marca_corte(t, self.u0 - 0.4 * E, -1, letra)
        f.texto(226, self.t0, self.y_tit, H_VISTA, "VISTA EM PLANTA (ARM. PUNÇÃO)")
        f.texto(0, self.t0 + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        # barras de montagem identificadas, embaixo da planta (abaixo das marcas dos cortes)
        y = self.u0 - 2.9 * E
        for sub in ("continua", "lateral"):
            fe = self.pos.get(("montagem", sub))
            if not fe:
                continue
            f.ferro(dict(tipo="reto", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], comp=fe["comp"],
                         ins=[dict(x=self.t0, y=y, ang=0.0, nivel=244, ipatas=1)]))
            if sub == "continua":
                marcos = [self.t0, lin[0], lin[-1], self.t1]
            else:
                marcos = [self.t0, lin[0], 0.0]
            for a, b in zip(marcos, marcos[1:]):
                f.cota((a, y), (b, y), (a, y + 0.6 * E), modo="h")
            y -= 2.2 * E
        self.y_min_planta = y

    # ------------------------------------------------------------------ colapso
    def colapso(self, X0):
        f, E, p = self.f, self.E, self.p
        L, Lt, ext = self.L, self.Lt, p["col_ext"]
        f.retangulo(203, X0, 0, X0 + Lt, L, s=1)
        f.retangulo(240, X0, 0, X0 + Lt, L)
        col_x, col_y = self.r["colapso"]
        for v in col_x["pos"]:
            f.linha(245, (X0 + col_x["ini"], v), (X0 + col_x["fim"], v))
        for v in col_y["pos"]:
            f.linha(245, (X0 + v, col_y["ini"]), (X0 + v, col_y["fim"]))
        f.texto(226, X0 - ext, self.y_tit, H_VISTA, "VISTA EM PLANTA (COLAPSO PROGRESSIVO)")
        f.texto(0, X0 - ext + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        fx = self.pos[("colapso", "x")]
        fy = self.pos[("colapso", "y")]
        y5 = -ext - 1.6 * E
        f.ferro(dict(tipo="reto", mark=fx["pos"], quant=fx["quant"], bitola=fx["bitola"], comp=fx["comp"],
                     ins=[dict(x=X0 + col_x["ini"], y=y5, ang=0.0, nivel=246, ipatas=1)]))
        f.cota((X0 + Lt, y5), (X0 + Lt + ext, y5), (X0 + Lt, y5 + 0.6 * E), modo="h")
        f.texto(0, X0 - 0.2 * E, y5 - 1.0 * E, H_NOTA, "(barras contra colapso progressivo)")
        f.texto(226, X0 + 0.3 * E, y5 - 1.55 * E, H_NOTA, "ARMADURA DA FACE INFERIOR")
        x6 = X0 + Lt + ext + 1.6 * E
        f.ferro(dict(tipo="reto", mark=fy["pos"], quant=fy["quant"], bitola=fy["bitola"], comp=fy["comp"],
                     ins=[dict(x=x6, y=col_y["ini"], ang=90.0, nivel=246, ipatas=1)]))
        f.cota((x6, L), (x6, L + ext), (x6 - 0.6 * E, L), modo="v")
        f.texto(0, x6 + 1.0 * E, -0.2 * E, H_NOTA, "(barras contra colapso progressivo)", a=90)
        f.texto(226, x6 + 1.55 * E, 0.3 * E, H_NOTA, "ARMADURA DA FACE INFERIOR", a=90)
        return x6 + 2.2 * E

    # ------------------------------------------------------------------ gabarito, notas, título
    def gabarito(self, X, Y):
        """DET. PLANTA - gabarito dos pentes mestres, a 1:25 (cotas com os valores reais)."""
        f, E, p = self.f, self.E, self.p
        k = E / 25.0
        Lt, L, s0 = self.Lt * k, self.L * k, p["cob_s0"] * k
        x0, y0 = X + 1.2 * E, Y - 2.7 * E - L - s0          # títulos, depois as cotas, depois o desenho
        f.retangulo(203, x0, y0, x0 + Lt, y0 + L, s=1)
        f.retangulo(240, x0, y0, x0 + Lt, y0 + L)
        f.retangulo(233, x0 - s0, y0 - s0, x0 + Lt + s0, y0 + L + s0)
        yc = y0 + L + s0 + 0.6 * E
        for a, b in ((x0 - s0, x0), (x0, x0 + Lt), (x0 + Lt, x0 + Lt + s0)):
            f.cota((a, y0 + L + s0), (b, y0 + L + s0), (a, yc), modo="h", fator=1 / k)
        xc = x0 + Lt + s0 + 0.6 * E
        for a, b in ((y0 - s0, y0), (y0, y0 + L), (y0 + L, y0 + L + s0)):
            f.cota((x0 + Lt + s0, a), (x0 + Lt + s0, b), (xc, a), modo="v", fator=1 / k)
        tx = xc + 1.0 * E
        f.texto(253, tx, y0 + L * 0.5 + 0.3 * E, H_CHAMADA, "NOTA 2")
        self._chamada(253, [(tx + 2.0 * E, y0 + L * 0.5 + 0.15 * E), (tx - 0.1 * E, y0 + L * 0.5 + 0.15 * E),
                            (x0 + Lt + s0, y0 + L * 0.5)])
        f.texto(220, X + 0.3 * E, Y - 0.6 * E, H_VISTA, "DET. PLANTA")
        f.texto(220, X + 0.3 * E, Y - 1.05 * E, 0.20, "GABARITO PENTES MESTRES")
        f.texto(0, X + 0.3 * E, Y - 1.4 * E, H_ESCALA, "ESCALA 1:25")
        x1, y1 = tx + 3.2 * E, y0 - s0 - 0.6 * E
        f.retangulo(0, X, y1, x1, Y)
        return x1, y1

    def notas(self, X, Y):
        f, E = self.f, self.E
        dy = 0.5 * E
        largura = 52                                   # caracteres por linha (o 1º traz 8 espaços para o "NOTA n:")
        linhas = []
        for i, nota in enumerate(NOTAS, 1):
            resto = nota
            primeira = _quebrar(resto, largura - 8)[0]
            linhas.append((i, "        " + primeira))
            resto = resto[len(primeira):].strip()
            for txt in (_quebrar(resto, largura) if resto else []):
                linhas.append((None, txt))
        W = largura * H_NOTA * E + 0.4 * E             # no TQS, cada caractere ocupa a largura da altura
        f.retangulo(240, X, Y - 0.8 * E, X + W, Y)
        f.texto(220, X + 0.2 * E, Y - 0.6 * E, H_NOTAS_TIT, "NOTAS IMPORTANTES")
        y = Y - 0.8 * E
        for i, txt in linhas:
            y -= dy
            f.texto(227, X + 0.2 * E, y + 0.12 * E, H_NOTA, txt)
            if i:
                f.texto(242, X + 0.2 * E, y + 0.12 * E, H_NOTA, f"NOTA {i}:")
            f.linha(227, (X, y), (X + W, y))
        f.linha(0, (X, Y - 0.8 * E), (X, y))
        f.linha(0, (X + W, Y - 0.8 * E), (X + W, y))
        return X + W, y

    def titulo(self, X, Y):
        f, p = self.f, self.p
        f.texto(222, X, Y, H_TITULO, p["titulo"])
        f.texto(202, X, Y - 0.75 * self.E, H_NX, f"{p['repeticoes']}X")
        f.texto(220, X, Y - 1.5 * self.E, H_NX, f"({_fmt(p['bx'])}x{_fmt(p['by'])})")

    # ------------------------------------------------------------------ montagem da folha
    def montar(self):
        f, E = self.f, self.E
        self.planta()
        x = self.t0 - 1.2 * E
        # à esquerda da planta: detalhes pelas faces e entre eixos (N2 e N1) e os cortes B-B e A-A
        fe_ext = self.pos[("cobrinha", "extremidade")]
        fe_cont = self.pos.get(("cobrinha", "continua"))
        for pc, fe in ((self.cont, fe_cont), (self.ext, fe_ext)):
            if not pc:
                continue
            esq, _ = self.detalhe_faces(x - 1.1 * E - self.fc / 2, pc)
            x = esq - 0.4 * E
            esq, _ = self.detalhe_eixos(x - 1.4 * E, pc, fe)
            x = esq - 0.6 * E
        zp = 1.3 * E
        esq, _ = self.corte(x - zp, self.t_lado, "B")
        x = esq - 1.0 * E
        esq, _ = self.corte(x - zp, self.t_frente, "A", nota1=True)
        x_esq = esq - 1.6 * E
        # linhas das faces do pilar, dos cortes até a planta (como no modelo)
        for u in (0.0, self.L):
            f.linha(204, (x_esq + 1.5 * E, u), (0.0, u), s=3)
        # à direita: colapso; em cima: título, gabarito e notas
        x_dir = self.colapso(self.t1 + 1.6 * E + self.p["col_ext"])
        y_top = self.y_tit + 1.2 * E
        xg, yg = self.gabarito(x_dir - 13.5 * E, y_top + 9.0 * E)
        self.notas(x_dir - 13.5 * E - 15.0 * E, y_top + 9.0 * E)
        self.titulo(x_esq + 0.5 * E, y_top + 8.0 * E)
        x1, y1, x2, y2 = f.extensao()
        m = 0.8 * E
        f.retangulo(0, x1 - m, y1 - m, max(x2, xg) + m, max(y2, y_top + 9.0 * E) + m)
        return f


def montar(res):
    """Folha da prancha da cobrinha a partir do resultado de nucleo.detalhe.detalhar."""
    return Prancha(res).montar()
