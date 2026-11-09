# -*- coding: utf-8 -*-
"""
Prancha dos conectores (pilar interno) em primitivas, no padrão do desenho de referência PUN_P02
(PADRAO_desenho.md), com as correções aprovadas: pino ø10 com cabeça de 32 mm e trilhos ø8 com a largura real
(seção 11). Sem o TQS.

Vistas (origem no canto inferior esquerdo do pilar na planta):
- VISTA EM PLANTA (PINOS): pilar, contornos das linhas de pinos (nível 200), pentes (bloco `PUN nP s cm`), eixos,
  cotas (entre pentes, entre os pinos de fora nos cantos e da face aos pinos), marcas do corte A-A e as linhas de
  identificação do colapso (N1 em cima, N2 à direita), com as cotas de col_ext;
- VISTA EM PLANTA (COLAPSO PROGRESSIVO), à direita, alinhada com a planta;
- CORTE A-A, embaixo: laje e pilar cortados, os pinos dos pentes das faces esquerda e direita (bloco
  `Pino L cm em corte`), as barras de flexão de referência (nota 1) e o colapso; abaixo, o pente sozinho, com as
  cotas da altura e dos espaçamentos (notas 2 e 3);
- quadro "ARMADURA DE COMBATE À PUNÇÃO" (canto superior direito), NOTAS IMPORTANTES (canto inferior direito) e
  título (nome, "Nx" e dimensões).

As posições e afastamentos que não dependem da geometria do pilar são os do modelo, em cm de desenho na escala 15,
convertidos para cm de papel (÷ 15) e multiplicados pela escala do pilar.
"""
import math

from .conectores import nome_bloco
from .folha import (Folha, H_CHAMADA, H_ESCALA, H_LETRA, H_NOTA, H_NOTAS_TIT, H_NX, H_QUADRO, H_TITULO,
                    H_VISTA, quebra)
from .parametros import cobrimento_borda

NOTAS = [
    "NO MÍNIMO UMA EXTREMIDADE ALARGADA DA ARMADURA DE PUNÇÃO DE CADA PENTE DEVERÁ CONTER UMA BARRA DA ARMADURA "
    "DE FLEXÃO DA LAJE.",
    "COTAGEM EM RELAÇÃO AO EIXOS DOS PINOS DA ARMADURA DE COMBATE À PUNÇÃO.",
    "AS ARMADURAS DE COMBATE À PUNÇÃO DEVERÃO SER LOCADAS COM BASE NAS COTAGENS REPRESENTADAS NESTE DESENHO, "
    "ADMITINDO-SE UMA VARIAÇÃO MÁXIMA IGUAL A MEIO DIÂMETRO DO PINO DE PUNÇÃO.",
]
CORTEA = "C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA"
ESC_CORTEA = 13.980263157894738 / 15.0          # escala do $CORTEA no modelo, por unidade de escala do desenho
CABECA_T, CABECA_C = 0.8, 0.2                    # cabeça do pino em corte: chapa e concordância até o fuste (cm)


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


def _ganchos(barra):
    """Ganchos de 90° do ferro de colapso (só quando há: a folha do pilar interno não muda)."""
    return dict(ganchos=barra["ganchos"], reto=barra["reto"]) if any(barra.get("ganchos") or ()) else {}


def _sem_repetidos(pts):
    """Polilinha sem pontos consecutivos repetidos (o pilar faceando a borda repete pontos no corte)."""
    out = []
    for q in pts:
        if not out or abs(q[0] - out[-1][0]) + abs(q[1] - out[-1][1]) > 1e-6:
            out.append(q)
    return out


def _linhas_notas(largura=51):
    """Linhas das notas: [(nº da nota ou None, texto)]; a 1ª de cada nota leva 8 espaços para o "NOTA n:"."""
    linhas = []
    for i, nota in enumerate(NOTAS, 1):
        primeira = _quebrar(nota, largura - 8)[0]
        linhas.append((i, "        " + primeira))
        resto = nota[len(primeira):].strip()
        for txt in (_quebrar(resto, largura) if resto else []):
            linhas.append((None, txt))
    return linhas


