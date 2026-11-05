# -*- coding: utf-8 -*-
# Copiado de _apps\TelaSoldada\tela_ribbon.py (app de telas soldadas, 05/11/2026), para este repositório não depender
# de fora da própria pasta (CLAUDE.md, Independência). Mudanças: import dos ícones e rótulo do botão azul.
"""
Ribbon no visual dos editores do TQS (EAG): botão azul do menu do aplicativo, abas de texto, grupos com o
nome embaixo e separadores finos, botões grandes (ícone de 32 px e texto em até duas linhas) e pequenos (ícone de
16 px e texto), campos com rótulo (como o "Elemento atual" do TQS) e dicas ao parar o mouse sobre um comando.

Uso:
    rb = Ribbon(raiz, menu_app=menu)          # menu_app: tk.Menu aberto pelo botão azul
    aba = rb.aba("Inserção")
    g = aba.grupo("Distribuição")
    g.grande("distribuir", "Distribuir automaticamente telas", comando, dica="...")
    c = g.coluna(); c.pequeno("parametros", "Parâmetros de telas e distribuição...", comando)
"""
import tkinter as tk
from tkinter import ttk
from . import cad_icones as ic

FONTE = ("Segoe UI", 9)
FONTE_ABA = ("Segoe UI", 9)
COR_FUNDO = "#f3f3f3"          # faixa das abas e barra de acesso rápido
COR_CORPO = "#fdfdfd"          # corpo do ribbon
COR_BORDA = "#d5d5d5"
COR_SEP = "#e2e2e2"
COR_TITULO = "#707070"
COR_HOVER, COR_HOVER_B = "#e5f1fb", "#cce4f7"
COR_PRESS, COR_PRESS_B = "#cce4f7", "#99c9ef"
COR_APP = "#2b5797"


class Dica:
    """Dica (screen tip) com título em negrito e descrição, depois de 600 ms sobre o widget."""

    def __init__(self, w, titulo, texto):
        self.w, self.titulo, self.texto, self.job, self.win = w, titulo, texto, None, None
        for e, f in (("<Enter>", self._agendar), ("<Leave>", self._fechar), ("<ButtonPress>", self._fechar)):
            w.bind(e, f, add="+")

    def _agendar(self, _=None):
        self._fechar()
        self.job = self.w.after(600, self._abrir)

    def _abrir(self):
        if not self.w.winfo_exists():
            return
        x, y = self.w.winfo_rootx() + 4, self.w.winfo_rooty() + self.w.winfo_height() + 4
        self.win = tk.Toplevel(self.w)
        self.win.wm_overrideredirect(True)
        self.win.wm_geometry(f"+{x}+{y}")
        fr = tk.Frame(self.win, bg="#ffffff", highlightthickness=1, highlightbackground="#a0a0a0")
        fr.pack()
        tk.Label(fr, text=self.titulo, font=("Segoe UI", 9, "bold"), bg="#ffffff", anchor="w").pack(fill="x", padx=8,
                                                                                                    pady=(6, 0))
        if self.texto:
            tk.Label(fr, text=self.texto, font=FONTE, bg="#ffffff", fg="#404040", justify="left", wraplength=320,
                     anchor="w").pack(fill="x", padx=8, pady=(2, 7))

    def _fechar(self, _=None):
        if self.job:
            self.w.after_cancel(self.job)
            self.job = None
        if self.win:
            self.win.destroy()
            self.win = None


