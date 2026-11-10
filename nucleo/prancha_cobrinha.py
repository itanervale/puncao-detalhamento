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
from . import colapso as col
from .parametros import cobrimento_borda

NOTAS = [
    "CADA VÉRTICE DA ARM. DE PUNÇÃO DEVERÁ CONTER UMA BARRA SUPERIOR CONFORME ARMADURA NEGATIVA. CASO A ARMADURA "
    "NÃO COINCIDA COM O VÉRTICE UTILIZAR BARRAS ADICIONAIS DA MESMA BITOLA DA ARMADURA SUPERIOR (NEGATIVA).",
    "LOCAR NA FORMA A POSIÇÃO DO PINO MESTRE DE PUNÇÃO CONFORME SEÇÃO A-A.",
    "ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS ENTRE EIXOS DAS BARRAS.",
    "ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS DE DOBRAS ENTRE FACES DAS BARRAS.",
]
# Pilar de borda (E9): com a montagem omitida entre a face e a borda curta (mont_min_borda; pedido do usuário em
# 09/11/2026)
NOTA_BORDA_CURTA = ("NA BORDA CURTA, ENTRE A FACE DO PILAR E A BORDA LIVRE, NÃO HÁ BARRA DE MONTAGEM: UTILIZAR A "
                    "ARMADURA POSITIVA DA LAJE COMO MONTAGEM DOS VÉRTICES DE BAIXO DA ARMADURA DE PUNÇÃO.")


