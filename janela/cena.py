# -*- coding: utf-8 -*-
"""
Prévia da prancha na área CAD da janela: desenha uma folha em primitivas (nucleo/folha.py) numa Vista
(janela/cad_vista.py), sem o TQS.

- Modo "tela": fundo preto e as cores de tela de cada nível (a tabela de níveis dos desenhos de referência), como no
  editor do TQS. Modo "plot": fundo branco, a cor e a espessura da pena de cada nível (TABPLTA), como no PDF.
- Blocos expandidos pela inserção; o `$CORTEA` da biblioteca do TQS é desenhado com a geometria lida do modelo.
- Cotas desenhadas como o TQS (linha de cota, chamadas, símbolo e o texto com a medida: inteiro ou com uma casa e
  ponto, "37.5"); ferros inteligentes com a linha (ou o ferro genérico pelos pontos) e o texto "8 N1 ø10 C=220".
- Cada primitiva recebe uma chave para a dica sob o mouse e a seleção: "f:i" ferro, "c:i" cota, "b:i" bloco (o
  pente inteiro) e "e:i" entidade; desenhar() devolve {chave: descrição}.
"""
import json
import math
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(RAIZ, "nucleo", "niveis.json"), encoding="utf-8") as _f:
    NIVEIS = json.load(_f)
PALETA = NIVEIS["paleta_tela"]
# $CORTEA (C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA): geometria lida do PUN_P02, em unidades do bloco
CORTEA = [((0.0, 0.0), (-1.216, 0.0)), ((-1.2131, 0.0017), (-1.0085, 0.4109)), ((-1.0085, 0.4109), (-0.8039, 0.0017))]
CORTEA_TRI = [(-1.2131, 0.0017), (-1.0085, 0.4109), (-0.8039, 0.0017)]
# Cotas (dwg_tqs/arquivo.COTA), em cm de papel
DIMEXO, DIMEXE, DIMTXT, R_DOT, GAP_TXT = 0.10, 0.10, 0.18, 0.035, 0.054


def titulo_nivel(n):
    return NIVEIS["niveis"].get(str(n), {}).get("titulo", "")


def _misturar(cor, pct, fundo="#ffffff"):
    r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
    R, G, B = (int(fundo[i:i + 2], 16) for i in (1, 3, 5))
    f = pct / 100.0
    return "#%02x%02x%02x" % (round(R + (r - R) * f), round(G + (g - G) * f), round(B + (b - B) * f))


def _fmt_medida(v):
    """Como o TQS escreve a medida da cota: inteiro, ou uma casa com ponto."""
    return str(int(round(v))) if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _br(v):
    return f"{v:.1f}".replace(".", ",")