class Botao(tk.Frame):
    """Botão plano com destaque ao passar o mouse; grande (ícone em cima) ou pequeno (ícone à esquerda).
    alternar=True: fica marcado enquanto `marcado` for verdadeiro (ex.: face superior/inferior)."""

    def __init__(self, master, icone, texto, comando, grande=True, dica=None, bg=COR_CORPO, alternar=False):
        super().__init__(master, bg=bg, highlightthickness=1, highlightbackground=bg, bd=0)
        self.bg, self.comando, self.ativo, self.marcado, self.alternar = bg, comando, True, False, alternar
        self.img = ic.foto(icone, 32 if grande else 16) if icone else None
        if grande:
            self.l_img = tk.Label(self, image=self.img, bg=bg, bd=0)
            self.l_img.pack(side="top", padx=6, pady=(3, 0))
            self.l_txt = tk.Label(self, text=_duas_linhas(texto), font=FONTE, bg=bg, fg="#202020", justify="center")
            self.l_txt.pack(side="top", padx=3, pady=(1, 2))
        else:
            self.l_img = tk.Label(self, image=self.img, bg=bg, bd=0)
            self.l_img.pack(side="left", padx=(3, 2), pady=1)
            self.l_txt = tk.Label(self, text=texto, font=FONTE, bg=bg, fg="#202020", anchor="w")
            self.l_txt.pack(side="left", padx=(0, 4), pady=1)
        for w in (self, self.l_img, self.l_txt):
            w.bind("<Enter>", self._entrar)
            w.bind("<Leave>", self._sair)
            w.bind("<ButtonPress-1>", self._apertar)
            w.bind("<ButtonRelease-1>", self._soltar)
        if dica:
            Dica(self, texto.replace("\n", " "), dica)

    def _cor(self, fundo, borda):
        for w in (self, self.l_img, self.l_txt):
            w.configure(bg=fundo)
        self.configure(highlightbackground=borda)

    def _normal(self):
        if self.marcado:
            self._cor(COR_PRESS, COR_PRESS_B)
        else:
            self._cor(self.bg, self.bg)

    def _entrar(self, _):
        if self.ativo:
            self._cor(COR_PRESS if self.marcado else COR_HOVER, COR_PRESS_B if self.marcado else COR_HOVER_B)

    def _sair(self, _):
        self._normal()

    def _apertar(self, _):
        if self.ativo:
            self._cor(COR_PRESS, COR_PRESS_B)

    def _soltar(self, e):
        if not self.ativo:
            return
        dentro = 0 <= e.x_root - self.winfo_rootx() < self.winfo_width() and \
            0 <= e.y_root - self.winfo_rooty() < self.winfo_height()
        self._normal()
        if dentro and self.comando:
            self.comando()

    def marcar(self, v):
        self.marcado = bool(v)
        self._normal()

    def habilitar(self, v):
        self.ativo = bool(v)
        self.l_txt.configure(fg="#202020" if v else "#a0a0a0")
        self._normal()


def _duas_linhas(texto):
    """Texto do botão grande em até duas linhas, quebrado no espaço mais perto do meio (como no TQS:
    "Regerar / desenho/planta", "Distribuir / automaticamente telas")."""
    texto = texto.replace("/ ", "/")
    if len(texto) <= 10 or " " not in texto:
        return texto
    meio = len(texto) / 2
    i = min((k for k, c in enumerate(texto) if c == " "), key=lambda k: abs(k - meio))
    return texto[:i] + "\n" + texto[i + 1:]


