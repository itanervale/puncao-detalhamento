# -*- coding: utf-8 -*-
# Copiado de _apps\TelaSoldada\tela_icones.py (app de telas soldadas, 05/11/2026), para este repositório não depender
# de fora da própria pasta (CLAUDE.md, Independência). Mantidos os ícones genéricos; os da punção estão no fim (seção própria).
"""
Ícones da janela (ribbon, barra de acesso rápido e árvore), desenhados com o Pillow no estilo dos ícones dos
editores do TQS: traço preto e poucas cores de destaque. Cada ícone é desenhado numa grade de 32 x 32 com
supersampling de 4x e reduzido para 32 ou 16 px. Sem o Pillow, foto() devolve um ícone vazio e a janela funciona
só com os textos.

Uso: foto("gerar", 32) -> PhotoImage (em cache).
     python -m janela.cad_icones  -> folha com todos os ícones em saidas/icones.png.
"""
import math
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:                                   # janela sem ícones
    Image = ImageDraw = ImageFont = None

SS = 4                                          # supersampling
PRETO, AZUL, AZUL_C, VERM, AMAR, VERDE = "#1b1b1b", "#1f5fbf", "#5b9bd5", "#d23b2f", "#f2c12e", "#2e9d48"
CINZA, CINZA_C, LARANJA, CIANO, LILAS = "#6e6e6e", "#bdbdbd", "#e8832a", "#1aa3b8", "#8e5cc4"
FUNDO_TELA = "#dfeef0"

_FONTES = {}

def _fonte(tam, negrito=True):
    k = (tam, negrito)
    if k not in _FONTES:
        nomes = ["segoeuib.ttf", "arialbd.ttf"] if negrito else ["segoeui.ttf", "arial.ttf"]
        for n in nomes:
            try:
                _FONTES[k] = ImageFont.truetype(os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", n), tam)
                break
            except OSError:
                continue
        else:
            _FONTES[k] = ImageFont.load_default()
    return _FONTES[k]

class D:
    """Desenho na grade 32 x 32 (y para baixo, como na tela)."""

    def __init__(self):
        self.im = Image.new("RGBA", (32 * SS, 32 * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def linha(self, pts, cor=PRETO, w=1.6):
        self.d.line(self._p(pts), fill=cor, width=max(1, round(w * SS)), joint="curve")

    def ret(self, x0, y0, x1, y1, cor=PRETO, fundo=None, w=1.6):
        self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], outline=cor, fill=fundo, width=max(1, round(w * SS)))

    def poli(self, pts, cor=PRETO, fundo=None, w=1.6):
        self.d.polygon(self._p(pts), outline=cor, fill=fundo, width=max(1, round(w * SS)))

    def elipse(self, x0, y0, x1, y1, cor=PRETO, fundo=None, w=1.6):
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], outline=cor, fill=fundo, width=max(1, round(w * SS)))

    def ponto(self, x, y, r=1.2, cor=PRETO):
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=cor)

    def seta(self, x0, y0, x1, y1, cor=PRETO, w=1.8, cab=3.6):
        self.linha([(x0, y0), (x1, y1)], cor, w)
        a = math.atan2(y1 - y0, x1 - x0)
        p1 = (x1 - cab * math.cos(a - 0.5), y1 - cab * math.sin(a - 0.5))
        p2 = (x1 - cab * math.cos(a + 0.5), y1 - cab * math.sin(a + 0.5))
        self.poli([(x1, y1), p1, p2], cor, cor, 0.5)

    def texto(self, x, y, s, cor=PRETO, tam=11, negrito=True, ancora="mm"):
        self.d.text((x * SS, y * SS), s, fill=cor, font=_fonte(round(tam * SS), negrito), anchor=ancora)

    def tracejado(self, x0, y0, x1, y1, cor=PRETO, w=1.6, traco=3.0, vao=2.0):
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        t = 0.0
        while t < L:
            t1 = min(t + traco, L)
            self.linha([(x0 + ux * t, y0 + uy * t), (x0 + ux * t1, y0 + uy * t1)], cor, w)
            t = t1 + vao