class Pintor:
    def __init__(self, vista, modo="tela", escala=15.0):
        self.v, self.modo, self.E = vista, modo, escala
        self.plot = modo == "plot"
        self.fundo = "#ffffff" if self.plot else "#000000"
        self.info = {}

    # ------------------------------------------------------------------ cor, espessura e estilo pelo nível
    def cor(self, n, c=None):
        nv = NIVEIS["niveis"].get(str(n), {})
        if self.plot:
            cor = nv.get("cor_plot", "#000000")
            return "#c8c8c8" if cor.lower() == "#ffffff" else cor
        idx = c if isinstance(c, int) and c >= 0 else nv.get("cor_tela", 7)
        return PALETA.get(str(idx), "#ffffff")

    def largura(self, n):
        if not self.plot:
            return 1
        return max(1, round(NIVEIS["niveis"].get(str(n), {}).get("espessura", 0.2) * 3.3))

    def estilo(self, n, s):
        if s is None or s < 0:
            nv = NIVEIS["niveis"].get(str(n), {})
            s = nv.get("estilo_plot" if self.plot else "estilo_tela", 0)
        return {5: 1}.get(s, s) or None

    def preenchimento(self, n, cheia):
        """Cor do preenchimento: polilinha cheia, ou nível com hachura de porcentagem (240: 25 %)."""
        nv = NIVEIS["niveis"].get(str(n), {})
        hd = nv.get("hachura_def")
        if not cheia and not (hd and hd.get("tipo") == 4):
            return ""
        pct = 100 if cheia else hd["parametro"]
        if self.plot:
            base = nv.get("cor_plot", "#000000")
            base = "#000000" if base.lower() == "#ffffff" else base
            return _misturar(base, pct, "#ffffff")
        return _misturar(self.cor(n), min(pct, 35), "#000000")

    # ------------------------------------------------------------------ primitivas
    def linha(self, n, pts, s=None, c=None, chave=None):
        self.v.linha(pts, self.cor(n, c), self.largura(n), self.estilo(n, s), chave=chave)

    def circulo_pts(self, x, y, r, a1=0.0, a2=360.0):
        if a2 <= a1:
            a2 += 360.0
        n = max(8, int((a2 - a1) / 6))
        return [(x + r * math.cos(math.radians(a1 + (a2 - a1) * i / n)),
                 y + r * math.sin(math.radians(a1 + (a2 - a1) * i / n))) for i in range(n + 1)]

    def texto(self, n, x, y, h, txt, a=0.0, c=None, chave=None):
        if txt.strip():
            self.v.texto(x, y, txt.replace("{", "ø"), h, a, self.cor(n, c), chave=chave)

    def primitiva(self, p, chave, T=None):
        """Desenha uma primitiva; T transforma os pontos (blocos)."""
        T = T or (lambda x, y: (x, y))
        t, n = p["t"], p.get("n", 0)
        if t == "Linha":
            self.linha(n, [T(*q) for q in p["xy"]], p.get("s"), p.get("c"), chave)
        elif t == "Polyline":
            pts = [T(*q) for q in p["xy"]]
            fundo = self.preenchimento(n, p.get("fill"))
            fechada = len(pts) > 3 and math.dist(pts[0], pts[-1]) < 1e-6
            if fundo and fechada:
                return                                    # preenchimentos vão na 1ª passada
            self.linha(n, pts, p.get("s"), p.get("c"), chave)
        elif t in ("Circulo", "Arco"):
            a1, a2 = (0.0, 360.0) if t == "Circulo" else (p["a1"], p["a2"])
            pts = [T(*q) for q in self.circulo_pts(p["x"], p["y"], p["r"], a1, a2)]
            self.linha(n, pts, p.get("s"), p.get("c"), chave)
        elif t == "Texto":
            x, y = T(p["x"], p["y"])
            self.texto(n, x, y, p["h"], p["txt"], p.get("a", 0.0), p.get("c"), chave)

    def preencher(self, prims, blocos):
        """1ª passada: polígonos preenchidos (ficam por baixo das linhas)."""
        for p in prims:
            if p["t"] == "Polyline":
                fundo = self.preenchimento(p.get("n", 0), p.get("fill"))
                if fundo and len(p["xy"]) > 3 and math.dist(p["xy"][0], p["xy"][-1]) < 1e-6:
                    self.v.poli([tuple(q) for q in p["xy"]], contorno="", fundo=fundo)

    # ------------------------------------------------------------------ blocos, cotas e ferros
    def bloco(self, p, blocos, chave):
        def T(x, y):
            x, y = x * p.get("sx", 1.0), y * p.get("sy", 1.0)
            a = math.radians(p.get("ang", 0.0))
            return p["x"] + x * math.cos(a) - y * math.sin(a), p["y"] + x * math.sin(a) + y * math.cos(a)
        prims = blocos.get(p["b"])
        if prims is None:                                 # $CORTEA do TQS
            n = p.get("n", 226)
            for a, b in CORTEA:
                self.linha(n, [T(*a), T(*b)], chave=chave)
            self.v.poli([T(*q) for q in CORTEA_TRI], contorno=self.cor(n), fundo=self.cor(n), chave=chave)
            return
        for q in prims:
            self.primitiva(q, chave, T)

    def cota(self, p, chave):
        E = self.E
        (x1, y1), (x2, y2), (x3, y3) = p["p1"], p["p2"], p["p3"]
        modo = p["modo"]
        if modo == "h":
            u = (1.0, 0.0)
        elif modo == "v":
            u = (0.0, 1.0)
        elif modo == "a":
            L = math.hypot(x2 - x1, y2 - y1) or 1.0
            u = ((x2 - x1) / L, (y2 - y1) / L)
        else:
            a = math.radians(p.get("ang") or 0.0)
            u = (math.cos(a), math.sin(a))
        nrm = (-u[1], u[0])
        # linha de cota: pela reta que passa em p3 na direção u
        off = (x3 * nrm[0] + y3 * nrm[1])
        def proj(x, y):
            t = x * u[0] + y * u[1]
            return (t * u[0] + off * nrm[0], t * u[1] + off * nrm[1])
        a1, a2 = proj(x1, y1), proj(x2, y2)
        nl, nt = p["niveis"][1], p["niveis"][0]
        self.linha(nl, [a1, a2], chave=chave)
        for (px, py), (qx, qy) in (((x1, y1), a1), ((x2, y2), a2)):
            d = math.hypot(qx - px, qy - py)
            if d > DIMEXO * E:
                vx, vy = (qx - px) / d, (qy - py) / d
                self.linha(nl, [(px + vx * DIMEXO * E, py + vy * DIMEXO * E),
                                (qx + vx * DIMEXE * E, qy + vy * DIMEXE * E)], chave=chave)
            self.linha(nl, self.circulo_pts(qx, qy, R_DOT * E), chave=chave)
        med = abs((x2 - x1) * u[0] + (y2 - y1) * u[1]) * p.get("fator", 1.0)
        txt = p["txt"] if p.get("txt") not in (None, "") else _fmt_medida(med)
        ang = math.degrees(math.atan2(u[1], u[0]))
        if ang > 90.001 or ang <= -90.001:                 # texto legível
            ang += 180 if ang <= -90.001 else -180
            nrm = (-nrm[0], -nrm[1])
        h = DIMTXT * E
        larg = len(txt) * h * 0.82
        mx, my = (a1[0] + a2[0]) / 2, (a1[1] + a2[1]) / 2
        ur = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        nr = (-ur[1], ur[0])
        x0 = mx - ur[0] * larg / 2 + nr[0] * GAP_TXT * E
        y0 = my - ur[1] * larg / 2 + nr[1] * GAP_TXT * E
        self.texto(nt, x0, y0, h, txt, ang, chave=chave)
        return txt, med

    def ferro(self, p, chave, comps):
        ins = p["ins"][0]
        n = ins.get("nivel", 220)
        comp = p.get("comp") or comps.get(p["mark"])
        txt = f"{p['quant']}  N{p['mark']}  {{{p['bitola']:g}  C={comp}"
        h = 0.20 * self.E
        if p["tipo"] == "gen":
            pts = [(ins["x"] + x, ins["y"] + y) for x, y in p["pontos"]]
            self.linha(n, pts, chave=chave)
            tx = p.get("texto") or dict(x=pts[0][0], y=pts[0][1] - 0.6 * self.E, ang=0.0)
            self.texto(1, tx["x"], tx["y"], h, txt, tx.get("ang", 0.0), chave=chave)
            return txt
        a = math.radians(ins.get("ang", 0.0))
        u = (math.cos(a), math.sin(a))
        nrm = (-u[1], u[0])
        L = p.get("reto", p["comp"])                     # com gancho, o C inclui o gancho (E9)
        x2, y2 = ins["x"] + L * u[0], ins["y"] + L * u[1]
        self.linha(n, [(ins["x"], ins["y"]), (x2, y2)], chave=chave)
        g = 8 * p["bitola"] / 10.0 + 3.5 * p["bitola"] / 10.0      # gancho de 90° esquemático: 8ø + raio externo
        for tem, (gx, gy) in zip(p.get("ganchos") or (), ((ins["x"], ins["y"]), (x2, y2))):
            if tem:
                self.linha(n, [(gx, gy), (gx + nrm[0] * g, gy + nrm[1] * g)], chave=chave)
        larg = len(txt) * h * 0.82
        mx, my = (ins["x"] + x2) / 2, (ins["y"] + y2) / 2
        self.texto(1, mx - u[0] * larg / 2 + nrm[0] * 0.1 * self.E, my - u[1] * larg / 2 + nrm[1] * 0.1 * self.E,
                   h, txt, ins.get("ang", 0.0), chave=chave)
        return txt