class Coluna(tk.Frame):
    """Coluna de até três linhas de comandos pequenos ou campos, dentro de um grupo."""

    def __init__(self, master):
        super().__init__(master, bg=COR_CORPO)

    def pequeno(self, icone, texto, comando, dica=None, alternar=False):
        b = Botao(self, icone, texto, comando, grande=False, dica=dica, alternar=alternar)
        b.pack(side="top", anchor="w", pady=0)
        return b

    def _linha(self, rotulo, largura_rot):
        fr = tk.Frame(self, bg=COR_CORPO)
        fr.pack(side="top", anchor="w", pady=1)
        if rotulo:
            tk.Label(fr, text=rotulo, font=FONTE, bg=COR_CORPO, fg="#202020", width=largura_rot, anchor="w").pack(
                side="left", padx=(4, 2))
        return fr

    def combo(self, rotulo, var, valores, largura=12, ler=True, largura_rot=None, dica=None, ao_mudar=None):
        fr = self._linha(rotulo, largura_rot)
        cb = ttk.Combobox(fr, textvariable=var, values=valores, width=largura, font=FONTE,
                          state="readonly" if ler else "normal")
        cb.pack(side="left", padx=(0, 4))
        if ao_mudar:
            cb.bind("<<ComboboxSelected>>", lambda e: ao_mudar())
            if not ler:
                cb.bind("<Return>", lambda e: ao_mudar())
                cb.bind("<FocusOut>", lambda e: ao_mudar())
        if dica:
            Dica(cb, rotulo or "", dica)
        return cb

    def campo(self, rotulo, var, largura=7, unidade="", largura_rot=None, dica=None, ao_mudar=None):
        fr = self._linha(rotulo, largura_rot)
        en = ttk.Entry(fr, textvariable=var, width=largura, font=FONTE, justify="right")
        en.pack(side="left")
        if unidade:
            tk.Label(fr, text=unidade, font=FONTE, bg=COR_CORPO, fg="#505050").pack(side="left", padx=(2, 4))
        if ao_mudar:
            en.bind("<Return>", lambda e: ao_mudar())
            en.bind("<FocusOut>", lambda e: ao_mudar())
        if dica:
            Dica(en, rotulo or "", dica)
        return en

    def spin(self, rotulo, var, de, ate, passo=1, largura=5, largura_rot=None, dica=None, ao_mudar=None):
        fr = self._linha(rotulo, largura_rot)
        sp = ttk.Spinbox(fr, textvariable=var, from_=de, to=ate, increment=passo, width=largura, font=FONTE,
                         justify="right", command=ao_mudar)
        sp.pack(side="left", padx=(0, 4))
        if ao_mudar:
            sp.bind("<Return>", lambda e: ao_mudar())
            sp.bind("<FocusOut>", lambda e: ao_mudar())
        if dica:
            Dica(sp, rotulo or "", dica)
        return sp

    def check(self, texto, var, ao_mudar=None, dica=None):
        cb = tk.Checkbutton(self, text=texto, variable=var, font=FONTE, bg=COR_CORPO, activebackground=COR_CORPO,
                            anchor="w", command=ao_mudar, highlightthickness=0, bd=0)
        cb.pack(side="top", anchor="w", padx=2, pady=1)
        if dica:
            Dica(cb, texto, dica)
        return cb

    def radio(self, texto, var, valor, ao_mudar=None, dica=None):
        rb = tk.Radiobutton(self, text=texto, variable=var, value=valor, font=FONTE, bg=COR_CORPO,
                            activebackground=COR_CORPO, anchor="w", command=ao_mudar, highlightthickness=0, bd=0)
        rb.pack(side="top", anchor="w", padx=2, pady=1)
        if dica:
            Dica(rb, texto, dica)
        return rb


class Grupo(tk.Frame):
    def __init__(self, master, titulo):
        super().__init__(master, bg=COR_CORPO)
        self.corpo = tk.Frame(self, bg=COR_CORPO)
        self.corpo.pack(side="top", fill="both", expand=True, padx=3, pady=(2, 0))
        tk.Label(self, text=titulo, font=("Segoe UI", 8), fg=COR_TITULO, bg=COR_CORPO).pack(side="bottom", pady=(0, 1))

    def grande(self, icone, texto, comando, dica=None, alternar=False):
        b = Botao(self.corpo, icone, texto, comando, grande=True, dica=dica, alternar=alternar)
        b.pack(side="left", fill="y", padx=1, pady=1)
        return b

    def coluna(self):
        c = Coluna(self.corpo)
        c.pack(side="left", fill="y", padx=2, pady=1, anchor="n")
        return c


class Aba(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=COR_CORPO)

    def grupo(self, titulo):
        g = Grupo(self, titulo)
        g.pack(side="left", fill="y")
        tk.Frame(self, bg=COR_SEP, width=1).pack(side="left", fill="y", pady=6)
        return g