# ------------------------------------------------------------------------- desenhos genéricos (do app de telas)
def _tela(d, x0, y0, x1, y1, fundo=FUNDO_TELA, w=1.6):
    d.ret(x0, y0, x1, y1, PRETO, fundo, w)
    d.linha([(x0, y1), (x1, y0)], VERM, w * 0.9)


def _folha(d, x0=7, y0=3, x1=25, y1=29, dobra=6, fundo="white"):
    d.poli([(x0, y0), (x1 - dobra, y0), (x1, y0 + dobra), (x1, y1), (x0, y1)], PRETO, fundo, 1.4)
    d.linha([(x1 - dobra, y0), (x1 - dobra, y0 + dobra), (x1, y0 + dobra)], PRETO, 1.2)


def _pasta(d, aberta=False):
    d.poli([(3, 9), (12, 9), (14, 12), (28, 12), (28, 27), (3, 27)], "#b8860b", "#f6d365", 1.4)
    if aberta:
        d.poli([(3, 27), (8, 15), (31, 15), (27, 27)], "#b8860b", "#fbe39b", 1.4)


def _lupa(d):
    d.elipse(3, 3, 21, 21, PRETO, "#eef6ff", 2.2)
    d.linha([(18.5, 18.5), (28, 28)], PRETO, 4.0)


def i_novo(d):
    _folha(d)


def i_abrir(d):
    _pasta(d, True)


def i_salvar(d):
    d.poli([(4, 4), (24, 4), (28, 8), (28, 28), (4, 28)], "#173f7a", AZUL, 1.2)
    d.ret(9, 4, 22, 12, "#173f7a", "#e9eef5", 1.0)
    d.ret(18, 5.5, 20.5, 10.5, "#173f7a", "#173f7a", 0.6)
    d.ret(8, 17, 24, 28, "#173f7a", "white", 1.0)
    for y in (20.5, 23.5):
        d.linha([(11, y), (21, y)], CINZA_C, 1.0)


def i_salvar_como(d):
    i_salvar(d)
    d.linha([(17, 29), (29, 17)], AMAR, 3.4)
    d.linha([(17, 29), (29, 17)], "#7a5c00", 0.8)


def i_dxf(d):
    _folha(d, 5, 2, 23, 28)
    d.linha([(8, 12), (13, 8), (18, 12), (13, 16), (8, 12)], AZUL, 1.3)
    d.ret(10, 18, 31, 29, VERM, VERM, 0.8)
    d.texto(20.5, 23.6, "DXF", "white", 8.5)


def i_recarregar(d):
    for a0, a1, cor in ((200, 340, VERDE), (20, 160, VERDE)):
        d.d.arc([6 * SS, 6 * SS, 26 * SS, 26 * SS], a0, a1, fill=cor, width=round(2.4 * SS))
    d.poli([(25.5, 8.5), (28.5, 16.5), (20.5, 15.0)], VERDE, VERDE, 0.5)
    d.poli([(6.5, 23.5), (3.5, 15.5), (11.5, 17.0)], VERDE, VERDE, 0.5)


def i_verificar(d):
    d.elipse(3, 3, 19, 19, PRETO, "#eef6ff", 2.2)
    d.linha([(16.5, 16.5), (27, 27)], PRETO, 4.0)
    d.texto(11, 11.2, "!", VERM, 13)
    d.linha([(25, 5), (25, 14)], VERM, 2.6)
    d.ponto(25, 18, 1.5, VERM)


def i_regerar(d):
    cx, cy = 16, 16
    for k in range(12):
        a = k * math.pi / 6
        d.linha([(cx + 9 * math.cos(a), cy + 9 * math.sin(a)), (cx + 14.5 * math.cos(a), cy + 14.5 * math.sin(a))],
                "#e09b00", 2.2)
    d.elipse(7, 7, 25, 25, "#d08a00", AMAR, 1.4)
    d.texto(16, 16.6, "R", VERM, 13)


def i_parametros(d):
    _folha(d, 7, 3, 27, 29, 6, "#fffaf2")
    d.texto(16.5, 18, "Pa", VERM, 12.5)


