# -*- coding: utf-8 -*-
# Copiado de _apps\TelaSoldada\tela_vista.py (app de telas soldadas, 05/11/2026), para este repositório não depender
# de fora da própria pasta (CLAUDE.md, Independência). Mudança: as prioridades das chaves.
"""
Área de desenho tipo CAD (tk.Canvas, coordenadas de mundo em cm, y para cima).

- Roda do mouse: zoom em torno do cursor. Botão do meio ou direito arrastado: deslocar. Duplo clique no botão do
  meio: enquadrar (como no TQS e no AutoCAD).
- Os itens são desenhados uma vez; zoom e deslocamento usam scale/move do próprio canvas (rápido). Os textos têm a
  altura em cm do desenho e são refeitos depois do zoom; textos com menos de 4 px somem até aproximar.
- Cada item pode ter uma chave ("f:3" ferro, "c:12" cota, "b:7" bloco, "e:40" entidade). O mouse parado sobre um item chama
  ao_mover(x, y, chave) e o clique chama ao_clicar(chave); destacar(chaves) contorna os itens em laranja.
"""
import math
import tkinter as tk

FONTE_DESENHO = "Consolas"            # largura de caractere próxima da altura, como nas fontes do TQS
TRACOS = {1: (6, 4), 2: (2, 3), 3: (9, 3, 2, 3), 4: (9, 3, 2, 3, 2, 3)}
COR_DESTAQUE = "#ff9f1a"
PRIORIDADE = ("f", "c", "b", "e")                 # ferro, cota, bloco (pente), entidade