class Prancha:
    def __init__(self, res):
        self.r, self.p, self.c = res, res["p"], res["conectores"]
        p, c = self.p, self.c
        self.E = E = p["escala"]
        self.k = E / 15.0                         # afastamentos do modelo (escala 15) na escala do pilar
        self.f = Folha(E)
        self.bx, self.by, self.h = p["bx"], p["by"], p["h_laje"]
        self.R = c["contornos"][-1]
        self.D = c["pino"]["cabeca_mm"] / 10.0    # diâmetro da cabeça (cm)
        self.rf = c["pino"]["bitola"] / 20.0      # raio do fuste
        self.L = c["pino"]["comprimento_mm"] / 10.0
        self.wt = c["trilhos"]["bitola"] / 10.0   # largura do trilho
        self.at = c["trilhos"]["afast"]           # eixo do trilho ao eixo dos pinos
        self.ext = p["col_ext"]
        self.pos = {}
        for fe in res["ferros"]:
            self.pos[(fe["tipo"], fe.get("subtipo") or fe.get("direcao"))] = fe
        self.bd = c.get("bordas") or {}           # faces voltadas para uma borda livre -> distância (E9)
        self.cb = cobrimento_borda(p)
        # Corte A-A: pela fileira de pentes das faces esquerda e direita mais perto do meio do pilar.
        laterais = [pt for pt in c["pentes"] if pt["face"] in ("esquerda", "direita") and pt["tipo"] == "face"]
        self.y_corte = min({pt["y"] for pt in laterais}, key=lambda y: (abs(y - self.by / 2), y))
        self.pentes_corte = sorted((pt for pt in laterais if abs(pt["y"] - self.y_corte) < 1e-6),
                                   key=lambda pt: pt["x"])
        # Identificação do colapso (N1 em cima, N2 à direita): fora das cotas da planta.
        folga = max(self.ext, self.R + 40 * self.k)
        self.y_n1 = self.by + folga + 15 * self.k
        self.x_n2 = self.bx + folga + 14 * self.k
        self.y_tit = self.y_n1 + 18 * self.k
        self.x_esq = min(-self.R - 53 * self.k, -self.ext - 13 * self.k)
        self.X0 = self.x_n2 + 35 * self.k + self.ext          # pilar da vista do colapso

    # ------------------------------------------------------------------ blocos
    def _bloco_pente(self, n=None):
        """Pente de n pinos em planta: 1º pino na origem, os outros em +x; cabeças no 241, fustes no 245 e os dois
        trilhos no 0, com a largura real, um de cada lado, cada um com gancho numa ponta (como o bloco do modelo).
        Com borda livre, pode haver pentes mais curtos (E9): um bloco por nº de pinos."""
        f = self.f
        s0, sr = self.p["con_s0"], self.p["con_sr"]
        n = n or self.p["con_pinos"]
        nome = nome_bloco(n, sr)
        b = f.novo_bloco(nome)
        comp = (n - 1) * sr
        for i in range(n):
            b.circ(241, i * sr, 0.0, self.D / 2)
            b.circ(245, i * sr, 0.0, self.rf)
        a, w = self.at, self.wt
        R = 1.6 * a                                       # raio do gancho pelo eixo (modelo: 3,0 com 1,875)
        xg = comp + self.D / 2                            # início do gancho: além da cabeça da ponta
        for lado in (1, -1):
            # lado +1: trilho de cima, do 1º pino até além do último, gancho para baixo; lado -1: espelhado
            if lado == 1:
                x_ini, x_fim, cx = 0.0, xg, xg
            else:
                x_ini, x_fim, cx = comp, -self.D / 2, -self.D / 2
            cy = lado * (a - R)
            for e in (w / 2, -w / 2):
                y = lado * (a + e)
                b.linha(0, (x_ini, y), (x_fim, y))
            # o gancho vira até a face de dentro do outro trilho
            y_alvo = -lado * (a - w / 2)
            ang = math.degrees(math.asin(max(-1.0, min(1.0, (y_alvo - cy) / (R + w / 2)))))
            if lado == 1:
                a1, a2 = (360 + ang) % 360, 90.0          # do fim do gancho (≈ 354°) ao topo, sentido anti-horário
            else:
                a1, a2 = 180 - ang, 270.0                 # do fim do gancho (≈ 174°) à base
            b.arco(0, cx, cy, R + w / 2, a1, a2)
            b.arco(0, cx, cy, R - w / 2, a1, a2)
            t = math.radians(a1)
            b.linha(0, (cx + (R + w / 2) * math.cos(t), cy + (R + w / 2) * math.sin(t)),
                    (cx + (R - w / 2) * math.cos(t), cy + (R - w / 2) * math.sin(t)))
        return nome

    def _bloco_pino_corte(self):
        """Pino em corte (nível 241): cabeças de D x 0,8, concordância de 0,2 até o fuste; origem no canto de baixo
        à esquerda da cabeça de baixo."""
        D, L, df = self.D, self.L, 2 * self.rf
        nome = f"Pino {_fmt(L)} cm em corte"
        b = self.f.novo_bloco(nome)
        x1, x2 = (D - df) / 2, (D + df) / 2
        t, c = CABECA_T, CABECA_C
        b.poli(241, [(0, 0), (D, 0), (D, t), (x2, t + c), (x2, L - t - c), (D, L - t), (D, L), (0, L), (0, L - t),
                     (x1, L - t - c), (x1, t + c), (0, t)], fechar=True)
        return nome

    # ------------------------------------------------------------------ planta dos pinos
    def _limites(self, folga=None):
        """Retângulo da laje em volta do pilar: (x0, x1, y0, y1), até as bordas livres; dos lados livres, folga
        além das faces (sem folga: None, sem limite)."""
        bd, bx, by = self.bd, self.bx, self.by
        livre = lambda v: None if folga is None else v                                     # noqa: E731
        return (-bd["esquerda"] if "esquerda" in bd else livre(-folga if folga else 0),
                bx + bd["direita"] if "direita" in bd else livre(bx + (folga or 0)),
                -bd["baixo"] if "baixo" in bd else livre(-folga if folga else 0),
                by + bd["cima"] if "cima" in bd else livre(by + (folga or 0)))

    def _dentro(self, x, y):
        x0, x1, y0, y1 = self._limites()
        return ((x0 is None or x >= x0 - 1e-9) and (x1 is None or x <= x1 + 1e-9)
                and (y0 is None or y >= y0 - 1e-9) and (y1 is None or y <= y1 + 1e-9))

    def _linha_recortada(self, n, p1, p2, s=None):
        """Linha horizontal ou vertical recortada pela laje (bordas livres)."""
        x0, x1, y0, y1 = self._limites()
        (xa, ya), (xb, yb) = p1, p2
        if abs(ya - yb) < 1e-9:                           # horizontal
            if not ((y0 is None or ya >= y0 - 1e-9) and (y1 is None or ya <= y1 + 1e-9)):
                return
            lo, hi = sorted((xa, xb))
            lo, hi = max(lo, x0) if x0 is not None else lo, min(hi, x1) if x1 is not None else hi
            if hi - lo > 1e-6:
                self.f.linha(n, (lo, ya) if xa <= xb else (hi, ya), (hi, ya) if xa <= xb else (lo, ya), s=s)
        else:                                             # vertical
            if not ((x0 is None or xa >= x0 - 1e-9) and (x1 is None or xa <= x1 + 1e-9)):
                return
            lo, hi = sorted((ya, yb))
            lo, hi = max(lo, y0) if y0 is not None else lo, min(hi, y1) if y1 is not None else hi
            if hi - lo > 1e-6:
                self.f.linha(n, (xa, lo) if ya <= yb else (xa, hi), (xa, hi) if ya <= yb else (xa, lo), s=s)

    def _arco_recortado(self, n, cx, cy, r, a1, a2, s=None):
        """Arco (graus, anti-horário de a1 a a2) só com os trechos dentro da laje: amostrado a cada grau e com as
        pontas acertadas por bisseção."""
        dentro = lambda t: self._dentro(cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t)))  # noqa
        passos = max(2, int(math.ceil(a2 - a1)))
        ts = [a1 + (a2 - a1) * i / passos for i in range(passos + 1)]

        def borda(t_in, t_out):
            for _ in range(30):
                m = (t_in + t_out) / 2
                t_in, t_out = (m, t_out) if dentro(m) else (t_in, m)
            return t_in
        ini = None
        for i, t in enumerate(ts):
            if dentro(t) and ini is None:
                ini = t if i == 0 else borda(t, ts[i - 1])
            if ini is not None and (not dentro(t) or i == len(ts) - 1):
                fim = t if dentro(t) else borda(ts[i - 1], t)
                if fim - ini > 1e-3:
                    self.f.arco(n, cx, cy, r, ini, fim, s=s)
                ini = None

    def _contorno(self, a):
        bx, by, f = self.bx, self.by, self.f
        if self.bd:                                       # recortado nas bordas livres (E9)
            lin, arc = self._linha_recortada, self._arco_recortado
            lin(200, (0, -a), (bx, -a), s=2)
            arc(200, bx, 0, a, 270, 360, s=2)
            lin(200, (bx + a, 0), (bx + a, by), s=2)
            arc(200, bx, by, a, 0, 90, s=2)
            lin(200, (bx, by + a), (0, by + a), s=2)
            arc(200, 0, by, a, 90, 180, s=2)
            lin(200, (-a, by), (-a, 0), s=2)
            arc(200, 0, 0, a, 180, 270, s=2)
            return
        f.linha(200, (0, -a), (bx, -a), s=2)
        f.arco(200, bx, 0, a, 270, 360, s=2)
        f.linha(200, (bx + a, 0), (bx + a, by), s=2)
        f.arco(200, bx, by, a, 0, 90, s=2)
        f.linha(200, (bx, by + a), (0, by + a), s=2)
        f.arco(200, 0, by, a, 90, 180, s=2)
        f.linha(200, (-a, by), (-a, 0), s=2)
        f.arco(200, 0, 0, a, 180, 270, s=2)

    def planta(self):
        f, E, k, p, c = self.f, self.E, self.k, self.p, self.c
        bx, by, R = self.bx, self.by, self.R
        f.retangulo(203, 0, 0, bx, by, s=1)
        f.retangulo(240, 0, 0, bx, by)
        for a in c["contornos"]:
            self._contorno(a)
        n = p["con_pinos"]
        nomes = {t["n_pinos"]: self._bloco_pente(t["n_pinos"]) for t in c.get("tipos") or [dict(n_pinos=n)]}
        for pt in c["pentes"]:
            f.bloco(nomes[pt.get("n_pinos") or n], pt["x"], pt["y"], pt["ang"], n=0)
        self._bordas_planta()
        for b in c["montagem"]:
            f.linha(243, b["p1"], b["p2"])
        # cotas entre os pinos de fora de pentes vizinhos: ao longo das faces e nos cantos
        off = 10 * k
        porface = {}
        for pt in c["pentes"]:
            porface.setdefault(pt["face"], []).append(pt["pinos"][-1])
        for face, pts in porface.items():
            if face.startswith("canto") or len(pts) < 2:
                continue
            pts = sorted(pts)
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if face == "esquerda":
                    f.cota((x1, y1), (x2, y2), (x1 - off, y1), modo="v")
                elif face == "direita":
                    f.cota((x1, y1), (x2, y2), (x1 + off, y1), modo="v")
                elif face == "baixo":
                    f.cota((x1, y1), (x2, y2), (x1, y1 - off), modo="h")
                else:
                    f.cota((x1, y1), (x2, y2), (x1, y1 + off), modo="h")
        centro = (bx / 2, by / 2)
        for v in c["vizinhos"]:
            if not v["canto"] or v.get("borda"):          # do lado da borda, o contorno termina nela
                continue
            a, b = c["pentes"][v["i"]]["pinos"][-1], c["pentes"][v["j"]]["pinos"][-1]
            if (b[0], b[1]) < (a[0], a[1]):               # da esquerda para a direita: o texto não fica invertido
                a, b = b, a
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            L = math.dist(a, b)
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            if (m[0] - centro[0]) * nx + (m[1] - centro[1]) * ny < 0:
                nx, ny = -nx, -ny
            f.cota(a, b, (m[0] + nx * off, m[1] + ny * off), modo="a", txt=f"{v['dist']:.0f}")
        # da face aos pinos: na fileira do corte (sobre o eixo dos pinos) e num pente de baixo e de cima
        # (só nas faces que têm pentes, com os pinos deles: na borda, pode faltar uma face ou haver pentes curtos)
        s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
        marcos = [0.0] + [-(s0 + i * sr) for i in range(n)]
        y = self.y_corte
        npin = lambda pts: max((pt["n_pinos"] or n for pt in pts), default=0)                # noqa: E731
        m_esq = npin(pt for pt in self.pentes_corte if pt["face"] == "esquerda")
        m_dir = npin(pt for pt in self.pentes_corte if pt["face"] == "direita")
        for i, (a_, b_) in enumerate(zip(marcos, marcos[1:])):
            if i < m_esq:
                f.cota((a_, y), (b_, y), (a_, y), modo="h")
            if i < m_dir:
                f.cota((bx - a_, y), (bx - b_, y), (bx - a_, y), modo="h")
        baixo = [pt for pt in c["pentes"] if pt["face"] == "baixo" and pt["tipo"] == "face"]
        cima = [pt for pt in c["pentes"] if pt["face"] == "cima" and pt["tipo"] == "face"]
        perto = lambda pts: min((pt["x"] for pt in pts), key=lambda x: (abs(x - bx / 2), x))   # noqa: E731
        xv_b = perto(baixo or cima) - self.at - self.wt / 2 - 1.5 * k
        xv_c = perto(cima or baixo) - self.at - self.wt / 2 - 1.5 * k
        m_b, m_c = npin(baixo), npin(cima)
        for i, (a_, b_) in enumerate(zip(marcos, marcos[1:])):
            if i < m_b:
                f.cota((xv_b, a_), (xv_b, b_), (xv_b, a_), modo="v")
            if i < m_c:
                f.cota((xv_c, by - a_), (xv_c, by - b_), (xv_c, by - a_), modo="v")
        # eixos (faces do pilar prolongadas, sem passar da borda livre da esquerda), marcas do corte e títulos
        f.linha(204, (bx + 3 * k, 0), (self.X0 - 3 * k, 0), s=3)
        f.linha(204, (bx + 3 * k, by), (self.X0 - 3 * k, by), s=3)
        xl = -R - 28 * k if "esquerda" not in self.bd else max(-R - 28 * k, -self.bd["esquerda"])
        if xl < -3 * k - 1e-6:
            f.linha(204, (-3 * k, 0), (xl, 0), s=3)
            f.linha(204, (-3 * k, by), (xl, by), s=3)
        for x in (0.0, bx):
            f.linha(204, (x, by + 3 * k), (x, self.y_n1 - 15 * k), s=3)
        f.bloco_tqs(CORTEA)
        esc = ESC_CORTEA * E
        xm = -R - 30 * k
        f.bloco(CORTEA, xm, y, 0.0, sx=esc, sy=esc, n=226)
        f.texto(226, xm - 7 * k, y + 2.5 * k, H_LETRA, "A")
        f.texto(226, self.x_esq, self.y_tit, H_VISTA, "VISTA EM PLANTA (PINOS)")
        f.texto(0, self.x_esq, self.y_tit - 6 * k, H_ESCALA, f"ESCALA 1:{E:g}")

    def _texto_largura(self, txt, h_papel):
        return len(txt) * h_papel * self.E * 0.92

    def _linha_borda(self, p1, p2, sinal):
        """Linha da borda livre (nível 0; o 240 é a hachura de 25 % e não sai na plotagem) de p1 a p2 (horizontal ou vertical) e o texto "BORDA LIVRE" paralelo a ela, do
        lado de fora da laje (sinal +1: x ou y maior), perto do fim da linha (como na prancha da cobrinha)."""
        f, E = self.f, self.E
        (x1, y1), (x2, y2) = p1, p2
        f.linha(0, (x1, y1), (x2, y2))
        larg = self._texto_largura("BORDA LIVRE", H_CHAMADA)
        if abs(y2 - y1) < 1e-9:
            ty = y1 + (0.2 * E if sinal > 0 else -0.2 * E - H_CHAMADA * E)
            f.texto(221, max(x1, x2) - larg - 0.3 * E, ty, H_CHAMADA, "BORDA LIVRE")
        else:
            tx = x1 + (0.2 * E + H_CHAMADA * E if sinal > 0 else -0.2 * E)
            f.texto(221, tx, max(y1, y2) - larg - 0.3 * E, H_CHAMADA, "BORDA LIVRE", a=90.0)

    def _bordas_vista(self, X0, folga):
        """Bordas livres de uma vista com o pilar em (X0, 0): a linha de cada borda até folga além das faces livres."""
        if not self.bd:
            return
        x0, x1, y0, y1 = self._limites(folga)
        x0, x1 = X0 + x0, X0 + x1
        for lado in self.bd:
            if lado == "esquerda":
                self._linha_borda((x0, y0), (x0, y1), -1)
            elif lado == "direita":
                self._linha_borda((x1, y0), (x1, y1), 1)
            elif lado == "baixo":
                self._linha_borda((x0, y0), (x1, y0), -1)
            else:
                self._linha_borda((x0, y1), (x1, y1), 1)

    def _bordas_planta(self):
        self._bordas_vista(0.0, self.R + 15 * self.k)

    def colapso_identificacao(self):
        """N1 (em x) acima da planta e N2 (em y) à direita, com as cotas de col_ext e as legendas, como no modelo."""
        f, k, bx, by, ext = self.f, self.k, self.bx, self.by, self.ext
        fx, fy = self.pos[("colapso", "x")], self.pos[("colapso", "y")]
        col_x, col_y = self.r["colapso"]
        atrib = dict(zona=1, cobrimento=self.p["c_inf"], atributos=dict(bendDimRadius=0))
        y1 = self.y_n1
        f.ferro(dict(tipo="reto", mark=fx["pos"], quant=fx["quant"], bitola=fx["bitola"], comp=fx["comp"],
                     ins=[dict(x=col_x["ini"], y=y1, ang=0.0, nivel=246, ipatas=1)], **atrib, **_ganchos(col_x)))
        # além das faces: col_ext do lado livre; do lado de uma borda, da face até a ponta (no cobrimento), se houver
        if not col_x.get("borda_ini") or -col_x["ini"] > 0.5:
            f.cota((col_x["ini"], y1 - 5 * k), (0, y1 - 20 * k), (col_x["ini"], y1 - 20 * k), modo="h")
        if not col_x.get("borda_fim") or col_x["fim"] - bx > 0.5:
            f.cota((bx, y1 - 20 * k), (col_x["fim"], y1 - 5 * k), (bx, y1 - 20 * k), modo="h")
        for txt, n, dy in (("(barras contra colapso progressivo)", 0, 6.4), ("ARMADURA DA FACE INFERIOR", 226, 13.5)):
            larg = len(txt) * H_NOTA * self.E
            f.texto(n, bx / 2 - larg / 2, y1 - dy * k, H_NOTA, txt)
        x2 = self.x_n2
        f.ferro(dict(tipo="reto", mark=fy["pos"], quant=fy["quant"], bitola=fy["bitola"], comp=fy["comp"],
                     ins=[dict(x=x2, y=col_y["ini"], ang=90.0, nivel=246, ipatas=1)], **atrib, **_ganchos(col_y)))
        if not col_y.get("borda_ini") or -col_y["ini"] > 0.5:
            f.cota((x2 - 15 * k, 0), (x2, col_y["ini"]), (x2 - 15 * k, 0), modo="v")
        if not col_y.get("borda_fim") or col_y["fim"] - by > 0.5:
            f.cota((x2 - 15 * k, by), (x2, col_y["fim"]), (x2 - 15 * k, by), modo="v")
        for txt, n, dx in (("(barras contra colapso progressivo)", 0, 6.4), ("ARMADURA DA FACE INFERIOR", 226, 13.9)):
            larg = len(txt) * H_NOTA * self.E
            f.texto(n, x2 + dx * k, by / 2 - larg / 2, H_NOTA, txt, a=90)

    # ------------------------------------------------------------------ colapso
    def colapso(self):
        f, X0 = self.f, self.X0
        f.retangulo(203, X0, 0, X0 + self.bx, self.by, s=1)
        f.retangulo(240, X0, 0, X0 + self.bx, self.by)
        col_x, col_y = self.r["colapso"]
        for v in col_x["pos"]:
            f.linha(245, (X0 + col_x["ini"], v), (X0 + col_x["fim"], v))
        for v in col_y["pos"]:
            f.linha(245, (X0 + v, col_y["ini"]), (X0 + v, col_y["fim"]))
        self._bordas_vista(X0, self.ext + 10 * self.k)
        # marca A da direita: além do colapso, na linha do corte (no modelo, em x = 411)
        k, esc, y = self.k, ESC_CORTEA * self.E, self.y_corte
        self.x_marca_dir = self.X0 + self.bx + self.ext + 7 * k
        f.bloco(CORTEA, self.x_marca_dir, y, 0.0, sx=-esc, sy=esc, n=226)
        f.texto(226, self.x_marca_dir + 4.5 * k, y + 2.5 * k, H_LETRA, "A")
        f.texto(226, self.x_n2, self.y_tit, H_VISTA, "VISTA EM PLANTA (COLAPSO PROGRESSIVO)")
        f.texto(0, self.x_n2, self.y_tit - 6 * self.k, H_ESCALA, f"ESCALA 1:{self.E:g}")

    # ------------------------------------------------------------------ corte A-A e pente
    def _barra_interrompida(self, n, x1, x2, z1, z2, furos):
        """Barra longitudinal no corte (duas linhas), interrompida nos fustes dos pinos, com as pontas fechadas."""
        f, rf = self.f, self.rf
        trechos, x = [], x1
        for xp in sorted(furos):
            if x1 < xp < x2:
                trechos.append((x, xp - rf))
                x = xp + rf
        trechos.append((x, x2))
        for a, b in trechos:
            f.linha(n, (a, z1), (b, z1))
            f.linha(n, (a, z2), (b, z2))
        f.linha(n, (x1, z1), (x1, z2))
        f.linha(n, (x2, z1), (x2, z2))

    def _pinos(self, nome_pino, z0):
        """Pinos dos pentes do corte, com os trilhos entre as cabeças de baixo."""
        f, D = self.f, self.D
        xs = []
        for pt in self.pentes_corte:
            px = [q[0] for q in pt["pinos"]]
            for x in px:
                f.bloco(nome_pino, x - D / 2, z0, n=0)
            px = sorted(px)
            for a, b in zip(px, px[1:]):
                f.linha(0, (a + D / 2, z0), (b - D / 2, z0))
                f.linha(0, (a + D / 2, z0 + self.wt), (b - D / 2, z0 + self.wt))
            xs += px
        return xs

    def corte(self):
        f, E, k, p = self.f, self.E, self.k, self.p
        bx, h, R = self.bx, self.h, self.R
        # posição: abaixo da planta e, se o corte chegar à linha do N2, abaixo dela também
        Yt = -R - 85 * k
        # a laje termina reta na borda livre (E9) e numa linha de quebra do lado livre
        b_esq, b_dir = self.bd.get("esquerda"), self.bd.get("direita")
        xa = -(R + 40 * k) if b_esq is None else -b_esq
        xb = bx + R + 45 * k if b_dir is None else bx + b_dir
        if xb + h / 2.8 > self.x_n2 - 15 * k - 0.5 * E:
            Yt = min(Yt, -self.ext - 1.0 * E)
        Yb = Yt - h
        zp = 2.0 * E
        qb = [] if b_dir is not None else quebra((xb, Yt), (xb, Yb), h / 2.8)[1:-1]
        qa = [] if b_esq is not None else quebra((xa, Yb), (xa, Yt), h / 2.8)[1:-1]
        # quebra do pilar: a do modelo (bx = 50: 50/2,8), sem crescer com pilares largos, em que invadia o pente
        aq = min(bx, 50.0 * k) / 2.8
        pts = [(0, Yt), (0, Yt + zp)] + quebra((0, Yt + zp), (bx, Yt + zp), aq)[1:-1]
        pts += [(bx, Yt + zp), (bx, Yt), (xb, Yt)] + qb
        pts += [(xb, Yb), (bx, Yb), (bx, Yb - zp)] + quebra((bx, Yb - zp), (0, Yb - zp), aq)[1:-1]
        pts += [(0, Yb - zp), (0, Yb), (xa, Yb)] + qa + [(xa, Yt)]
        if self.bd:
            pts = _sem_repetidos(pts)
        f.poli(0, pts, fechar=True)
        f.poli(240, pts, fechar=True)
        # NOTA 1 do lado que tem pentes (a direita, como no modelo); "TOPO LAJE" do lado livre ou, sem ele, fora
        # da laje, além da borda
        nome_pino = self._bloco_pino_corte()
        nota_dir = any(pt["face"] == "direita" for pt in self.pentes_corte)
        larg_topo = self._texto_largura("TOPO LAJE", H_CHAMADA)
        if not nota_dir:
            x_topo = xb + 0.5 * E
        elif b_esq is not None:
            x_topo = xa - larg_topo - 0.5 * E
        else:
            x_topo = xa
        f.texto(253, x_topo, Yt + 3 * k, H_CHAMADA, "TOPO LAJE")
        y_tit = Yt + 47 * k
        x_tit = min(xa, x_topo)
        f.texto(226, x_tit, y_tit, H_VISTA, "CORTE A-A")
        f.texto(0, x_tit, y_tit - 6 * k, H_ESCALA, f"ESCALA 1:{E:g}")
        z0 = Yb + p["c_inf"]
        xs = self._pinos(nome_pino, z0)
        # barras de flexão de referência: negativa e positiva junto de cada pino (nota 1), colapso N1 e N2
        e = p["con_cabeca_esp"]
        f1, f2, fc = p["neg_bitola_ext"] / 10, p["neg_bitola_int"] / 10, p["col_bitola"] / 10
        zs = Yt - p["c_sup"] - e
        xl1 = xa + (0.3 * E if b_esq is None else self.cb)
        xl2 = xb - (0.3 * E if b_dir is None else self.cb)
        self._barra_interrompida(0, xl1, xl2, zs, zs - f1, xs)
        zi = Yb + p["c_inf"] + e
        col_x, col_y = self.r["colapso"]
        self._barra_interrompida(245, max(col_x["ini"], xl1), min(col_x["fim"], xl2), zi, zi + fc, xs)
        topo = []
        for x in xs:
            xc = x + self.rf + f2 / 2
            topo.append((xc, zs - f1 - f2 / 2))
            f.circ(0, xc, zs - f1 - f2 / 2, f2 / 2)
            f.circ(0, x + self.rf + f2 / 2, zi + fc + f2 / 2, f2 / 2)
        zc = zi + fc + fc / 2
        for x in col_y["pos"]:
            f.circ(245, x, zc, fc / 2)
            f.linha(221, (x, zc - fc / 2), (x, Yb - 2 * k))
        if len(col_y["pos"]) > 1:
            f.linha(221, (col_y["pos"][0], Yb - 2 * k), (col_y["pos"][-1], Yb - 2 * k))
        fy = self.pos[("colapso", "y")]
        rot = f"N{fy['pos']}"
        f.texto(221, bx / 2 - len(rot) * 0.2 * E / 2, Yb - 6.5 * k, 0.2, rot)
        for b in self.c["montagem"]:
            if b["grupo"].startswith("by"):
                fm = p["mont_bitola"] / 10
                xb_ = b["p1"][0]
                f.circ(243, xb_, z0 + self.wt + fm / 2, fm / 2)
        # NOTA 1: chamadas das barras de cima do pente da direita (sem ele, borda faceando: as do pente da esquerda)
        yn = Yt + 6.5 * k
        if nota_dir:
            dir_ = [q for q in topo if q[0] > bx]
            for xc, zc_ in dir_:
                f.linha(221, (xc, zc_), (xc + 5.25 * k, yn))
            if dir_:
                f.linha(221, (dir_[0][0] + 5.25 * k, yn), (xb, yn))
            f.texto(221, xb - 6 * H_CHAMADA * E, Yt + 8.5 * k, H_CHAMADA, "NOTA 1")
        else:
            esq_ = [q for q in topo if q[0] < 0]
            for xc, zc_ in esq_:
                f.linha(221, (xc, zc_), (xc - 5.25 * k, yn))
            if esq_:
                f.linha(221, (xa, yn), (esq_[-1][0] - 5.25 * k, yn))
            f.texto(221, xa, Yt + 8.5 * k, H_CHAMADA, "NOTA 1")
        # o pente sozinho, abaixo do corte: altura e espaçamentos (notas 2 e 3)
        Yd = Yb - 10.5 * k - self.L
        xs2 = self._pinos(nome_pino, Yd)
        D = self.D
        x_esq, x_dir = min(xs2), max(xs2)
        for xo, sinal in ((x_esq - D / 2, -1), (x_dir + D / 2, 1)):
            f.cota((xo, Yd), (xo, Yd + self.L), (xo + sinal * 8.2 * k, Yd), modo="v")
        yc = Yd - 12 * k
        s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
        marcos = [0.0] + [s0 + i * sr for i in range(n)]
        npin = lambda face: max((pt["n_pinos"] or n for pt in self.pentes_corte if pt["face"] == face),  # noqa
                                default=0)
        m_esq, m_dir = npin("esquerda"), npin("direita")
        meios = []
        for i, (a_, b_) in enumerate(zip(marcos, marcos[1:])):
            if i < m_esq:
                f.cota((-a_, yc), (-b_, yc), (-a_, yc), modo="h")
                meios.append(-(a_ + b_) / 2)
            if i < m_dir:
                f.cota((bx + a_, yc), (bx + b_, yc), (bx + a_, yc), modo="h")
                meios.append(bx + (a_ + b_) / 2)
        yl = Yd - 26.5 * k
        for m in meios:
            f.linha(221, (m, yc), (m + 5.25 * k, yl))
        f.linha(221, (min(meios) + 5.25 * k, yl), (xb, yl))
        f.texto(221, xb - 6 * H_CHAMADA * E, Yd - 24.5 * k, H_CHAMADA, "NOTA 2")
        f.texto(221, xb - 6 * H_CHAMADA * E, Yd - 32.25 * k, H_CHAMADA, "NOTA 3")
        # eixos: faces do pilar até o pente e as linhas de pinos do corte ao pente
        for x in (0.0, bx):
            f.linha(204, (x, 0.0), (x, Yt + zp + 5 * k), s=3)
            f.linha(204, (x, Yd - 20 * k), (x, Yd - 2.5 * k), s=3)
        for x in xs:
            f.linha(205, (x, Yt + 13 * k), (x, Yd - 20 * k), s=4)
        self.y_min_corte = Yd - 36 * k                    # -225,5 no modelo (borda da folha)
        self.x_max_corte = max(xb + h / 2.8, x_topo + larg_topo)
        # região da vista (sem as linhas das faces que descem da planta): do título ao pente
        self.reg_corte = (min(xa - h / 2.8, x_tit), self.y_min_corte, self.x_max_corte, y_tit + H_VISTA * E)
        return Yd

    def montagem_identificacao(self, y):
        """Montagem opcional (Q7): linhas de identificação abaixo do pente, uma por posição."""
        f, E = self.f, self.E
        for fe in [x for x in self.r["ferros"] if x["tipo"] == "montagem"]:
            g = fe["subtipo"]
            y -= 1.6 * E
            f.ferro(dict(tipo="reto", mark=fe["pos"], quant=fe["quant"], bitola=fe["bitola"], comp=fe["comp"],
                         ins=[dict(x=-self.R - 40 * self.k, y=y, ang=0.0, nivel=244, ipatas=1)]))
            faces = "faces esquerda e direita" if g.startswith("by") else "faces de baixo e de cima"
            f.texto(0, -self.R - 40 * self.k, y - 0.7 * E, H_NOTA, f"(montagem dos pentes, {faces})")
            y -= 0.7 * E
        return y - (0.6 * E if self.c["montagem"] else 0.0)

    # ------------------------------------------------------------------ quadro, notas, título
    def quadro(self, x_dir, y_top):
        f, E = self.f, self.E
        linhas = self.c["quadro"]
        W = round(max(len(t) for t in linhas) * H_QUADRO * E + 16 * self.k)     # 155 no modelo
        x = x_dir - W
        y_bot = y_top - (39 + 8.16 * (len(linhas) - 4)) * self.k      # com pentes curtos (E9), mais linhas
        f.poli(240, [(x, y_bot), (x_dir, y_bot), (x_dir, y_top), (x, y_top)], fechar=True)
        f.linha(0, (x, y_top), (x, y_bot))
        f.linha(0, (x, y_top - 10 * self.k), (x_dir, y_top - 10 * self.k))
        f.linha(0, (x, y_bot), (x_dir, y_bot))
        f.texto(220, x + 4 * self.k, y_top - 7.4 * self.k, H_QUADRO, linhas[0])
        for i, t in enumerate(linhas[1:]):
            f.texto(242, x + 4 * self.k, y_top - (18.4 + 8.16 * i) * self.k, H_QUADRO, t)
        return x, y_bot

    def notas(self, x_dir, y_bot):
        """NOTAS IMPORTANTES no canto inferior direito, como no modelo (linhas no 0, separação das notas no 227)."""
        f, E, k = self.f, self.E, self.k
        dy = 0.5 * E
        linhas = _linhas_notas()
        W = 52 * H_NOTA * E + 1 * k                     # 196 no modelo
        X = x_dir - W
        Y = y_bot + 0.8 * E + len(linhas) * dy
        f.poli(240, [(X, Y), (x_dir, Y), (x_dir, Y - 0.8 * E), (X, Y - 0.8 * E)], fechar=True)
        f.linha(227, (X, y_bot), (X, Y))
        f.linha(227, (X, Y), (x_dir, Y))
        f.linha(227, (X, Y - 0.8 * E), (x_dir, Y - 0.8 * E))
        f.texto(220, X + 3 * k, Y - 8.8 * k, H_NOTAS_TIT, "NOTAS IMPORTANTES")
        y = Y - 0.8 * E
        for j, (i, txt) in enumerate(linhas):
            f.texto(227, X + 3 * k, y - dy + 1.71 * k, H_NOTA, txt)
            if i:
                f.texto(242, X + 3 * k, y - dy + 1.71 * k, H_NOTA, f"NOTA {i}:")
                if j:
                    f.linha(227, (X, y), (x_dir, y))      # separa as notas
            y -= dy
            if j < len(linhas) - 1:
                f.linha(0, (X, y), (x_dir, y))
        return X, Y

    def titulo(self):
        f, p, k = self.f, self.p, self.k
        x, y = self.x_esq, self.y_tit
        f.texto(222, x, y + 37 * k, H_TITULO, p["titulo"])
        f.texto(202, x, y + 26 * k, H_NX, f"{p['repeticoes']}X")
        f.texto(220, x, y + 14 * k, H_NX, f"({_fmt(p['bx'])}x{_fmt(p['by'])})")

    # ------------------------------------------------------------------ montagem da folha
    def montar(self):
        f, E, k = self.f, self.E, self.k
        i0 = len(f.prims)
        self.planta()
        self.colapso_identificacao()
        f.regiao("planta", i0)
        i0 = len(f.prims)
        self.colapso()
        f.regiao("colapso", i0)
        self.corte()
        f.regioes["corte"] = self.reg_corte
        y_min = self.montagem_identificacao(self.y_min_corte)
        self.titulo()
        # com pentes curtos (E9), o quadro tem mais linhas: a folha sobe o mesmo tanto, para ele não descer sobre o
        # título do colapso
        topo = self.y_tit + 52 * k + 8.16 * (len(self.c["quadro"]) - 4) * k
        esq = self.x_esq - 8 * k
        dir_ = self.x_marca_dir + 23 * k                  # 434 no modelo (marca A em 411)
        # notas no canto inferior direito: abaixo do colapso e à direita do corte (senão, a folha cresce)
        W_notas = 52 * H_NOTA * E + 1 * k
        dir_ = max(dir_, self.x_max_corte + 1.0 * E + W_notas)
        H_notas = 0.8 * E + len(_linhas_notas()) * 0.5 * E
        base = min(y_min, -self.ext - 1.0 * E - H_notas)
        self.notas(dir_, base)
        self.quadro(dir_, topo)
        f.retangulo(0, esq, base, dir_, topo)
        f.regiao("prancha", 0)
        return f


def montar(res):
    """Folha da prancha dos conectores a partir do resultado de nucleo.detalhe.detalhar."""
    return Prancha(res).montar()