def i_listar(d):
    d.ret(5, 3, 27, 29, PRETO, "white", 1.6)
    for y in (9, 14, 19, 24):
        d.ponto(9.5, y, 1.3)
        d.linha([(13, y), (23.5, y)], PRETO, 1.8)


def i_tabela(d):
    d.ret(4, 5, 28, 27, PRETO, "white", 1.4)
    d.ret(4, 5, 28, 10, PRETO, "#c6dbf6", 1.4)
    for y in (15, 21):
        d.linha([(4, y), (28, y)], CINZA, 1.0)
    for x in (12, 20):
        d.linha([(x, 5), (x, 27)], CINZA, 1.0)


def i_enquadrar(d):
    d.ret(8, 8, 24, 24, CINZA, None, 1.0)
    for (x, y, dx, dy) in ((3, 3, 1, 1), (29, 3, -1, 1), (3, 29, 1, -1), (29, 29, -1, -1)):
        d.linha([(x, y + 7 * dy), (x, y), (x + 7 * dx, y)], PRETO, 2.0)
    d.seta(13, 13, 8.5, 8.5, AZUL, 1.6, 3.0)
    d.seta(19, 19, 23.5, 23.5, AZUL, 1.6, 3.0)


def i_ampliar(d):
    _lupa(d)
    d.linha([(7.5, 12), (16.5, 12)], AZUL, 2.4)
    d.linha([(12, 7.5), (12, 16.5)], AZUL, 2.4)


def i_reduzir(d):
    _lupa(d)
    d.linha([(7.5, 12), (16.5, 12)], AZUL, 2.4)


def i_fundo(d):
    d.elipse(4, 4, 28, 28, PRETO, "white", 1.6)
    d.d.pieslice([4 * SS, 4 * SS, 28 * SS, 28 * SS], 90, 270, fill=PRETO)


def i_prancha(d):
    d.ret(2, 5, 30, 27, PRETO, "white", 1.4)
    d.ret(4, 7, 19, 25, CINZA_C, "#eef3f8", 0.8)
    _tela(d, 6, 9, 13, 15, w=1.0)
    _tela(d, 6, 16, 13, 22, w=1.0)
    for y in (9, 12, 15):
        d.linha([(21, y), (28, y)], CINZA, 1.0)
    d.ret(21, 20, 28, 25, PRETO, "#d9d9d9", 0.8)


def i_previa(d):
    i_prancha(d)
    d.elipse(14, 13, 26, 25, AZUL, "#ffffffcc", 2.0)
    d.linha([(24, 23), (30, 29)], AZUL, 3.0)


def i_gerar(d):
    d.poli([(4, 4), (24, 4), (28, 8), (28, 28), (4, 28)], "#8f1d14", VERM, 1.2)
    d.ret(9, 4, 22, 12, "#8f1d14", "#fbe9e7", 1.0)
    d.ret(8, 16, 24, 28, "#8f1d14", "white", 1.0)
    d.texto(16, 22.5, "DWG", VERM, 7)


def i_pdf(d):
    _folha(d, 5, 2, 23, 28)
    d.ret(9, 16, 31, 28, "#b3261e", "#b3261e", 0.8)
    d.texto(20, 22.4, "PDF", "white", 8.5)


def i_pasta(d):
    _pasta(d)


def i_notas(d):
    d.texto(16, 16.5, "T", AZUL, 24)


def i_copiar(d):
    d.ret(4, 3, 19, 21, PRETO, "white", 1.4)
    d.ret(12, 10, 27, 28, PRETO, "white", 1.4)
    for y in (15, 19, 23):
        d.linha([(15, y), (24, y)], CINZA, 1.2)


def i_ajuda(d):
    d.elipse(3, 3, 29, 29, AZUL, AZUL, 1.0)
    d.texto(16, 16.8, "?", "white", 17)


def i_sair(d):
    d.ret(6, 3, 21, 29, PRETO, "#e9e9e9", 1.4)
    d.seta(14, 16, 29, 16, VERM, 2.4, 5)


def i_pilar(d):
    d.ret(9, 9, 23, 23, PRETO, "#9e9e9e", 1.6)
    d.linha([(9, 9), (23, 23)], PRETO, 1.0)
    d.linha([(9, 23), (23, 9)], PRETO, 1.0)