class Ribbon(tk.Frame):
    ALTURA = 98

    def __init__(self, master, menu_app=None, rotulo_app="Punção"):
        super().__init__(master, bg=COR_FUNDO)
        self.abas, self.rotulos, self.atual = {}, {}, None
        self.faixa = tk.Frame(self, bg=COR_FUNDO)
        self.faixa.pack(side="top", fill="x")
        self.corpo = tk.Frame(self, bg=COR_CORPO, height=self.ALTURA, highlightthickness=1,
                              highlightbackground=COR_BORDA)
        self.corpo.pack(side="top", fill="x")
        self.corpo.pack_propagate(False)
        self.menu_app = menu_app
        self.bt_app = tk.Label(self.faixa, text=f"  {rotulo_app}  ▾", font=("Segoe UI", 9, "bold"), bg=COR_APP,
                               fg="white", padx=6, pady=3, cursor="hand2")
        self.bt_app.pack(side="left", padx=(2, 6), pady=(2, 0))
        self.bt_app.bind("<Button-1>", self._abrir_menu)
        self.bt_app.bind("<Enter>", lambda e: self.bt_app.configure(bg="#3a6db5"))
        self.bt_app.bind("<Leave>", lambda e: self.bt_app.configure(bg=COR_APP))
        self.direita = tk.Frame(self.faixa, bg=COR_FUNDO)
        self.direita.pack(side="right", padx=4)

    def _abrir_menu(self, _=None):
        if self.menu_app:
            self.menu_app.tk_popup(self.bt_app.winfo_rootx(), self.bt_app.winfo_rooty() + self.bt_app.winfo_height())

    def aba(self, nome):
        a = Aba(self.corpo)
        lb = tk.Label(self.faixa, text=nome, font=FONTE_ABA, bg=COR_FUNDO, fg="#333333", padx=11, pady=4,
                      highlightthickness=1, highlightbackground=COR_FUNDO)
        lb.pack(side="left", pady=(2, 0))
        lb.bind("<Button-1>", lambda e, n=nome: self.selecionar(n))
        lb.bind("<Enter>", lambda e, n=nome: self.rotulos[n].configure(fg=COR_APP))
        lb.bind("<Leave>", lambda e, n=nome: self.rotulos[n].configure(fg=COR_APP if n == self.atual else "#333333"))
        self.abas[nome], self.rotulos[nome] = a, lb
        if self.atual is None:
            self.selecionar(nome)
        return a

    def selecionar(self, nome):
        if self.atual:
            self.abas[self.atual].pack_forget()
            self.rotulos[self.atual].configure(bg=COR_FUNDO, fg="#333333", highlightbackground=COR_FUNDO)
        self.atual = nome
        self.abas[nome].pack(side="left", fill="both", expand=True)
        self.rotulos[nome].configure(bg=COR_CORPO, fg=COR_APP, highlightbackground=COR_BORDA)


class BarraRapida(tk.Frame):
    """Barra de acesso rápido (ícones de 16 px), acima das abas, como a do TQS."""

    def __init__(self, master):
        super().__init__(master, bg=COR_FUNDO)

    def botao(self, icone, dica, comando):
        b = tk.Label(self, image=ic.foto(icone, 16), bg=COR_FUNDO, bd=0, padx=3, pady=2, highlightthickness=1,
                     highlightbackground=COR_FUNDO)
        b.pack(side="left", padx=1, pady=1)
        b.bind("<Enter>", lambda e: b.configure(bg=COR_HOVER, highlightbackground=COR_HOVER_B))
        b.bind("<Leave>", lambda e: b.configure(bg=COR_FUNDO, highlightbackground=COR_FUNDO))
        b.bind("<ButtonRelease-1>", lambda e: comando())
        Dica(b, dica, "")
        return b

    def separador(self):
        tk.Frame(self, bg=COR_BORDA, width=1, height=16).pack(side="left", padx=4, pady=3)