def _ganchos(barra):
    """Ganchos de 90° do ferro de colapso (só quando há: a folha do pilar interno não muda)."""
    return dict(ganchos=barra["ganchos"], reto=barra["reto"]) if any(barra["ganchos"]) else {}


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
        # Uma peça-modelo por tipo (posição): as da face, de preferência a do lado u = 0 (a do outro lado é a
        # espelhada); com borda livre, pode haver peças só de um lado (E9).
        self.modelos = {}
        for x in sorted(pc, key=lambda x: x["ini"] != 0):
            self.modelos.setdefault(x["tipo"], x)
        self.ext = self.modelos.get("extremidade") or self.modelos.get("extremidade_borda")
        self.cont = self.modelos.get("continua") or self.modelos.get("continua_borda")
        self.bd = self.c.get("bordas") or {k: None for k in ("u-", "u+", "t-", "t+")}
        self.u0 = min(u for x in pc for u, _ in x["pontos"])
        self.u1 = max(u for x in pc for u, _ in x["pontos"])
        lin = self.c["linhas"]
        self.t0, self.t1 = self.c.get("t_mont") or (lin[0] - p["mont_ext"], lin[-1] + p["mont_ext"])
        # corte A-A na linha diante da face mais perto do meio (afasta as marcas A e B na planta); B-B numa linha ao
        # lado do pilar, do lado livre
        self.t_frente = min((t for t in lin if 0 < t < self.Lt), key=lambda t: abs(t - self.Lt / 2))
        lado = [t for t in lin if t < 0]
        direita = [t for t in lin if t > self.Lt]
        if lado and not (self.bd["t-"] is not None and direita):
            self.t_lado = max(lado)
        else:
            self.t_lado = min(direita)
        self.cb = cobrimento_borda(p)                     # cobrimento na borda livre (Q15)
        # linha dos títulos (em x, refeita depois da planta, pela extensão dela)
        # além da borda livre (E9): as cotas, as marcas dos cortes e o pente mestre ficam fora da laje
        bu_mais, bu_menos = self.bd["u+"], self.bd["u-"]
        self.u_top = max(self.u1, self.L + bu_mais["a"]) if bu_mais else self.u1
        self.u_bot = min(self.u0, -bu_menos["a"]) if bu_menos else self.u0
        self.y_tit = max(self.u_top + 3.6 * self.E, self.by + p["col_ext"] + 2.2 * self.E)

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
        # a laje termina reta na borda livre (E9) e, do lado livre, numa linha de quebra
        ba, bb = self.bd["u-"], self.bd["u+"]
        ua = -ba["a"] if ba else self.u0 - 1.2 * E
        ub = L + bb["a"] if bb else self.u1 + 1.2 * E
        zp = 1.3 * E
        amp = 0.67 * E
        qa = [] if ba else quebra((ua, h), (ua, 0), amp * 0.45)[1:-1]
        qb = [] if bb else quebra((ub, 0), (ub, h), amp * 0.45)[1:-1]
        if sobre:                                         # pilar cortado
            uz = [(ua, 0), (0, 0), (0, -zp)] + quebra((0, -zp), (L, -zp), amp)[1:-1] + [(L, -zp), (L, 0), (ub, 0)]
            uz += qb + [(ub, h), (L, h), (L, h + zp)]
            uz += quebra((L, h + zp), (0, h + zp), amp)[1:-1] + [(0, h + zp), (0, h), (ua, h)]
            uz += qa
        else:                                             # pilar além do corte, tracejado
            uz = [(ua, 0), (ub, 0)] + qb + [(ub, h), (ua, h)] + qa
            f.poli(203, [T(0, -zp), T(L, -zp), T(L, h + zp), T(0, h + zp)], s=1, fechar=True)
        if ba or bb:                                      # pilar faceando a borda: pontos repetidos
            uz = [q for i, q in enumerate(uz) if i == 0 or abs(q[0] - uz[i - 1][0]) + abs(q[1] - uz[i - 1][1]) > 1e-6]
        contorno = [T(u, z) for u, z in uz]
        f.poli(0, contorno, fechar=True)
        f.poli(240, contorno, fechar=True)
        self._cotas_espessura(T, ua)
        # barras de flexão de referência (traço-ponto): 2ª camada da negativa e positiva sobre a montagem; na borda,
        # até o cobrimento
        ra = ua + (self.cb if ba else 0.3 * E)
        rb = ub - (self.cb if bb else 0.3 * E)
        for z1, z2 in ((h - self.cs - self.fc - self.f1 - self.f2, h - self.cs - self.fc - self.f1),
                       (self.ci + self.fc + self.fm, self.ci + self.fc + 2 * self.fm)):
            for zz in (z1, z2):
                f.linha(0, T(ra, zz), T(rb, zz), s=3)
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
            for tem, u, sinal in ((longit["ganchos"][0], longit["ini"], 1), (longit["ganchos"][1], longit["fim"], -1)):
                if tem:                                   # gancho de 90° para cima na borda livre (E9, Q13)
                    alt = col.altura_gancho(self.p["col_bitola"])
                    f.poli(245, [T(u + sinal * self.fcol, self.ci + self.fcol), T(u + sinal * self.fcol,
                                 self.ci + alt), T(u, self.ci + alt), T(u, self.ci)])
        # "TOPO LAJE" do lado livre: além da face u = L ou, com a borda desse lado, antes da face u = 0
        u_txt = L + (self.u1 - L) * 0.25 if bb is None else self.u0 * 0.75
        if nota1:                                         # fora das chamadas da NOTA 1 e do pilar
            u_txt = self._topo_livre(u_txt, sup, ua, ub)
        f.texto(221, *T(u_txt, h + 0.35 * E), H_CHAMADA, "TOPO LAJE", a=self.a_u)
        if self.vert:
            tx, ty = B - h - zp, self.y_tit
        else:
            tx, ty = ua, B + h + zp + 0.9 * E
            # com a borda faceando a face u = 0, o título começa no pilar, embaixo da caixa da NOTA 1: sobe acima dela
            larg = self._texto_largura(f"SEÇÃO {letra}-{letra}", H_VISTA)
            if nota1 and tx < L / 2 + 1.3 * E and tx + larg > L / 2 - 1.3 * E:
                ty = B + h + zp + 0.6 * E + 0.63 * E + 0.7 * E
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

    def _cotas_espessura(self, T, ua):
        """Espessura da laje e cobrimentos na ponta u = ua da seção (embaixo com as cobrinhas em y, à esquerda em x;
        pedido do usuário em 09/11/2026): numa fila os dois cobrimentos e, por fora, h. Sem o trecho entre os
        cobrimentos: o texto do cobrimento não cabe no trecho, o TQS o empurra para o lado e ele caía sobre o do meio
        ("222.5")."""
        f, E, h = self.f, self.E, self.h
        mz = self._modo("t")
        for a, b in ((0.0, self.ci), (h - self.cs, h)):
            f.cota(T(ua, a), T(ua, b), T(ua - 0.7 * E, a), modo=mz)
        f.cota(T(ua, 0.0), T(ua, h), T(ua - 1.3 * E, 0.0), modo=mz)

    def _topo_livre(self, u_pref, sup, ua, ub):
        """Posição (u) do "TOPO LAJE" na seção A-A: o trecho do tamanho do texto, logo acima da face superior, que
        não cruza as chamadas da NOTA 1 (da caixa sobre o pilar aos vértices de cima) nem o pilar, o mais perto
        possível de u_pref. Sem trecho livre, u_pref."""
        E, h, L = self.E, self.h, self.L
        larg = self._texto_largura("TOPO LAJE", H_CHAMADA)
        meio, z1 = L / 2, h + 1.3 * E + 0.6 * E           # ponto de onde saem as chamadas (como em corte())
        za, zb = h + 0.35 * E, h + 0.35 * E + H_CHAMADA * E
        r1 = self.f1 / 2
        proib = [(-0.1 * E, L + 0.1 * E)]                 # o pilar cortado, acima da laje
        for uc, zc in sup:
            zt = zc + r1 * 0.7
            us = [meio + (uc - meio) * (z1 - z) / (z1 - zt) for z in (za, zb) if min(z1, zt) <= z <= max(z1, zt)]
            if us:
                proib.append((min(us) - 0.15 * E, max(us) + 0.15 * E))
        lo, hi = ua + 0.2 * E, ub - 0.2 * E - larg
        livres = [u for u in (lo + i for i in range(int(max(0.0, hi - lo)) + 1))
                  if all(u + larg < a or u > b for a, b in proib)]
        return min(livres, key=lambda u: abs(u - u_pref)) if livres else u_pref

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
        """Um bloco por tipo de peça (posição), desenhado ao longo do y local. As peças da face ficam na orientação do
        lado u = 0; a que só existe do lado u = L (borda do outro lado) é levada para ela (v = L - u) e inserida
        espelhada, como a peça da face direita do pilar interno."""
        f, fc = self.f, self.fc
        nomes = {}
        for tipo in ("extremidade", "extremidade_borda", "continua", "continua_borda", "recuada"):
            pc = self.modelos.get(tipo)
            if pc is None:
                continue
            v = (lambda u: self.L - u) if tipo.startswith("extremidade") and pc["ini"] != 0 else (lambda u: u)
            fe = self.pos[("cobrinha", tipo)]
            nome = f"COBRINHA N{fe['pos']} {_fmt(self.p['cob_bitola'])}"
            b = f.novo_bloco(nome)
            for a, z, nivel in pc["trechos"]:
                for dx in (-fc / 2, fc / 2):
                    b.linha(241, (dx, v(a)), (dx, v(z)), s=1 if nivel == "sup" else 0)
            for u in pc["pernas"]:
                b.circ(241, 0.0, v(u), fc / 2)
                b.circ(233, 0.0, v(u), fc / 2)
            nomes[tipo] = nome
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
            if pc["tipo"].startswith("extremidade"):
                if pc["ini"] == 0:
                    self._inserir(nomes[pc["tipo"]], pc["linha"], 0.0)
                else:
                    self._inserir(nomes[pc["tipo"]], pc["linha"], L, espelhar=True)
            else:
                self._inserir(nomes[pc["tipo"]], pc["linha"], 0.0)
        self._bordas_planta()
        for b in c["montagem"]:
            f.linha(243, Pl(b["ini"], b["pos"]), Pl(b["fim"], b["pos"]))
        # cotas: linhas de cobrinha (além da ponta u1), fileiras diante das faces (além da última linha) e ao lado
        # do pilar (antes da primeira linha)
        mt, mu = self._modo("t"), self._modo("u")
        lin = c["linhas"]
        bd = self.bd
        # as cadeias ficam além da borda livre, fora da laje
        alem = lambda k, base, sinal, v: (v if bd[k] is None else                       # noqa: E731
                                          (max if sinal > 0 else min)(v, base + sinal * bd[k]["a"]))
        yc = alem("u+", L, 1, self.u1) + 0.9 * E
        for a, b in zip(lin, lin[1:]):
            f.cota(Pl(a, self.u1), Pl(b, self.u1), Pl(a, yc), modo=mt)
        # peças diante da face recuada (E9): as pernas delas na cadeia do lado em que ficam
        rec = set(self.modelos["recuada"]["pernas"]) if "recuada" in self.modelos else set()
        rec_neg = any(pc["tipo"] == "recuada" and pc["linha"] < 0 for pc in c["pecas"])
        rec_pos = any(pc["tipo"] == "recuada" and pc["linha"] > Lt for pc in c["pecas"])
        fil = sorted({u for pc in c["pecas"] if pc["tipo"].startswith("extremidade") for u in pc["pernas"]} | {0.0, L}
                     | (rec if rec_pos else set()))
        xc = alem("t+", Lt, 1, lin[-1]) + 0.9 * E
        for a, b in zip(fil, fil[1:]):
            f.cota(Pl(lin[-1], a), Pl(lin[-1], b), Pl(xc, a), modo=mu)
        # pilar recuado da borda (E9): a distância da face à borda numa fila própria, além da cadeia (dentro dela,
        # o trecho da última linha à borda é só o cobrimento, curto demais para o texto)
        for k, base, sinal in (("t-", 0.0, -1), ("t+", Lt, 1)):
            if bd[k] is not None and bd[k]["a"] > 0.5:
                a, b = sorted((base, base + sinal * bd[k]["a"]))
                f.cota(Pl(a, L), Pl(b, L), Pl(a, yc + 0.6 * E), modo=mt)
        for k, base, sinal in (("u-", 0.0, -1), ("u+", L, 1)):
            if bd[k] is not None and bd[k]["a"] > 0.5:
                a, b = sorted((base, base + sinal * bd[k]["a"]))
                f.cota(Pl(Lt, a), Pl(Lt, b), Pl(xc + 0.6 * E, a), modo=mu)
        if self.cont or rec_neg:
            if rec_neg:
                lado = sorted(rec | {0.0, L})
            else:
                lado = [u for u in self.cont["pernas"] if -s0 - 1e-6 <= u <= L + s0 + 1e-6]
            xl = alem("t-", 0.0, -1, lin[0]) - 0.9 * E
            for a, b in zip(lado, lado[1:]):
                f.cota(Pl(lin[0], a), Pl(lin[0], b), Pl(xl, a), modo=mu)
        # s0 nas duas direções, num lado que tem a linha (ou a perna) de s0, de preferência livre (na borda curta, o
        # pente mestre não serve para locar: E9), e sem as duas cotas no mesmo canto
        lado_t = self._lado_s0(lin, -s0, Lt + s0, "t-", "t+", ("-", "+"))
        lado_u = self._lado_s0(fil, -s0, L + s0, "u-", "u+", ("+", "-"))
        if lado_t == "-":
            f.cota(Pl(-s0, L), Pl(0, L), Pl(-s0, L + s0 / 2), modo=mt)
        elif lado_t == "+" and lado_u == "+":                     # o canto (Lt, L) é da cota em u: a de t desce
            f.cota(Pl(Lt, 0.0), Pl(Lt + s0, 0.0), Pl(Lt, -s0 / 2), modo=mt)
        elif lado_t == "+":
            f.cota(Pl(Lt, L), Pl(Lt + s0, L), Pl(Lt, L + s0 / 2), modo=mt)
        if lado_u == "+":
            f.cota(Pl(Lt, L), Pl(Lt, L + s0), Pl(Lt + s0 / 2, L), modo=mu)
        elif lado_u == "-":
            f.cota(Pl(Lt, -s0), Pl(Lt, 0.0), Pl(Lt + s0 / 2, -s0), modo=mu)
        # pente mestre (além da cadeia de cotas, do lado da linha que ele aponta, sem passar sobre as marcas dos
        # cortes) e marcas dos cortes (além das cotas e da borda livre)
        t_pm = -s0 if lado_t == "-" else Lt + s0
        larg = self._texto_largura("PENTE MESTRE", H_CHAMADA)
        marcas = (self.t_frente, self.t_lado)
        alvo = Pl(t_pm, self.u1 + 0.05 * E)
        if t_pm < 0 or not self.vert:
            if t_pm < 0:
                t_txt = self.t0 + 0.2 * E
                if self.vert:
                    t_txt = min(t_txt, min(marcas) - 1.4 * E - larg - 0.3 * E)
            else:                                         # em x, o texto fica em cima, do lado da linha
                t_txt = self.t1 - 0.2 * E - H_CHAMADA * E
            tx, ty = Pl(t_txt, self.u_top + 2.3 * E)
            pts = [(tx, ty - 0.1 * E), (tx + larg + 0.3 * E, ty - 0.1 * E), alvo]
            if not self.vert:                             # em x, dobra antes das cotas e cruza a cadeia no tique
                pts.insert(2, Pl(t_pm, self.u_top + 1.2 * E))
        else:                                             # em y, à direita das marcas, com a chamada para a esquerda
            tx, ty = Pl(max(marcas) + 0.5 * E, self.u_top + 2.3 * E)
            pts = [(tx + larg, ty - 0.1 * E), (tx - 0.3 * E, ty - 0.1 * E), Pl(t_pm, self.u_top + 1.2 * E), alvo]
        f.texto(253, tx, ty, H_CHAMADA, "PENTE MESTRE")
        f.texto(253, tx + 0.5 * E, ty - 0.45 * E, H_CHAMADA, "P/ LOCAÇÃO")
        self._chamada(253, pts)
        for t, letra in ((self.t_frente, "A"), (self.t_lado, "B")):
            self._marca_corte(t, self.u_top + 1.6 * E, 1, letra)
            self._marca_corte(t, self.u_bot - 0.4 * E, -1, letra)
        if self.vert:                                     # em x, o título vai depois, pela extensão da planta
            f.texto(226, self.t0, self.y_tit, H_VISTA, "VISTA EM PLANTA (ARM. PUNÇÃO)")
            f.texto(0, self.t0 + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        # barras de montagem identificadas, antes do início das cobrinhas (abaixo das marcas dos cortes); com borda,
        # pode haver duas posições de barra lateral (uma de cada lado do pilar)
        y = self.u_bot - 2.9 * E
        for fe in [x for x in self.r["ferros"] if x["tipo"] == "montagem"]:
            if fe["subtipo"] == "continua":
                b = next(b for b in c["montagem"] if b["tipo"] == "continua" and abs(b["comp"] - fe["comp"]) < 0.5)
                ini = b["ini"]
                marcos = [b["ini"]] + [x for x in (lin[0], lin[-1]) if b["ini"] < x < b["fim"]] + [b["fim"]]
            else:
                b = next(b for b in c["montagem"] if b["tipo"] == "lateral" and abs(b["comp"] - fe["comp"]) < 0.5)
                ini = b["ini"]
                marcos = [b["ini"], lin[0], 0.0] if b["ini"] < 0 else [Lt, lin[-1], b["fim"]]
            xi, yi = Pl(ini, y)
            f.ferro(dict(tipo="reto", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], comp=fe["comp"],
                         ins=[dict(x=xi, y=yi, ang=0.0 if self.vert else 90.0, nivel=244, ipatas=1)]))
            marcos = sorted(set(round(m, 4) for m in marcos if min(marcos[0], marcos[-1]) - 1e-6 <= m
                                <= max(marcos[0], marcos[-1]) + 1e-6))
            for a, b in zip(marcos, marcos[1:]):
                if b - a > 0.5:
                    f.cota(Pl(a, y), Pl(b, y), Pl(a, y + 0.6 * E), modo=mt)
            y -= 2.2 * E
        self.y_min_planta = y

    def _lado_s0(self, lista, v_neg, v_pos, k_neg, k_pos, ordem):
        """Lado ("-" ou "+") da linha ou da perna de s0 para a cota e o pente mestre: um lado que a tem, livre de
        preferência (na ordem dada), ou None."""
        tem = {"-": any(abs(x - v_neg) < 1e-6 for x in lista), "+": any(abs(x - v_pos) < 1e-6 for x in lista)}
        livre = {"-": self.bd[k_neg] is None, "+": self.bd[k_pos] is None}
        for lado in ordem:
            if tem[lado] and livre[lado]:
                return lado
        return next((lado for lado in ordem if tem[lado]), None)

    def _bordas_planta(self):
        """Borda livre na planta (E9): a linha da borda (nível 0, o do contorno da laje nos cortes do modelo), o
        texto "BORDA LIVRE" (221, como o "TOPO LAJE") e, com o pilar recuado, a cota da face até a borda."""
        f, E, Pl, bd = self.f, self.E, self.Pl, self.bd
        if not any(bd.values()):
            return
        lin, L, Lt = self.c["linhas"], self.L, self.Lt
        a = {k: (v["a"] if v else None) for k, v in bd.items()}
        t_ini = -a["t-"] if a["t-"] is not None else min(self.t0, lin[0]) - 0.6 * E
        t_fim = Lt + a["t+"] if a["t+"] is not None else max(self.t1, lin[-1]) + 0.6 * E
        u_ini = -a["u-"] if a["u-"] is not None else self.u0 - 0.6 * E
        u_fim = L + a["u+"] if a["u+"] is not None else self.u1 + 0.6 * E
        linhas = []
        if a["u-"] is not None:
            linhas.append(((t_ini, -a["u-"]), (t_fim, -a["u-"]), "u", 0.0, -1))
        if a["u+"] is not None:
            linhas.append(((t_ini, L + a["u+"]), (t_fim, L + a["u+"]), "u", L, 1))
        if a["t-"] is not None:
            linhas.append(((-a["t-"], u_ini), (-a["t-"], u_fim), "t", 0.0, -1))
        if a["t+"] is not None:
            linhas.append(((Lt + a["t+"], u_ini), (Lt + a["t+"], u_fim), "t", Lt, 1))
        for p1, p2, eixo, face, sinal in linhas:
            self._linha_borda(Pl(*p1), Pl(*p2), sinal)

    def _linha_borda(self, p1, p2, sinal):
        """Linha da borda livre (nível 0; o 240 é a hachura de 25 % e não sai na plotagem) de p1 a p2 (na prancha, horizontal ou vertical) e o texto "BORDA LIVRE"
        paralelo a ela, do lado de fora da laje (sinal +1: x ou y maior), perto do fim da linha."""
        f, E = self.f, self.E
        (x1, y1), (x2, y2) = p1, p2
        f.linha(0, (x1, y1), (x2, y2))
        larg = self._texto_largura("BORDA LIVRE", H_CHAMADA)
        if abs(y2 - y1) < 1e-9:
            xb = max(x1, x2)
            ty = y1 + (0.2 * E if sinal > 0 else -0.2 * E - H_CHAMADA * E)
            f.texto(221, xb - larg - 0.3 * E, ty, H_CHAMADA, "BORDA LIVRE")
        else:
            yb = max(y1, y2)
            tx = x1 + (0.2 * E + H_CHAMADA * E if sinal > 0 else -0.2 * E)
            f.texto(221, tx, yb - larg - 0.3 * E, H_CHAMADA, "BORDA LIVRE", a=90.0)

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
        self._bordas_colapso(X0, col_x, col_y)
        f.texto(226, X0 + col_x["ini"], self.y_tit, H_VISTA, "VISTA EM PLANTA (COLAPSO PROGRESSIVO)")
        f.texto(0, X0 + col_x["ini"] + 0.1 * E, self.y_tit - 0.45 * E, H_ESCALA, f"ESCALA 1:{E:g}")
        fx = self.pos[("colapso", "x")]
        fy = self.pos[("colapso", "y")]
        y5 = col_y["ini"] - 1.6 * E
        f.ferro(dict(tipo="reto", mark=fx["pos"], quant=fx["quant"], bitola=fx["bitola"], comp=fx["comp"],
                     ins=[dict(x=X0 + col_x["ini"], y=y5, ang=0.0, nivel=246, ipatas=1)], **_ganchos(col_x)))
        # comprimento além da face num lado livre e, do lado da borda, da face até a ponta (no cobrimento)
        if not col_x["borda_fim"]:
            f.cota((X0 + bx, y5), (X0 + bx + ext, y5), (X0 + bx, y5 + 0.6 * E), modo="h")
        else:
            f.cota((X0 - ext, y5), (X0, y5), (X0 - ext, y5 + 0.6 * E), modo="h")
        for b_ponta, a, b in ((col_x["borda_ini"], col_x["ini"], 0.0), (col_x["borda_fim"], bx, col_x["fim"])):
            if b_ponta and b - a > 0.5:
                f.cota((X0 + a, y5), (X0 + b, y5), (X0 + a, y5 + 0.6 * E), modo="h")
        f.texto(0, X0 - 0.2 * E, y5 - 1.0 * E, H_NOTA, "(barras contra colapso progressivo)")
        f.texto(226, X0 + 0.3 * E, y5 - 1.55 * E, H_NOTA, "ARMADURA DA FACE INFERIOR")
        x6 = X0 + col_x["fim"] + 1.6 * E
        f.ferro(dict(tipo="reto", mark=fy["pos"], quant=fy["quant"], bitola=fy["bitola"], comp=fy["comp"],
                     ins=[dict(x=x6, y=col_y["ini"], ang=90.0, nivel=246, ipatas=1)], **_ganchos(col_y)))
        if not col_y["borda_fim"]:
            f.cota((x6, by), (x6, by + ext), (x6 - 0.6 * E, by), modo="v")
        else:
            f.cota((x6, -ext), (x6, 0.0), (x6 - 0.6 * E, -ext), modo="v")
        for b_ponta, a, b in ((col_y["borda_ini"], col_y["ini"], 0.0), (col_y["borda_fim"], by, col_y["fim"])):
            if b_ponta and b - a > 0.5:
                f.cota((x6, a), (x6, b), (x6 - 0.6 * E, a), modo="v")
        f.texto(0, x6 + 1.0 * E, -0.2 * E, H_NOTA, "(barras contra colapso progressivo)", a=90)
        f.texto(226, x6 + 1.55 * E, 0.3 * E, H_NOTA, "ARMADURA DA FACE INFERIOR", a=90)
        return x6 + 2.2 * E

    def _x0_colapso(self, x_ref):
        """Origem da vista do colapso com borda livre: a parte da esquerda (barra ou borda) a 1,6E de x_ref."""
        p, col_x = self.p, self.r["colapso"][0]
        esq = -p["dist_borda_x"] if p["borda_x"] == "esquerda" else col_x["ini"] - 0.6 * self.E
        return x_ref + 1.6 * self.E - min(esq, col_x["ini"])

    def _bordas_colapso(self, X0, col_x, col_y):
        """Bordas livres na vista do colapso (coordenadas da prancha: bx na horizontal, by na vertical)."""
        p, E, bx, by = self.p, self.E, self.bx, self.by
        ex = p["dist_borda_x"] if p["borda_x"] else None
        ey = p["dist_borda_y"] if p["borda_y"] else None
        if ex is None and ey is None:
            return
        xa = X0 - ex if p["borda_x"] == "esquerda" else X0 + col_x["ini"] - 0.6 * E
        xb = X0 + bx + ex if p["borda_x"] == "direita" else X0 + col_x["fim"] + 0.6 * E
        ya = -ey if p["borda_y"] == "baixo" else col_y["ini"] - 0.6 * E
        yb = by + ey if p["borda_y"] == "cima" else col_y["fim"] + 0.6 * E
        if p["borda_x"] == "esquerda":
            self._linha_borda((xa, ya), (xa, yb), -1)
        elif p["borda_x"] == "direita":
            self._linha_borda((xb, ya), (xb, yb), 1)
        if p["borda_y"] == "baixo":
            self._linha_borda((xa, ya), (xb, ya), -1)
        elif p["borda_y"] == "cima":
            self._linha_borda((xa, yb), (xb, yb), 1)

    # ------------------------------------------------------------------ gabarito, notas, título
    def _lados_prancha(self):
        """Lados do pilar na prancha ("x-", "x+", "y-", "y+") -> (tem a linha do pente mestre a s0?, distância da
        borda livre ou None). O gabarito mostra o pilar de borda ou de canto desprezando a borda curta (pedido do
        usuário em 09/11/2026): do lado de uma borda, sem pente mestre e com a borda na face (0)."""
        mapa = ({"x-": "t-", "x+": "t+", "y-": "u-", "y+": "u+"} if self.vert
                else {"x-": "u-", "x+": "u+", "y-": "t-", "y+": "t+"})
        s0, cont = self.p["cob_s0"], self.c["contorno"]
        return {k: ((False, 0.0) if self.bd[loc] else (abs(cont[loc] - s0) < 1e-6, None)) for k, loc in mapa.items()}

    def _afastamentos_gabarito(self):
        """Quanto o gabarito vai além de cada face (cm reais): s0 ou a borda, o maior."""
        s0 = self.p["cob_s0"]
        return {k: max(s0 if tem else 0.0, a or 0.0) for k, (tem, a) in self._lados_prancha().items()}

    def gabarito(self, X, Y):
        """DET. PLANTA - gabarito dos pentes mestres, a 1:25 (cotas com os valores reais)."""
        if any(a is not None for _, a in self._lados_prancha().values()):
            return self._gabarito_bordas(X, Y)
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
        ym = y0 + L * 0.75                              # longe do texto da cota do lado maior, que fica no meio
        f.texto(253, tx, ym + 0.3 * E, H_CHAMADA, "NOTA 2")
        self._chamada(253, [(tx + 2.0 * E, ym + 0.15 * E), (tx - 0.1 * E, ym + 0.15 * E), (x0 + Lt + s0, ym)])
        f.texto(220, X + 0.3 * E, Y - 0.6 * E, H_VISTA, "DET. PLANTA")
        f.texto(220, X + 0.3 * E, Y - 1.05 * E, 0.20, "GABARITO PENTES MESTRES")
        f.texto(0, X + 0.3 * E, Y - 1.4 * E, H_ESCALA, "ESCALA 1:25")
        x1, y1 = tx + 3.2 * E, y0 - s0 - 0.6 * E
        f.retangulo(0, X, y1, x1, Y)
        self.caixa_gabarito = (X, y1, x1, Y)
        return x1, y1

    def _gabarito_bordas(self, X, Y):
        """O gabarito com borda livre (E9): a linha do pente mestre (233) só nos lados que a têm, a borda (0) nos
        outros e as cotas até a borda."""
        f, E = self.f, self.E
        k = E / 25.0
        s0 = self.p["cob_s0"] * k
        lados = self._lados_prancha()
        off = {n: v * k for n, v in self._afastamentos_gabarito().items()}
        Lx, Ly = self.bx * k, self.by * k
        x0, y0 = X + 0.8 * E + off["x-"], Y - 2.7 * E - Ly - off["y+"]
        xL, xR, yB, yT = x0 - off["x-"], x0 + Lx + off["x+"], y0 - off["y-"], y0 + Ly + off["y+"]
        f.retangulo(203, x0, y0, x0 + Lx, y0 + Ly, s=1)
        f.retangulo(240, x0, y0, x0 + Lx, y0 + Ly)
        # linha do pente mestre: do lado sem ela, as vizinhas vão até a borda
        pos = {}
        for n, base, sinal in (("x-", x0, -1), ("x+", x0 + Lx, 1), ("y-", y0, -1), ("y+", y0 + Ly, 1)):
            tem, a = lados[n]
            pos[n] = base + sinal * (s0 if tem else a * k)
        L_, R_, B_, T_ = pos["x-"], pos["x+"], pos["y-"], pos["y+"]
        lados_pm = [("y-", (L_, B_), (R_, B_)), ("x+", (R_, B_), (R_, T_)), ("y+", (R_, T_), (L_, T_)),
                    ("x-", (L_, T_), (L_, B_))]
        i = next((j for j, (n, _, _) in enumerate(lados_pm) if not lados[n][0]), None)
        if i is None:                                     # borda além de s0: as quatro linhas
            f.retangulo(233, L_, B_, R_, T_)
            lados_pm, i = [], -1
        corrida = []
        for n, a, b in lados_pm[i + 1:] + lados_pm[:i + 1]:
            if lados[n][0]:
                corrida = corrida or [a]
                corrida.append(b)
            elif corrida:
                f.poli(233, corrida)
                corrida = []
        if corrida:
            f.poli(233, corrida)
        for n, (tem, a) in lados.items():
            if a is None:
                continue
            if n[0] == "x":
                x = x0 - a * k if n == "x-" else x0 + Lx + a * k
                f.linha(0, (x, yB - 0.3 * E), (x, yT + 0.3 * E))
            else:
                y = y0 - a * k if n == "y-" else y0 + Ly + a * k
                f.linha(0, (xL - 0.3 * E, y), (xR + 0.3 * E, y))
        # cotas: em cima (x) e à direita (y), com o pente mestre e a borda
        def marcos(lo, hi, neg, posit):
            v = {lo, hi}
            for n, base, sinal in ((neg, lo, -1), (posit, hi, 1)):
                tem, a = lados[n]
                if tem:
                    v.add(base + sinal * s0)
                if a is not None:
                    v.add(base + sinal * a * k)
            out = []
            for m in sorted(v):
                if not out or m - out[-1] > 1e-6:
                    out.append(m)
            return out
        yc = yT + 0.6 * E
        mx = marcos(x0, x0 + Lx, "x-", "x+")
        for a, b in zip(mx, mx[1:]):
            f.cota((a, yT), (b, yT), (a, yc), modo="h", fator=1 / k)
        xc = xR + 0.6 * E
        my = marcos(y0, y0 + Ly, "y-", "y+")
        for a, b in zip(my, my[1:]):
            f.cota((xR, a), (xR, b), (xc, a), modo="v", fator=1 / k)
        tx = xc + 1.0 * E
        ym = y0 + Ly * 0.75                             # longe do texto da cota do lado maior, que fica no meio
        if lados["x+"][0]:
            alvo, yl = (x0 + Lx + s0, ym), ym + 0.15 * E
        elif lados["y-"][0]:                            # sem pente mestre à direita: a linha de baixo, por fora
            alvo, yl = (x0 + Lx * 0.8, y0 - s0), yB - 0.35 * E     # das cotas (abaixo da última)
        else:                                           # ou a de cima, entre ela e a cadeia de cima
            alvo, yl = (x0 + Lx * 0.8, y0 + Ly + s0), yT + 0.3 * E
        f.texto(253, tx, yl + 0.15 * E, H_CHAMADA, "NOTA 2")
        self._chamada(253, [(tx + 2.0 * E, yl), (tx - 0.1 * E, yl), alvo])
        f.texto(220, X + 0.3 * E, Y - 0.6 * E, H_VISTA, "DET. PLANTA")
        f.texto(220, X + 0.3 * E, Y - 1.05 * E, 0.20, "GABARITO PENTES MESTRES")
        f.texto(0, X + 0.3 * E, Y - 1.4 * E, H_ESCALA, "ESCALA 1:25")
        x1, y1 = tx + 3.2 * E, yB - 0.6 * E
        f.retangulo(0, X, y1, x1, Y)
        self.caixa_gabarito = (X, y1, x1, Y)
        return x1, y1

    def notas(self, X, Y):
        f, E = self.f, self.E
        dy = 0.5 * E
        largura = 52                                   # caracteres por linha (o 1º traz 8 espaços para o "NOTA n:")
        linhas = []
        notas = NOTAS + ([NOTA_BORDA_CURTA] if self.c.get("mont_omitidas") else [])
        for i, nota in enumerate(notas, 1):
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
        itens = []
        # peças inteiras primeiro, depois as da face; com borda livre, também as que terminam nela (E9)
        for tipo in ("continua", "continua_borda", "extremidade", "extremidade_borda", "recuada"):
            pc, fe = self.modelos.get(tipo), self.pos.get(("cobrinha", tipo))
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
        if any(self.bd.values()):                         # a borda e as cotas além dela podem passar de t1
            x_dir = self.colapso(self._x0_colapso(max(self.t1, f.regioes["planta"][2])))
        else:
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
        x_dir = self.colapso(self._x0_colapso(x2) if any(self.bd.values()) else x2 + 1.6 * E + self.p["col_ext"])
        f.regiao("colapso", i0)
        x_esq = f.caixa(0)[0] - 1.6 * E
        return self._fechar(x_esq, x_dir)

    def altura_gabarito(self):
        """Altura do DET. PLANTA (títulos, cotas, desenho a 1:25 e margem), como em gabarito()."""
        k = self.E / 25.0
        if any(a is not None for _, a in self._lados_prancha().values()):
            off = self._afastamentos_gabarito()
            return 2.7 * self.E + self.by * k + (off["y-"] + off["y+"]) * k + 0.6 * self.E
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