def i_aviso(d):
    d.poli([(16, 3), (30, 28), (2, 28)], "#a35a00", "#ffd24d", 1.6)
    d.texto(16, 19, "!", PRETO, 13)


def i_ok(d):
    d.linha([(5, 17), (13, 25), (28, 7)], VERDE, 4.0)


def i_guia(d):
    d.poli([(4, 5), (15, 7), (15, 29), (4, 27)], "#173f7a", "#e9eef5", 1.2)
    d.poli([(28, 5), (17, 7), (17, 29), (28, 27)], "#173f7a", "#e9eef5", 1.2)
    for y in (12, 16, 20):
        d.linha([(6.5, y), (13, y + 0.6)], CINZA, 1.0)
        d.linha([(25.5, y), (19, y + 0.6)], CINZA, 1.0)


# ------------------------------------------------------------------------- PUNÇÃO
def _pilar(d, x0, y0, x1, y1, w=1.4):
    d.ret(x0, y0, x1, y1, PRETO, "#a8a8a8", w)


def _pino(d, x, y0, y1, cor=AZUL):
    """Pino de cabeça dupla visto de lado (o pente em corte)."""
    d.linha([(x, y0), (x, y1)], cor, 1.6)
    d.linha([(x - 2.6, y0), (x + 2.6, y0)], cor, 2.2)
    d.linha([(x - 2.6, y1), (x + 2.6, y1)], cor, 2.2)


def i_pente(d):
    for x in (7, 16, 25):
        _pino(d, x, 6, 25)
    d.linha([(4.5, 23.6), (27.5, 23.6)], LARANJA, 1.8)


def i_cobrinha(d):
    d.linha([(3, 24), (8, 24), (8, 8), (14, 8), (14, 24), (20, 24), (20, 8), (26, 8), (26, 24), (30, 24)], AZUL, 2.0)
    d.ponto(8, 24, 1.6, LARANJA)
    d.ponto(20, 24, 1.6, LARANJA)


def i_conectores(d):
    _pilar(d, 12, 12, 20, 20)
    for (x0, y0, x1, y1) in ((16, 9, 16, 2), (16, 23, 16, 30), (9, 16, 2, 16), (23, 16, 30, 16),
                             (10, 10, 4, 4), (22, 22, 28, 28), (10, 22, 4, 28), (22, 10, 28, 4)):
        d.linha([(x0, y0), (x1, y1)], CINZA, 1.0)
        for t in (0.15, 0.6, 1.0):
            d.ponto(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.4, AZUL)


def i_colapso(d):
    _pilar(d, 11, 11, 21, 21)
    for v in (13.5, 18.5):
        d.linha([(2, v), (30, v)], PRETO, 1.8)
        d.linha([(v, 2), (v, 30)], PRETO, 1.8)


def i_planta(d):
    _pilar(d, 12, 9, 20, 23)
    d.ret(6, 3, 26, 29, CINZA, None, 1.0)
    d.ret(2, 1, 30, 31, CINZA_C, None, 0.8)


def i_corte(d):
    d.poli([(2, 13), (30, 13), (30, 21), (2, 21)], PRETO, "#c8c8c8", 1.2)
    d.ret(12, 4, 20, 13, PRETO, "#a8a8a8", 1.2)
    d.ret(12, 21, 20, 30, PRETO, "#a8a8a8", 1.2)
    for x in (5, 8, 24, 27):
        d.linha([(x, 14.5), (x, 19.5)], AZUL, 1.4)


def i_mais_pilar(d):
    _pilar(d, 3, 11, 19, 27)
    d.linha([(25, 3), (25, 15)], VERDE, 3.0)
    d.linha([(19, 9), (31, 9)], VERDE, 3.0)


def i_duplicar(d):
    _pilar(d, 3, 3, 19, 19)
    d.ret(12, 12, 28, 28, PRETO, "#d0d0d0", 1.4)
    d.linha([(16, 20), (24, 20)], VERDE, 2.0)
    d.linha([(20, 16), (20, 24)], VERDE, 2.0)


