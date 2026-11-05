# -*- coding: utf-8 -*-
"""
Folha de desenho em primitivas (sem o TQS): linhas, polilinhas, círculos, arcos, textos, cotas, blocos e ferros
inteligentes, cada um com o nível dos desenhos de referência (PADRAO_desenho.md). O gravador (dwg_tqs/gravar.py)
transcreve a folha para o DWG-TQS.

Coordenadas em cm reais; alturas de texto dadas em cm de papel (multiplicadas pela escala). Estilo e cor None = os
do nível. As linhas, polilinhas, círculos, arcos e textos seguem o formato do despejo (ferramentas/ler_modelo.py),
para a mesma ferramenta de imagem servir aos dois.
"""
import math

# Alturas de texto (cm de papel), dos modelos (PADRAO_desenho.md, seção 2)
H_TITULO, H_NX, H_VISTA, H_ESCALA, H_LETRA = 0.50, 0.45, 0.35, 0.22, 0.30
H_NOTA, H_NOTAS_TIT, H_QUADRO, H_CHAMADA = 0.25, 0.37, 0.32, 0.25


class Folha:
    def __init__(self, escala=15.0):
        self.E = float(escala)
        self.prims = []
        self.blocos = {}             # nome -> lista de primitivas em coordenadas do bloco ("" = bloco do TQS)
        self.regioes = {}            # nome da vista -> (x1, y1, x2, y2), para a janela enquadrar cada vista

    # ------------------------------------------------------------------ primitivas
    def _add(self, p):
        self.prims.append(p)
        return p

    def linha(self, n, p1, p2, s=None, c=None):
        return self._add({"t": "Linha", "n": n, "s": s, "c": c, "xy": [list(p1), list(p2)]})

    def poli(self, n, pts, s=None, c=None, fechar=False, cheia=False):
        pts = [list(p) for p in pts]
        if fechar and pts[0] != pts[-1]:
            pts.append(list(pts[0]))
        return self._add({"t": "Polyline", "n": n, "s": s, "c": c, "xy": pts, "fill": bool(cheia)})

    def retangulo(self, n, x1, y1, x2, y2, s=None, c=None):
        return self.poli(n, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], s, c, fechar=True)

    def circ(self, n, x, y, r, s=None, c=None):
        return self._add({"t": "Circulo", "n": n, "s": s, "c": c, "x": x, "y": y, "r": r})

    def arco(self, n, x, y, r, a1, a2, s=None, c=None):
        return self._add({"t": "Arco", "n": n, "s": s, "c": c, "x": x, "y": y, "r": r, "a1": a1, "a2": a2})

    def texto(self, n, x, y, h_papel, txt, a=0.0, c=None):
        return self._add({"t": "Texto", "n": n, "s": None, "c": c, "x": x, "y": y, "h": h_papel * self.E,
                          "a": a, "txt": str(txt)})

    def cota(self, p1, p2, p3, modo="h", ang=None, txt=None, niveis=(221, 253), fator=1.0):
        """Cota (objeto IPOCOT do TQS). modo: "h", "v", "a" (alinhada) ou "i" (inclinada em ang graus).
        p3 = ponto da linha de cota. txt = texto fixo (None = a medida). fator = dimlfc (vista em outra escala)."""
        return self._add({"t": "Cota", "p1": list(p1), "p2": list(p2), "p3": list(p3), "modo": modo, "ang": ang,
                          "txt": txt, "niveis": tuple(niveis), "fator": fator})

    def bloco(self, nome, x, y, ang=0.0, sx=1.0, sy=1.0, n=0):
        return self._add({"t": "Bloco", "n": n, "b": nome, "x": x, "y": y, "ang": ang, "sx": sx, "sy": sy})

    def ferro(self, spec):
        """Ferro inteligente: dict com tipo ("gen" ou "reto"), mark, quant, bitola, comp (reto), pontos (gen,
        relativos à 1ª inserção), ins = [dict(x, y, ang, nivel, ipatas, ident, idobra)], texto (opcional:
        dict(x, y, ang)) e atributos (dict de atributos do SmartRebar)."""
        spec = dict(spec, t="Ferro")
        return self._add(spec)

    # ------------------------------------------------------------------ desenhos compostos
    def novo_bloco(self, nome):
        """Começa a definição de um bloco: devolve uma Folha cujas primitivas vão para o bloco."""
        sub = Folha(self.E)
        self.blocos[nome] = sub.prims
        return sub

    def bloco_tqs(self, nome):
        """Bloco da biblioteca do TQS (carregado pelo caminho, sem extensão)."""
        self.blocos[nome] = None

    def regiao(self, nome, i0, i1=None):
        """Guarda a extensão das primitivas prims[i0:i1] como a região de uma vista (blocos e ferros incluídos)."""
        xs, ys = [], []
        for p in self.prims[i0:i1]:
            if p["t"] == "Bloco":
                for q in self.blocos.get(p["b"]) or []:
                    for x, y in _pontos(q):
                        X, Y = _transformar(x, y, p)
                        xs.append(X)
                        ys.append(Y)
                xs.append(p["x"])
                ys.append(p["y"])
            elif p["t"] == "Ferro":
                for i in p["ins"]:
                    a = math.radians(i.get("ang", 0.0))
                    L = p.get("comp") or 0.0
                    xs += [i["x"], i["x"] + L * math.cos(a)]
                    ys += [i["y"], i["y"] + L * math.sin(a)]
                for x, y in p.get("pontos") or []:
                    xs.append(p["ins"][0]["x"] + x)
                    ys.append(p["ins"][0]["y"] + y)
            else:
                for x, y in _pontos(p):
                    xs.append(x)
                    ys.append(y)
        if xs:
            self.regioes[nome] = (min(xs), min(ys), max(xs), max(ys))
        return self.regioes.get(nome)

    def extensao(self):
        xs, ys = [], []
        for p in self.prims:
            if p.get("xy"):
                xs += [q[0] for q in p["xy"]]
                ys += [q[1] for q in p["xy"]]
            elif p["t"] in ("Circulo", "Arco"):
                xs += [p["x"] - p["r"], p["x"] + p["r"]]
                ys += [p["y"] - p["r"], p["y"] + p["r"]]
            elif p["t"] == "Texto":
                larg = len(p["txt"]) * p["h"]
                a = math.radians(p["a"])
                xs += [p["x"], p["x"] + larg * math.cos(a)]
                ys += [p["y"], p["y"] + larg * math.sin(a) + p["h"]]
            elif p["t"] == "Cota":
                xs += [p["p1"][0], p["p2"][0], p["p3"][0]]
                ys += [p["p1"][1], p["p2"][1], p["p3"][1]]
            elif p["t"] == "Bloco":
                xs.append(p["x"])
                ys.append(p["y"])
        return min(xs), min(ys), max(xs), max(ys)