class Vista(tk.Canvas):

    def __init__(self, master, fundo="#000000", **kw):
        super().__init__(master, bg=fundo, highlightthickness=0, cursor="crosshair", **kw)
        self.k, self.x0, self.y0 = 1.0, 0.0, 0.0           # tela = ((x - x0) k, (y0 - y) k)
        self.textos = {}                                    # item -> altura em cm
        self.marcas = {}                                    # item -> (x, y, raio em px): tamanho fixo na tela
        self.chave_item, self.geo = {}, {}                  # item -> chave; chave -> [(tipo, pontos)]
        self.limites = None                                 # (xmin, ymin, xmax, ymax) da cena
        self.ao_mover = self.ao_clicar = self.ao_menu = None
        self._job_txt, self._arraste, self._sob = None, None, None
        self._ini_px, self._botao = None, None
        self.bind("<MouseWheel>", self._roda)
        for b in (2, 3):
            self.bind(f"<ButtonPress-{b}>", lambda e, b=b: self._ini_arraste(e, b))
            self.bind(f"<B{b}-Motion>", self._arrastar)
            self.bind(f"<ButtonRelease-{b}>", self._fim_arraste)
        self.bind("<Double-Button-2>", lambda e: self.enquadrar())
        self.bind("<Motion>", self._mover)
        self.bind("<Button-1>", self._clicar)
        self.bind("<Configure>", lambda e: self._ajustar_textos())

    # ------------------------------------------------------------------ transformações
    def T(self, x, y):
        return (x - self.x0) * self.k, (self.y0 - y) * self.k

    def M(self, sx, sy):
        return self.x0 + sx / self.k, self.y0 - sy / self.k

    def _flat(self, pts):
        out = []
        for x, y in pts:
            out.extend(self.T(x, y))
        return out

    def limpar(self):
        self.delete("all")
        self.textos.clear()
        self.marcas.clear()
        self.chave_item.clear()
        self.geo.clear()
        self.limites = None
        self._sob = None

    def _registrar(self, item, chave, tipo, pts):
        if chave:
            self.chave_item[item] = chave
            self.geo.setdefault(chave, []).append((tipo, pts))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if xs:
            b = (min(xs), min(ys), max(xs), max(ys))
            self.limites = b if self.limites is None else (min(self.limites[0], b[0]), min(self.limites[1], b[1]),
                                                           max(self.limites[2], b[2]), max(self.limites[3], b[3]))

    # ------------------------------------------------------------------ primitivas (coordenadas em cm)
    def linha(self, pts, cor="#ffffff", w=1, estilo=None, chave=None, tags=()):
        if len(pts) < 2:
            return None
        it = self.create_line(*self._flat(pts), fill=cor, width=w, dash=TRACOS.get(estilo, ""), tags=tags,
                              capstyle="butt")
        self._registrar(it, chave, "linha", pts)
        return it

    def poli(self, pts, contorno="#ffffff", fundo="", w=1, estilo=None, chave=None, tags=(), stipple=""):
        if len(pts) < 3:
            return None
        it = self.create_polygon(*self._flat(pts), outline=contorno, fill=fundo, width=w,
                                 dash=TRACOS.get(estilo, ""), tags=tags, stipple=stipple)
        self._registrar(it, chave, "poli", pts)
        return it

    def texto(self, x, y, s, h, ang=0.0, cor="#ffffff", ancora="sw", chave=None, tags=()):
        sx, sy = self.T(x, y)
        it = self.create_text(sx, sy, text=s, fill=cor, anchor=ancora, angle=ang, tags=tags,
                              font=(FONTE_DESENHO, -max(1, int(h * self.k / 0.72))))
        self.textos[it] = h
        w = len(s) * h
        a = math.radians(ang)
        self._registrar(it, chave, "texto", [(x, y), (x + w * math.cos(a), y + w * math.sin(a))])
        return it

    def marca(self, x, y, r_px=7, cor="#ff3b30", fundo="", rotulo=None, chave=None, tags=()):
        """Círculo de tamanho fixo na tela (marca de verificação), com rótulo opcional."""
        sx, sy = self.T(x, y)
        it = self.create_oval(sx - r_px, sy - r_px, sx + r_px, sy + r_px, outline=cor, fill=fundo, width=2, tags=tags)
        self.marcas[it] = (x, y, r_px)
        self._registrar(it, chave, "ponto", [(x, y)])
        if rotulo:
            t = self.create_text(sx + r_px + 3, sy - r_px, text=rotulo, fill=cor, anchor="sw",
                                 font=("Segoe UI", 8, "bold"), tags=tags)
            self.marcas[t] = (x, y, -r_px)
            if chave:
                self.chave_item[t] = chave
        return it

    # ------------------------------------------------------------------ zoom e deslocamento
    def _aplicar(self, k, x0, y0):
        """Leva os itens da transformação atual para (k, x0, y0) sem redesenhar."""
        f = k / self.k
        self.scale("all", 0, 0, f, f)
        self.move("all", (self.x0 - x0) * k, (y0 - self.y0) * k)
        self.k, self.x0, self.y0 = k, x0, y0
        self._fixar_marcas()
        self._agendar_textos()

    def enquadrar(self, lim=None, margem=0.06):
        lim = lim or self.limites
        if not lim:
            return
        W, H = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        dx, dy = max(lim[2] - lim[0], 1.0), max(lim[3] - lim[1], 1.0)
        k = min(W / dx, H / dy) * (1 - 2 * margem)
        cx, cy = (lim[0] + lim[2]) / 2, (lim[1] + lim[3]) / 2
        self._aplicar(k, cx - W / (2 * k), cy + H / (2 * k))

    def zoom(self, f, sx=None, sy=None):
        if sx is None:
            sx, sy = self.winfo_width() / 2, self.winfo_height() / 2
        k = min(max(self.k * f, 1e-4), 1e4)
        f = k / self.k
        self.scale("all", sx, sy, f, f)
        self.x0 += sx / self.k - sx / k
        self.y0 += -sy / self.k + sy / k
        self.k = k
        self._fixar_marcas()
        self._agendar_textos()

    def _roda(self, e):
        self.zoom(1.25 if e.delta > 0 else 0.8, e.x, e.y)

    def _ini_arraste(self, e, botao=2):
        self._arraste = (e.x, e.y)
        self._ini_px, self._botao = (e.x, e.y), botao

    def _arrastar(self, e):
        if self._arraste and self._ini_px and abs(e.x - self._ini_px[0]) + abs(e.y - self._ini_px[1]) > 3:
            self.configure(cursor="fleur")
        if self._arraste:
            dx, dy = e.x - self._arraste[0], e.y - self._arraste[1]
            self.move("all", dx, dy)
            self.x0 -= dx / self.k
            self.y0 += dy / self.k
            self._arraste = (e.x, e.y)

    def _fim_arraste(self, e):
        self._arraste = None
        self.configure(cursor="crosshair")
        # botão direito sem arrastar: menu de contexto (como no TQS), com o item sob o cursor
        if self._botao == 3 and self._ini_px and abs(e.x - self._ini_px[0]) + abs(e.y - self._ini_px[1]) <= 3                 and self.ao_menu:
            x, y = self.M(e.x, e.y)
            self.ao_menu(e.x_root, e.y_root, self.chave_em(e.x, e.y), x, y)
        self._ini_px = self._botao = None

    def _fixar_marcas(self):
        for it, (x, y, r) in self.marcas.items():
            sx, sy = self.T(x, y)
            if r > 0:
                self.coords(it, sx - r, sy - r, sx + r, sy + r)
            else:
                self.coords(it, sx - r + 3, sy + r)

    def _agendar_textos(self):
        if self._job_txt:
            self.after_cancel(self._job_txt)
        self._job_txt = self.after(90, self._ajustar_textos)

    def _ajustar_textos(self):
        self._job_txt = None
        for it, h in self.textos.items():
            px = h * self.k / 0.72
            if px < 4.0:
                self.itemconfigure(it, state="hidden")
            else:
                self.itemconfigure(it, state="normal", font=(FONTE_DESENHO, -int(px)))

    # ------------------------------------------------------------------ seleção
    def chave_em(self, sx, sy):
        its = self.find_overlapping(sx - 3, sy - 3, sx + 3, sy + 3)
        cands = [self.chave_item[i] for i in reversed(its) if i in self.chave_item]
        if not cands:
            return None
        return min(cands, key=lambda c: PRIORIDADE.index(c.split(":")[0]) if c.split(":")[0] in PRIORIDADE else 99)

    def _mover(self, e):
        x, y = self.M(e.x, e.y)
        ch = self.chave_em(e.x, e.y)
        if ch != self._sob:
            self._sob = ch
            self.apagar("sob")
            if ch:
                self._contornar(ch, "sob", "#ffd27f", 2)
        if self.ao_mover:
            self.ao_mover(x, y, ch)

    def _clicar(self, e):
        ch = self.chave_em(e.x, e.y)
        if self.ao_clicar:
            x, y = self.M(e.x, e.y)
            self.ao_clicar(ch, x, y)

    # ------------------------------------------------------------------ desenho temporário (comandos)
    def temp_limpar(self):
        self.apagar("temp")

    def temp_poli(self, pts, cor="#5ad1ff", w=2, estilo=1):
        if len(pts) >= 3:
            self.create_polygon(*self._flat(pts), outline=cor, fill="", width=w, dash=TRACOS.get(estilo, ""),
                                tags=("temp",))

    def temp_preencher(self, pts, cor="#5ad1ff"):
        """Polígono preenchido com trama (seleção de placas), no grupo temporário."""
        if len(pts) >= 3:
            self.create_polygon(*self._flat(pts), outline=cor, fill=cor, width=2, stipple="gray25", tags=("temp",))

    def temp_linha(self, pts, cor="#5ad1ff", w=2, estilo=None):
        if len(pts) >= 2:
            self.create_line(*self._flat(pts), fill=cor, width=w, dash=TRACOS.get(estilo, ""), tags=("temp",),
                             arrow="last")

    def _contornar(self, chave, tag, cor, w):
        for tipo, pts in self.geo.get(chave, []):
            if tipo == "poli":
                self.create_polygon(*self._flat(pts), outline=cor, fill="", width=w, tags=(tag,))
            elif tipo == "linha":                     # textos não: o contorno deles virava uma barra
                self.create_line(*self._flat(pts), fill=cor, width=w + 1, tags=(tag,))
            elif tipo == "ponto":
                sx, sy = self.T(*pts[0])
                it = self.create_oval(sx - 11, sy - 11, sx + 11, sy + 11, outline=cor, width=w, tags=(tag,))
                self.marcas[it] = (pts[0][0], pts[0][1], 11)

    def apagar(self, tag):
        for it in self.find_withtag(tag):
            self.marcas.pop(it, None)
        self.delete(tag)

    def destacar(self, chaves, aproximar=False):
        """Contorna as chaves em laranja. aproximar: enquadra o conjunto (um ponto ou um item pequeno, com pelo
        menos 3 m em volta). O contorno é desenhado depois do zoom (as marcas têm tamanho fixo na tela)."""
        self.apagar("destaque")
        lim = None
        for ch in chaves or []:
            for _, pts in self.geo.get(ch, []):
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                b = (min(xs), min(ys), max(xs), max(ys))
                lim = b if lim is None else (min(lim[0], b[0]), min(lim[1], b[1]), max(lim[2], b[2]), max(lim[3], b[3]))
        if aproximar and lim:
            w, h = lim[2] - lim[0], lim[3] - lim[1]
            d = max(150.0 - max(w, h) / 2, 0.15 * max(w, h))
            self.enquadrar((lim[0] - d, lim[1] - d, lim[2] + d, lim[3] + d), 0.0)
        for ch in chaves or []:
            self._contornar(ch, "destaque", COR_DESTAQUE, 3)
        return lim