def i_apagar(d):
    _pilar(d, 3, 9, 21, 27)
    d.linha([(17, 2), (30, 15)], VERM, 3.2)
    d.linha([(30, 2), (17, 15)], VERM, 3.2)


def i_colar(d):
    d.ret(6, 5, 26, 30, "#8a5a2b", "#d9b38c", 1.4)
    d.ret(11, 2, 21, 7, PRETO, "#eeeeee", 1.2)
    d.ret(9, 10, 23, 26, PRETO, "white", 1.0)
    for y in (14, 18, 22):
        d.linha([(9, y), (23, y)], VERDE, 0.9)
    d.linha([(15, 10), (15, 26)], VERDE, 0.9)


def i_lote(d):
    for k, cor in ((0, "#e8e8e8"), (3, "#f3f3f3"), (6, "white")):
        d.ret(4 + k, 2 + k, 22 + k, 24 + k, PRETO, cor, 1.2)
    d.texto(19, 19.5, "Nx", AZUL, 8)


def i_gerar_lote(d):
    for k, cor in ((0, "#e8e8e8"), (4, "white")):
        d.ret(3 + k, 3 + k, 19 + k, 23 + k, PRETO, cor, 1.2)
    d.seta(14, 27, 29, 27, VERDE, 2.2, 4.4)
    d.texto(15, 15, "DWG", AZUL, 6)


def i_cores(d):
    d.ret(3, 3, 29, 29, PRETO, "black", 1.2)
    d.poli([(29, 3), (29, 29), (3, 29)], PRETO, "white", 0.8)
    d.linha([(7, 12), (16, 12)], "#00ffff", 1.8)
    d.linha([(16, 24), (25, 24)], VERM, 1.8)


def i_verificacoes(d):
    d.ret(4, 4, 28, 28, PRETO, "white", 1.2)
    for y, cor in ((10, VERDE), (16, VERDE), (22, LARANJA)):
        d.ponto(9, y, 1.8, cor)
        d.linha([(13, y), (25, y)], CINZA, 1.2)



ICONES = {k[2:]: v for k, v in globals().items() if k.startswith("i_") and callable(v)}
_CACHE = {}


def imagem(nome, tam=32):
    if Image is None:
        return None
    d = D()
    ICONES[nome](d)
    return d.im.resize((tam, tam), Image.LANCZOS)


_RAIZ = [None]


def foto(nome, tam=32):
    """PhotoImage do ícone (em cache, para o Tk não o perder); sem o Pillow, uma imagem vazia do mesmo tamanho.
    As imagens pertencem ao interpretador Tk em que foram criadas: com uma janela nova (outra raiz no mesmo
    processo, como nos testes), o cache é refeito."""
    import tkinter as tk
    if tk._default_root is not _RAIZ[0]:
        _CACHE.clear()
        _RAIZ[0] = tk._default_root
    k = (nome, tam)
    if k not in _CACHE:
        if Image is None:
            _CACHE[k] = tk.PhotoImage(width=tam, height=tam)
        else:
            from PIL import ImageTk
            _CACHE[k] = ImageTk.PhotoImage(imagem(nome, tam))
    return _CACHE[k]


def folha(arq):
    """Todos os ícones em 32 e 16 px, com o nome (conferência visual)."""
    nomes = sorted(ICONES)
    col = 8
    lin = math.ceil(len(nomes) / col)
    W, H = 120, 70
    im = Image.new("RGB", (col * W, lin * H), "white")
    dr = ImageDraw.Draw(im)
    for i, n in enumerate(nomes):
        x, y = (i % col) * W, (i // col) * H
        im.paste(imagem(n, 32), (x + 10, y + 8), imagem(n, 32))
        im.paste(imagem(n, 16), (x + 52, y + 16), imagem(n, 16))
        dr.text((x + 10, y + 48), n, fill="black", font=_fonte(11, False))
    im.save(arq)
    return arq


if __name__ == "__main__":
    pasta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saidas")
    os.makedirs(pasta, exist_ok=True)
    print(folha(os.path.join(pasta, "icones.png")))