def _pontos(p):
    """Pontos que delimitam uma primitiva (linha, polilinha, círculo, arco, texto ou cota)."""
    if p.get("xy"):
        return [tuple(q) for q in p["xy"]]
    if p["t"] in ("Circulo", "Arco"):
        return [(p["x"] - p["r"], p["y"] - p["r"]), (p["x"] + p["r"], p["y"] + p["r"])]
    if p["t"] == "Texto":
        larg = len(p["txt"]) * p["h"]
        a = math.radians(p["a"])
        return [(p["x"], p["y"]), (p["x"] + larg * math.cos(a), p["y"] + larg * math.sin(a) + p["h"])]
    if p["t"] == "Cota":
        return [tuple(p["p1"]), tuple(p["p2"]), tuple(p["p3"])]
    return []


def _transformar(x, y, ins):
    """Ponto de um bloco levado para o desenho pela inserção (escala, giro em graus e translação)."""
    x, y = x * ins.get("sx", 1.0), y * ins.get("sy", 1.0)
    a = math.radians(ins.get("ang", 0.0))
    return ins["x"] + x * math.cos(a) - y * math.sin(a), ins["y"] + x * math.sin(a) + y * math.cos(a)


def contorno_barra(pontos, diam):
    """Contorno fechado de uma barra de eixo ortogonal (polilinha de pontos), com a bitola dada: offsets dos dois
    lados com cantos em esquadria, ligados nas pontas."""
    r = diam / 2.0

    def normal(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        return -dy / L, dx / L

    segs = [(pontos[i], pontos[i + 1]) for i in range(len(pontos) - 1) if pontos[i] != pontos[i + 1]]
    pts = [segs[0][0]] + [s[1] for s in segs]
    ns = [normal(a, b) for a, b in segs]
    lados = []
    for sinal in (1, -1):
        q = [(pts[0][0] + sinal * r * ns[0][0], pts[0][1] + sinal * r * ns[0][1])]
        for i in range(1, len(pts) - 1):
            n1, n2 = ns[i - 1], ns[i]
            q.append((pts[i][0] + sinal * r * (n1[0] + n2[0]), pts[i][1] + sinal * r * (n1[1] + n2[1])))
        q.append((pts[-1][0] + sinal * r * ns[-1][0], pts[-1][1] + sinal * r * ns[-1][1]))
        lados.append(q)
    return lados[0] + list(reversed(lados[1])) + [lados[0][0]]


def quebra(p1, p2, amp, frac=0.5):
    """Linha de quebra de p1 a p2 com o zigue-zague no meio (como nos cortes do modelo R01)."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    m = (p1[0] + dx * frac, p1[1] + dy * frac)
    w = amp / 3.0
    return [p1, (m[0] - ux * w, m[1] - uy * w), (m[0] + nx * amp, m[1] + ny * amp),
            (m[0] - nx * amp, m[1] - ny * amp), (m[0] + ux * w, m[1] + uy * w), p2]
