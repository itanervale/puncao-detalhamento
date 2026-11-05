# -*- coding: utf-8 -*-
# Copiado de _apps\TelaSoldada\tela_dialogos.py (app de telas soldadas, 05/11/2026), para este repositório não depender
# de fora da própria pasta (CLAUDE.md, Independência). Só a base Dialogo e os conversores num e fmt.
"""
Base dos diálogos, no formato dos diálogos do TQS: rótulos à esquerda, campos alinhados, grupos em moldura e,
embaixo, a caixa de descrição do campo em foco, com OK e Cancelar. O resultado fica em self.resultado
(None = cancelado).
"""
import tkinter as tk
from tkinter import ttk, messagebox

FONTE = ("Segoe UI", 9)
BITOLAS = ["5", "6,3", "8", "10", "12,5", "16", "20", "25", "32"]


def num(s, padrao=None):
    s = str(s).strip().replace(",", ".")
    if s == "":
        return padrao
    return float(s)


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)


class Dialogo(tk.Toplevel):
    """Base: corpo, caixa de descrição embaixo e OK/Cancelar."""

    def __init__(self, master, titulo, ajuda_inicial=""):
        super().__init__(master)
        self.title(titulo)
        self.transient(master)
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.resultado = None
        self.corpo = tk.Frame(self, bg="#f0f0f0")
        self.corpo.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 4))
        base = tk.Frame(self, bg="#f0f0f0")
        base.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.ajuda = tk.Label(base, text=ajuda_inicial, font=FONTE, bg="#f7f7f7", fg="#303030", anchor="nw",
                              justify="left", wraplength=430, relief="sunken", bd=1, padx=6, pady=4, height=3)
        self.ajuda.pack(side="left", fill="both", expand=True, padx=(0, 10))
        bt = tk.Frame(base, bg="#f0f0f0")
        bt.pack(side="right", anchor="s")
        ttk.Button(bt, text="OK", width=12, command=self._ok).pack(side="left", padx=3)
        ttk.Button(bt, text="Cancelar", width=12, command=self.destroy).pack(side="left", padx=3)
        self.bind("<Escape>", lambda e: self.destroy())
        self._ajuda0 = ajuda_inicial

    def mostrar(self):
        self.update_idletasks()
        m = self.master
        x = m.winfo_rootx() + (m.winfo_width() - self.winfo_reqwidth()) // 2
        y = m.winfo_rooty() + (m.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.grab_set()
        self.focus_set()
        self.wait_window(self)
        return self.resultado

    def com_ajuda(self, w, texto):
        w.bind("<FocusIn>", lambda e: self.ajuda.configure(text=texto), add="+")
        w.bind("<Enter>", lambda e: self.ajuda.configure(text=texto), add="+")
        return w

    def moldura(self, pai, titulo):
        return ttk.LabelFrame(pai, text=titulo, padding=(8, 4))

    def linha(self, pai, r, rotulo, var, largura=8, unidade="", ajuda=""):
        ttk.Label(pai, text=rotulo, font=FONTE).grid(row=r, column=0, sticky="w", pady=2)
        e = ttk.Entry(pai, textvariable=var, width=largura, justify="right", font=FONTE)
        e.grid(row=r, column=1, sticky="e", padx=4, pady=2)
        if unidade:
            ttk.Label(pai, text=unidade, font=FONTE).grid(row=r, column=2, sticky="w")
        return self.com_ajuda(e, ajuda)

    def combo(self, pai, r, rotulo, var, valores, largura=10, ajuda="", ler=True):
        ttk.Label(pai, text=rotulo, font=FONTE).grid(row=r, column=0, sticky="w", pady=2)
        c = ttk.Combobox(pai, textvariable=var, values=valores, width=largura, font=FONTE,
                         state="readonly" if ler else "normal")
        c.grid(row=r, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        return self.com_ajuda(c, ajuda)

    def check(self, pai, r, texto, var, ajuda=""):
        c = ttk.Checkbutton(pai, text=texto, variable=var)
        c.grid(row=r, column=0, columnspan=3, sticky="w", pady=2)
        return self.com_ajuda(c, ajuda)

    def _ok(self):
        try:
            self.resultado = self.aplicar()
        except ValueError as e:
            messagebox.showerror(self.title(), f"Valor inválido: {e}", parent=self)
            return
        self.destroy()

    def aplicar(self):
        return None