def desenhar(vista, folha, modo="tela", ferros=None):
    """Desenha a folha na vista (limpa antes). ferros = res["ferros"] (descrição e comprimento dos genéricos).
    Devolve {chave: descrição} para a dica e a seleção."""
    vista.limpar()
    vista.configure(bg="#ffffff" if modo == "plot" else "#000000")
    pt = Pintor(vista, modo, folha.E)
    desc = {f["pos"]: f for f in (ferros or [])}
    comps = {k: f["comp"] for k, f in desc.items()}
    pt.preencher(folha.prims, folha.blocos)
    for i, p in enumerate(folha.prims):
        t = p["t"]
        if t == "Bloco":
            ch = f"b:{i}"
            pt.bloco(p, folha.blocos, ch)
            nome = "marca de corte ($CORTEA)" if folha.blocos.get(p["b"]) is None else p["b"]
            pt.info[ch] = f"{nome} em ({_br(p['x'])}; {_br(p['y'])}), {p.get('ang', 0) % 360:g}°"
        elif t == "Cota":
            ch = f"c:{i}"
            txt, med = pt.cota(p, ch)
            pt.info[ch] = f"Cota {txt} (medida {_br(med)} cm)"
        elif t == "Ferro":
            ch = f"f:{p['mark']}"
            txt = pt.ferro(p, ch, comps)
            d = desc.get(p["mark"], {})
            pt.info[ch] = f"N{p['mark']}: {txt.replace('{', 'ø')}" + (f" - {d['descricao']}" if d.get("descricao") else "")
        else:
            ch = f"e:{i}"
            pt.primitiva(p, ch)
            pt.info[ch] = _descrever(p)
    return pt.info


def _descrever(p):
    n = p.get("n", 0)
    t = p["t"]
    nome = {"Linha": "Linha", "Polyline": "Polilinha", "Circulo": "Círculo", "Arco": "Arco", "Texto": "Texto"}[t]
    s = f"{nome}, nível {n} ({titulo_nivel(n)})"
    if t == "Linha":
        s += f", L = {_br(math.dist(*p['xy']))} cm"
    elif t == "Polyline":
        s += f", perímetro {_br(sum(math.dist(a, b) for a, b in zip(p['xy'], p['xy'][1:])))} cm"
    elif t == "Circulo":
        s += f", ø {_br(2 * p['r'])} cm"
    elif t == "Texto":
        s += f": {p['txt'].strip()}"
    return s
