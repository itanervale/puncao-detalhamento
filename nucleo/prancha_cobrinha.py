# -*- coding: utf-8 -*-
"""
Prancha da cobrinha (pilar interno) em primitivas, no padrão do desenho de referência PUN_P02-R01
(PADRAO_desenho.md), com as regras do usuário de 03/11/2026 (PLANO, E1). Sem o TQS.

As vistas são desenhadas em coordenadas locais e levadas para a prancha conforme a direção das cobrinhas:
- planta: (t, u), com t transversal (as linhas de cobrinha) e u ao longo da cobrinha; Pl(t, u) dá o ponto;
- cortes e detalhes: (u, z), com z na altura da laje; T(u, z) dá o ponto.

Cobrinhas em y (verticais na prancha, como no modelo): as seções ficam à esquerda da planta, giradas (face superior
da laje à esquerda) e alinhadas com ela: SEÇÃO A-A (linha diante da face, peças N1 e o pilar cortado) e SEÇÃO B-B
(linha ao lado do pilar, peça N2); para cada cobrinha, o ferro inteligente com os comprimentos entre eixos (NOTA 3) e
o desenho pelas faces, com as barras nos vértices e as cotas entre faces (NOTA 4).

Cobrinhas em x (horizontais): as mesmas vistas ficam embaixo da planta, alinhadas com ela e com a face superior para
cima, empilhadas na mesma ordem (a mais perto da planta é o detalhe pelas faces da peça inteira).

Nas duas: VISTA EM PLANTA (ARM. PUNÇÃO) com as cobrinhas (blocos, bitola real, trechos de cima tracejados), a
montagem, as cotas, "PENTE MESTRE P/ LOCAÇÃO", as marcas dos cortes e as barras de montagem identificadas; VISTA EM
PLANTA (COLAPSO PROGRESSIVO), DET. PLANTA (gabarito dos pentes mestres, 1:25), NOTAS IMPORTANTES e título.
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
        self.r, self.p, self.c = res, res["p"], res["cobrinha"]
        p = self.p
        self.vert = self.c["direcao"] == "y"              # cobrinhas na vertical da prancha (o modelo)
        self.f = Folha(p["escala"])
        self.E = p["escala"]
        self.bx, self.by = p["bx"], p["by"]
        # L: dimensão do pilar ao longo da cobrinha; Lt: na direção transversal (das linhas)
        self.L, self.Lt = (p["by"], p["bx"]) if self.vert else (p["bx"], p["by"])
        self.a_u = 90.0 if self.vert else 0.0             # ângulo dos textos que correm ao longo de u nos cortes
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
        # linha dos títulos (em x, refeita depois da planta, pela extensão dela)
        self.y_tit = max(self.u1 + 3.6 * self.E, self.by + p["col_ext"] + 2.2 * self.E)

    # ------------------------------------------------------------------ coordenadas locais
    def Pl(self, t, u):
        """Planta: ponto (t transversal, u ao longo da cobrinha) na prancha."""
        return (t, u) if self.vert else (u, t)

    def _T(self, B, z0=0.0):
        """Cortes e detalhes: (u ao longo da cobrinha, z na altura) na prancha. B = posição de z = z0: em y, o x da
        face inferior (a face superior fica à esquerda); em x, o y dela (a face superior fica em cima)."""
        if self.vert:
            return lambda u, z: (B - (z - z0), u)
        return lambda u, z: (u, B + (z - z0))

    def _modo(self, eixo):
        """Modo da cota que mede ao longo de u ("u") ou na direção transversal / da altura ("t")."""
        if eixo == "u":
            return "v" if self.vert else "h"
        return "h" if self.vert else "v"

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

    def _marca_corte(self, t, u, sentido, letra):
        """Marca de corte do modelo R01: haste ao longo da linha de corte (sentido +1 ou -1 em u), bandeira
        triangular hachurada apontando para o lado onde as seções estão desenhadas (-t) e a letra."""
        f, E = self.f, self.E
        L, b = 0.9 * E, 0.41 * E
        x, y = self.Pl(t, u)
        d = self.Pl(0.0, float(sentido))                  # direção da haste
        g = self.Pl(-1.0, 0.0)                            # direção da bandeira
        x2, y2 = x + d[0] * L, y + d[1] * L
        f.linha(253, (x, y), (x2, y2))
        tri = [(x2, y2), (x2 + g[0] * b - d[0] * b / 2, y2 + g[1] * b - d[1] * b / 2),
               (x2 - d[0] * b, y2 - d[1] * b)]
        f.poli(253, tri, fechar=True)
        for i in range(1, 12):
            k = i / 12
            ax, ay = x2 + g[0] * b * k, y2 + g[1] * b * k
            f.linha(253, (ax - d[0] * b * k / 2, ay - d[1] * b * k / 2),
                    (ax - d[0] * b * (1 - k / 2), ay - d[1] * b * (1 - k / 2)))
        f.texto(253, x2 + g[0] * (b + 0.15 * E) - d[0] * b + min(0.0, g[0]) * 0.35 * E,
                y2 + g[1] * (b + 0.15 * E) - d[1] * b + min(0.0, g[1]) * 0.35 * E, H_LETRA, letra)

    # ------------------------------------------------------------------ cortes
    def _barras_vertices(self, pc, T, nivel_sup=254, nivel_inf=243):
        """Barras nos vértices: negativa dentro das dobras de cima, montagem dentro das dobras de baixo. Devolve as
        barras de cima, em coordenadas locais (u, z), para as chamadas da NOTA 1."""
        f = self.f
        r1, rm = self.f1 / 2, self.fm / 2
        z_sup = self.h - self.cs - self.fc - r1
        z_inf = self.ci + self.fc + rm
        pts = pc["pontos"]
        sup = []
        for i in range(1, len(pts) - 1, 2):
            u = pts[i][0]
            for j in (i - 1, i + 2):                      # vizinhos horizontais da perna
                if 0 <= j < len(pts):
                    lado = 1 if pts[j][0] > u else -1
                    nivel = pts[j][1] if j < i else pts[i + 1][1]
                    if nivel == "sup":
                        uc = u + lado * (self.fc / 2 + r1)
                        f.circ(nivel_sup, *T(uc, z_sup), r1)
                        sup.append((uc, z_sup))
                    else:
                        f.circ(nivel_inf, *T(u + lado * (self.fc / 2 + rm), z_inf), rm)
        return sup

    def _cobrinha_corte(self, pc, T):
        f = self.f
        z = {"sup": self.h - self.cs - self.fc / 2, "inf": self.ci + self.fc / 2}
        eixo = [T(u, z[n]) for u, n in pc["pontos"]]
        cont = contorno_barra(eixo, self.fc)
        f.poli(224, cont)
        f.poli(233, cont)
        f.poli(0, eixo, s=3)

    def corte(self, B, linha, letra, nota1=False):
        """Seção ao longo de uma linha de cobrinhas; B = posição da face inferior da laje (ver _T)."""
        f, E, h, L = self.f, self.E, self.h, self.L
        T = self._T(B)
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
        sup = []
        for pc in pecas:
            self._cobrinha_corte(pc, T)
            sup += self._barras_vertices(pc, T)
        # colapso: as barras transversais à cobrinha cruzam o corte (círculos); as paralelas, só no corte diante da
        # face (linha, como o modelo)
        rcol = self.fcol / 2
        col_x, col_y = self.r["colapso"]
        transv, longit = (col_x, col_y) if self.vert else (col_y, col_x)
        if transv["ini"] <= linha <= transv["fim"]:
            for u in transv["pos"]:
                f.circ(245, *T(u, self.ci + self.fc + rcol), rcol)
        if sobre:
            baixo = sorted((min(a, b), max(a, b)) for x in pecas for a, b, n in x["trechos"] if n == "inf")
            livres, u = [], longit["ini"]
            for a, b in baixo:
                if a > u:
                    livres.append((u, a))
                u = max(u, b)
            livres.append((u, longit["fim"]))
            for a, b in livres:
                if b - a > 0.5:
                    f.linha(245, T(a, self.ci), T(b, self.ci))
                    f.linha(245, T(a, self.ci + self.fcol), T(b, self.ci + self.fcol))
        f.texto(221, *T(L + (self.u1 - L) * 0.25, h + 0.35 * E), H_CHAMADA, "TOPO LAJE", a=self.a_u)
        if self.vert:
            tx, ty = B - h - zp, self.y_tit
        else:
            tx, ty = ua, B + h + zp + 0.9 * E
        f.texto(226, tx, ty, H_VISTA, f"SEÇÃO {letra}-{letra}")
        f.texto(0, tx + 0.1 * E, ty - 0.45 * E, H_ESCALA, f"ESCALA 1:{self.E:g}")
        if nota1:
            meio = L / 2
            z1 = h + zp + 0.6 * E                         # caixa da NOTA 1, além da face superior
            (xa, ya), (xb, yb) = T(meio - 0.97 * E, z1), T(meio + 0.97 * E, z1 + 0.63 * E)
            f.retangulo(225, min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb))
            f.texto(227, *T(meio - 0.55 * E, z1 + 0.2 * E), H_CHAMADA, "NOTA 1", a=self.a_u)
            r1 = self.f1 / 2
            for uc, zc in sup:
                f.linha(210, T(meio, z1), T(uc, zc + r1 * 0.7))
        return (B - h - zp, B + zp) if self.vert else (B - zp, B + h + zp)

    # ------------------------------------------------------------------ detalhes das cobrinhas
    def detalhe_eixos(self, B, pc, fe):
        """Ferro inteligente com os comprimentos entre eixos (o TQS escreve os trechos). B = eixo do trecho de baixo."""
        f, E, H = self.f, self.E, self.H
        T = self._T(B)
        if self.vert:
            pts = [(-H if n == "sup" else 0.0, u) for u, n in pc["pontos"]]
        else:
            pts = [(u, H if n == "sup" else 0.0) for u, n in pc["pontos"]]
        us = [u for u, _ in pc["pontos"]]
        xi, yi = T(0.0, 0.0)
        tx, ty = T(min(us) + 0.15 * E, -0.75 * E)
        f.ferro(dict(tipo="gen", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], pontos=pts,
                     ins=[dict(x=xi, y=yi, ang=0.0, nivel=242, ident=1, idobra=1, ipatas=0)],
                     texto=dict(x=tx, y=ty, ang=self.a_u)))
        # cotas em relação às faces do pilar
        marcos = sorted({min(us), max(us)} | {u for u in (-self.p["cob_s0"], 0.0, self.L, self.L + self.p["cob_s0"])
                                               if min(us) <= u <= max(us)})
        for a, b in zip(marcos, marcos[1:]):
            f.cota(T(a, H), T(b, H), T(a, H + 0.9 * E), modo=self._modo("u"))
        f.texto(221, *T(max(us) + 0.5 * E, -0.2 * E), H_CHAMADA, "NOTA 3")
        return (B - H - 1.5 * E, B + 1.4 * E) if self.vert else (B - 1.4 * E, B + H + 1.5 * E)

    def detalhe_faces(self, B, pc):
        """A cobrinha pelas faces, com as barras nos vértices e as cotas entre faces. B = eixo do trecho de baixo."""
        f, E, H, fc = self.f, self.E, self.H, self.fc
        z_inf = self.ci + fc / 2                          # o eixo de baixo fica em B
        T = self._T(B, z_inf)
        self._cobrinha_corte(pc, T)
        self._barras_vertices(pc, T)
        zs = z_inf + H + fc / 2                           # face externa de cima
        zi = z_inf - fc / 2                               # face externa de baixo
        pts = pc["pontos"]
        for nivel, zf, zc in (("sup", zs, zs + 0.7 * E), ("inf", zi, zi - 0.7 * E)):
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
                f.cota(T(a, zf), T(b, zf), T(a, zc), modo=self._modo("u"))
        u_min = min(u for u, _ in pts)
        perna = pc["pernas"][0]
        f.cota(T(perna, zs), T(perna, zi), T(u_min - 0.9 * E, zs), modo=self._modo("t"))
        f.texto(221, *T(max(u for u, _ in pts) + 0.5 * E, z_inf - 0.2 * E), H_CHAMADA, "NOTA 4")
        if self.vert:
            return B - H - fc / 2 - 1.1 * E, B + fc / 2 + 1.1 * E
        return B - fc / 2 - 1.1 * E, B + H + fc / 2 + 1.1 * E

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

    def _inserir(self, nome, t, u, espelhar=False):
        """Bloco da cobrinha (desenhado ao longo do y local) na linha t, a partir de u; em x, girado de -90°."""
        x, y = self.Pl(t, u)
        if self.vert:
            if espelhar:
                self.f.bloco(nome, x, y, sy=-1.0, n=241)
            else:
                self.f.bloco(nome, x, y, n=241)
        else:
            self.f.bloco(nome, x, y, ang=-90.0, sy=-1.0 if espelhar else 1.0, n=241)

    def planta(self):
        f, E, p, c = self.f, self.E, self.p, self.c
        L, Lt, s0, Pl = self.L, self.Lt, p["cob_s0"], self.Pl
        bx, by = self.bx, self.by
        f.retangulo(227, 0, 0, bx, by)
        f.linha(204, (bx / 2, -0.6 * E), (bx / 2, by + 0.6 * E), s=3)
        f.linha(204, (-0.6 * E, by / 2), (bx + 0.6 * E, by / 2), s=3)
        nomes = self._blocos_cobrinha()
        for pc in c["pecas"]:
            if pc["tipo"] == "extremidade":
                if pc["ini"] == 0:
                    self._inserir(nomes["ext"], pc["linha"], 0.0)
                else:
                    self._inserir(nomes["ext"], pc["linha"], L, espelhar=True)
            else:
                self._inserir(nomes["cont"], pc["linha"], 0.0)
        for b in c["montagem"]:
            f.linha(243, Pl(b["ini"], b["pos"]), Pl(b["fim"], b["pos"]))
        # cotas: linhas de cobrinha (além da ponta u1), fileiras diante das faces (além da última linha) e ao lado
        # do pilar (antes da primeira linha)
        mt, mu = self._modo("t"), self._modo("u")
        lin = c["linhas"]
        yc = self.u1 + 0.9 * E
        for a, b in zip(lin, lin[1:]):
            f.cota(Pl(a, self.u1), Pl(b, self.u1), Pl(a, yc), modo=mt)
        fil = sorted(set(self.ext["pernas"]) | {L - u for u in self.ext["pernas"]} | {0.0, L})
        xc = lin[-1] + 0.9 * E
        for a, b in zip(fil, fil[1:]):
            f.cota(Pl(lin[-1], a), Pl(lin[-1], b), Pl(xc, a), modo=mu)
        if self.cont:
            lado = [u for u in self.cont["pernas"] if -s0 - 1e-6 <= u <= L + s0 + 1e-6]
            xl = lin[0] - 0.9 * E
            for a, b in zip(lado, lado[1:]):
                f.cota(Pl(lin[0], a), Pl(lin[0], b), Pl(xl, a), modo=mu)
        f.cota(Pl(-s0, L), Pl(0, L), Pl(-s0, L + s0 / 2), modo=mt)
        f.cota(Pl(Lt, L), Pl(Lt, L + s0), Pl(Lt + s0 / 2, L), modo=mu)
        # pente mestre (além da cadeia de cotas) e marcas dos cortes (além das cotas)
        tx, ty = Pl(self.t0 + 0.2 * E, self.u1 + 2.3 * E)
        f.texto(253, tx, ty, H_CHAMADA, "PENTE MESTRE")
        f.texto(253, tx + 0.5 * E, ty - 0.45 * E, H_CHAMADA, "P/ LOCAÇÃO")
        larg = self._texto_largura("PENTE MESTRE", H_CHAMADA)
        self._chamada(253, [(tx, ty - 0.1 * E), (tx + larg + 0.3 * E, ty - 0.1 * E), Pl(-s0, self.u1 + 0.05 * E)])
        for t, letra in ((self.t_frente, "A"), (self.t_lado, "B")):
            self._marca_corte(t, self.u1 + 1.6 * E, 1, letra)
            self._marca_corte(t, self.u0 - 0.4 * E, -1, letra)
        if self.vert:                                     # em x, o título vai depois, pela extensão da planta
            f.texto(226, self.t0, self.y_tit, H_VISTA, "VISTA EM PLANTA (ARM. PUNÇÃO)")
            f.texto(0, self.t0 + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        # barras de montagem identificadas, antes do início das cobrinhas (abaixo das marcas dos cortes)
        y = self.u0 - 2.9 * E
        for sub in ("continua", "lateral"):
            fe = self.pos.get(("montagem", sub))
            if not fe:
                continue
            xi, yi = Pl(self.t0, y)
            f.ferro(dict(tipo="reto", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], comp=fe["comp"],
                         ins=[dict(x=xi, y=yi, ang=0.0 if self.vert else 90.0, nivel=244, ipatas=1)]))
            if sub == "continua":
                marcos = [self.t0, lin[0], lin[-1], self.t1]
            else:
                marcos = [self.t0, lin[0], 0.0]
            for a, b in zip(marcos, marcos[1:]):
                f.cota(Pl(a, y), Pl(b, y), Pl(a, y + 0.6 * E), modo=mt)
            y -= 2.2 * E
        self.y_min_planta = y

    # ------------------------------------------------------------------ colapso
    def colapso(self, X0):
        f, E, p = self.f, self.E, self.p
        bx, by, ext = self.bx, self.by, p["col_ext"]
        f.retangulo(203, X0, 0, X0 + bx, by, s=1)
        f.retangulo(240, X0, 0, X0 + bx, by)
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
        f.cota((X0 + bx, y5), (X0 + bx + ext, y5), (X0 + bx, y5 + 0.6 * E), modo="h")
        f.texto(0, X0 - 0.2 * E, y5 - 1.0 * E, H_NOTA, "(barras contra colapso progressivo)")
        f.texto(226, X0 + 0.3 * E, y5 - 1.55 * E, H_NOTA, "ARMADURA DA FACE INFERIOR")
        x6 = X0 + bx + ext + 1.6 * E
        f.ferro(dict(tipo="reto", mark=fy["pos"], quant=fy["quant"], bitola=fy["bitola"], comp=fy["comp"],
                     ins=[dict(x=x6, y=col_y["ini"], ang=90.0, nivel=246, ipatas=1)]))
        f.cota((x6, by), (x6, by + ext), (x6 - 0.6 * E, by), modo="v")
        f.texto(0, x6 + 1.0 * E, -0.2 * E, H_NOTA, "(barras contra colapso progressivo)", a=90)
        f.texto(226, x6 + 1.55 * E, 0.3 * E, H_NOTA, "ARMADURA DA FACE INFERIOR", a=90)
        return x6 + 2.2 * E

    # ------------------------------------------------------------------ gabarito, notas, título
    def gabarito(self, X, Y):
        """DET. PLANTA - gabarito dos pentes mestres, a 1:25 (cotas com os valores reais)."""
        f, E, p = self.f, self.E, self.p
        k = E / 25.0
        Lt, L, s0 = self.bx * k, self.by * k, p["cob_s0"] * k
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
        self.caixa_gabarito = (X, y1, x1, Y)
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
    def _detalhes_e_cortes(self):
        """Na ordem a partir da planta: os detalhes (pelas faces e entre eixos) da peça inteira e da peça da face e
        as seções B-B e A-A. Cada função recebe a posição B e devolve a extensão na direção do empilhamento."""
        fe_ext = self.pos[("cobrinha", "extremidade")]
        fe_cont = self.pos.get(("cobrinha", "continua"))
        itens = []
        for pc, fe in ((self.cont, fe_cont), (self.ext, fe_ext)):
            if not pc:
                continue
            itens.append(("faces", lambda B, pc=pc: self.detalhe_faces(B, pc)))
            itens.append(("eixos", lambda B, pc=pc, fe=fe: self.detalhe_eixos(B, pc, fe)))
        itens.append(("corte", lambda B: self.corte(B, self.t_lado, "B")))
        itens.append(("corte", lambda B: self.corte(B, self.t_frente, "A", nota1=True)))
        return itens

    def montar(self):
        return self._montar_y() if self.vert else self._montar_x()

    def _montar_y(self):
        """Cobrinhas em y: os detalhes e os cortes à esquerda da planta, girados, como no modelo."""
        f, E = self.f, self.E
        self.planta()
        f.regiao("planta", 0)
        i0 = len(f.prims)
        x = self.t0 - 1.2 * E
        zp = 1.3 * E
        for tipo, desenhar in self._detalhes_e_cortes():
            if tipo == "faces":
                esq, _ = desenhar(x - 1.1 * E - self.fc / 2)
                x = esq - 0.4 * E
            elif tipo == "eixos":
                esq, _ = desenhar(x - 1.4 * E)
                x = esq - 0.6 * E
            else:
                esq, _ = desenhar(x - zp)
                x = esq - 1.0 * E
        x_esq = x - 0.6 * E
        f.regiao("corte", i0)
        # linhas das faces do pilar, dos cortes até a planta (como no modelo)
        for u in (0.0, self.L):
            f.linha(204, (x_esq + 1.5 * E, u), (0.0, u), s=3)
        # à direita: colapso; em cima: título, gabarito e notas
        i0 = len(f.prims)
        x_dir = self.colapso(self.t1 + 1.6 * E + self.p["col_ext"])
        f.regiao("colapso", i0)
        return self._fechar(x_esq, x_dir)

    def _montar_x(self):
        """Cobrinhas em x: os detalhes e os cortes embaixo da planta, alinhados com ela (x = u), face superior para
        cima. Cada um é desenhado em B = 0 e descido até abaixo do anterior."""
        f, E = self.f, self.E
        self.planta()
        x1, y1, x2, y2 = f.caixa(0)
        self.y_tit = max(y2 + 1.2 * E, self.by + self.p["col_ext"] + 2.2 * E)
        f.texto(226, x1, self.y_tit, H_VISTA, "VISTA EM PLANTA (ARM. PUNÇÃO)")
        f.texto(0, x1 + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        f.regiao("planta", 0)
        i_cortes = len(f.prims)
        cursor = y1 - 1.0 * E
        for tipo, desenhar in self._detalhes_e_cortes():
            i0 = len(f.prims)
            desenhar(0.0)
            _, b1, _, b2 = f.caixa(i0)
            dy = cursor - b2
            f.mover(i0, 0.0, dy)
            cursor = b1 + dy - (1.0 * E if tipo == "corte" else 0.6 * E)
        f.regiao("corte", i_cortes)
        y_fim = f.regioes["corte"][1]
        for u in (0.0, self.L):                           # faces do pilar, dos cortes até a planta
            f.linha(204, (u, y_fim - 0.1 * E), (u, 0.0), s=3)
        i0 = len(f.prims)
        x_dir = self.colapso(x2 + 1.6 * E + self.p["col_ext"])
        f.regiao("colapso", i0)
        x_esq = f.caixa(0)[0] - 1.6 * E
        return self._fechar(x_esq, x_dir)

    def altura_gabarito(self):
        """Altura do DET. PLANTA (títulos, cotas, desenho a 1:25 e margem), como em gabarito()."""
        k = self.E / 25.0
        return 2.7 * self.E + self.by * k + 2 * self.p["cob_s0"] * k + 0.6 * self.E

    def _fechar(self, x_esq, x_dir):
        """Título, gabarito e notas em cima, moldura e região da prancha. A faixa de cima tem 9,0E acima dos títulos
        das vistas, como no modelo, ou mais, quando o gabarito (desenhado a 1:25 com a altura do pilar) não cabe:
        com by >= 150 ele descia sobre o título do colapso. O fundo do gabarito fica 0,6E acima dos títulos."""
        f, E = self.f, self.E
        y_top = self.y_tit + 1.2 * E
        Y = max(y_top + 9.0 * E, self.y_tit + H_VISTA * E + 0.6 * E + self.altura_gabarito())
        xg, yg = self.gabarito(x_dir - 13.5 * E, Y)
        self.notas(x_dir - 13.5 * E - 15.0 * E, Y)
        self.titulo(x_esq + 0.5 * E, Y - 1.0 * E)
        x1, y1, x2, y2 = f.extensao()
        m = 0.8 * E
        f.retangulo(0, x1 - m, y1 - m, max(x2, xg) + m, max(y2, Y) + m)
        f.regiao("prancha", 0)
        return f


def montar(res):
    """Folha da prancha da cobrinha a partir do resultado de nucleo.detalhe.detalhar."""
    return Prancha(res).montar()
