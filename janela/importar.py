# -*- coding: utf-8 -*-
"""
Diálogo "Importar do TQS": escolhe o edifício e a planta, lê a planta (em cópia, num processo à parte: uma falha da
DLL do TQS não derruba a janela) e mostra os pilares para o usuário escolher quais trazer.

- Marcados de saída: os internos retangulares sem abertura próxima nem capitel. Os de borda e de canto podem ser
  marcados, com confirmação (o app os detalharia como internos); os de seção não retangular, não.
- Os esforços de ELU da grelha (tf e tf·m, característicos) aparecem só para conferência: na tabela, a combinação de
  maior Fz; embaixo, todas as combinações do pilar selecionado.
"""
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from nucleo import importacao as imp

from .cad_dialogo import FONTE, Dialogo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCA = {True: "\u2611", False: "\u2610"}
SOLUCOES = ("a do pilar atual", "cobrinha", "conectores")


def _br(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def ler_tqs(acao, edificio, planta=None):
    """Roda o leitor (dwg_tqs/leitor_tqs.py) num processo à parte e devolve o JSON da leitura."""
    tmp = tempfile.mkdtemp(prefix="pun_imp_")
    saida = os.path.join(tmp, "leitura.json")
    cmd = [sys.executable, "-m", "dwg_tqs.leitor_tqs", acao, edificio] + ([planta] if planta else []) + \
          ["--saida", saida, "--tmp", os.path.join(tmp, "copia")]
    try:
        r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, timeout=600,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if os.path.isfile(saida):
            with open(saida, encoding="utf-8") as f:
                return json.load(f)
        erro = r.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return dict(erro=(erro[-1] if erro else f"o leitor terminou com o código {r.returncode}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class DlgImportar(Dialogo):
    """resultado = dict(pilares=[pilar do projeto], atualizar=bool, origem=dict(edificio, planta, data)) ou None."""

    def __init__(self, master, base, inicial=None, leitor=ler_tqs):
        super().__init__(master, "Importar pilares do TQS",
                         "Escolha a pasta do edifício e a planta. A leitura é feita numa cópia (o edifício não é "
                         "alterado). Marque os pilares a importar: dimensões, h da laje e cobrimentos. Os esforços "
                         "de ELU da grelha ficam só para conferência.")
        self.resizable(True, True)
        self.base, self.leitor = dict(base), leitor
        self.fila, self.ocupado = queue.Queue(), False
        self.dados, self.linhas, self.marcados, self.plantas = None, [], set(), []
        ini = inicial or {}
        self.v_edif = tk.StringVar(value=ini.get("edificio", ""))
        self.v_planta = tk.StringVar(value=ini.get("planta", ""))
        self.v_atualizar = tk.BooleanVar(value=True)
        self.v_solucao = tk.StringVar(value=SOLUCOES[0])
        self.v_ajustar = tk.BooleanVar(value=True)
        self._montar()
        self.ajuda.configure(wraplength=760)
        self._job = self.after(100, self._fila)
        if self.v_edif.get():
            self.after(150, self.listar_plantas)

    # ------------------------------------------------------------------ montagem
    def _montar(self):
        fr = self.moldura(self.corpo, "Edifício e planta")
        fr.pack(fill="x")
        ttk.Label(fr, text="Edifício", font=FONTE).grid(row=0, column=0, sticky="w")
        e = ttk.Entry(fr, textvariable=self.v_edif, width=70, font=FONTE)
        e.grid(row=0, column=1, sticky="we", padx=4)
        self.com_ajuda(e, "Pasta do edifício no TQS (a que tem o EDIFICIO.BDE), por exemplo C:\\TQS\\<edifício>.")
        ttk.Button(fr, text="...", width=3, command=self.escolher_edificio).grid(row=0, column=2)
        ttk.Label(fr, text="Planta", font=FONTE).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.cb_planta = ttk.Combobox(fr, textvariable=self.v_planta, width=30, state="readonly", font=FONTE)
        self.cb_planta.grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))
        self.com_ajuda(self.cb_planta, "Planta (pavimento) cuja laje tem os pilares a detalhar.")
        self.bt_ler = ttk.Button(fr, text="Ler a planta", command=self.ler_planta)
        self.bt_ler.grid(row=1, column=2, sticky="w", pady=(4, 0))
        fr.columnconfigure(1, weight=1)
        self.lb_estado = tk.Label(self.corpo, text="", font=FONTE, bg="#f0f0f0", fg="#505050", anchor="w",
                                  justify="left", wraplength=760)
        self.lb_estado.pack(fill="x", pady=(6, 2))

        fr = self.moldura(self.corpo, "Pilares da planta (clique para marcar)")
        fr.pack(fill="both", expand=True)
        cols = (("sel", "", 30), ("pilar", "Pilar", 60), ("secao", "Seção (cm)", 110), ("posicao", "Posição", 80),
                ("h", "h (cm)", 55), ("fz", "Fz máx (tf)", 80), ("comb", "Comb.", 50), ("mx", "Mx (tf·m)", 75),
                ("my", "My (tf·m)", 75), ("situacao", "Situação", 330))
        self.tv = ttk.Treeview(fr, columns=[c for c, _, _ in cols], show="headings", height=12, selectmode="browse")
        for c, t, w in cols:
            self.tv.heading(c, text=t)
            self.tv.column(c, width=w, anchor="center" if c in ("sel", "posicao", "comb") else
                           ("e" if c in ("h", "fz", "mx", "my") else "w"), stretch=c == "situacao")
        sb = ttk.Scrollbar(fr, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv.tag_configure("cinza", foreground="#8a8a8a")
        self.tv.tag_configure("aviso", foreground="#9a6400")
        self.tv.bind("<ButtonRelease-1>", self._clique)
        self.tv.bind("<space>", lambda e: self._alternar(self.tv.focus()))
        self.tv.bind("<<TreeviewSelect>>", lambda e: self._mostrar_esforcos())

        bt = tk.Frame(self.corpo, bg="#f0f0f0")
        bt.pack(fill="x", pady=4)
        ttk.Button(bt, text="Marcar os internos", command=self.marcar_internos).pack(side="left")
        ttk.Button(bt, text="Marcar todos", command=lambda: self._marcar_todos(True)).pack(side="left", padx=4)
        ttk.Button(bt, text="Desmarcar todos", command=lambda: self._marcar_todos(False)).pack(side="left")
        self.lb_contagem = tk.Label(bt, text="", font=FONTE, bg="#f0f0f0")
        self.lb_contagem.pack(side="right")

        fr = self.moldura(self.corpo, "Esforços de ELU do pilar selecionado (conferência; característicos, da grelha)")
        fr.pack(fill="x")
        self.te = ttk.Treeview(fr, columns=("n", "titulo", "fz", "mx", "my"), show="headings", height=4)
        for c, t, w in (("n", "Comb.", 50), ("titulo", "Combinação", 330), ("fz", "Fz (tf)", 80),
                        ("mx", "Mx (tf·m)", 80), ("my", "My (tf·m)", 80)):
            self.te.heading(c, text=t)
            self.te.column(c, width=w, anchor="w" if c == "titulo" else "e", stretch=c == "titulo")
        self.te.pack(fill="x")

        fr = self.moldura(self.corpo, "Opções")
        fr.pack(fill="x", pady=(6, 0))
        self.check(fr, 0, "Atualizar os pilares do projeto com o mesmo nome (dimensões, h, cobrimentos e repetições; "
                          "o detalhamento fica)", self.v_atualizar,
                   "Desmarcado, os pilares que já estão no projeto com o mesmo nome são pulados.")
        self.check(fr, 1, "Ajustar s0 e os espaçamentos aos limites da NBR 6118 (s0 <= 0,5d e sr <= 0,75d, em cm "
                          "inteiros)", self.v_ajustar,
                   "Com o d de cada pilar importado (h e cobrimentos da laje do TQS): s0 e os espaçamentos da "
                   "cobrinha e dos conectores que passam do limite descem até ele, arredondados para baixo ao cm. "
                   "O número de linhas não muda. Vale também para os pilares do projeto que forem atualizados.")
        self.combo(fr, 2, "Solução dos pilares novos", self.v_solucao, SOLUCOES, largura=18,
                   ajuda="Os demais parâmetros de detalhamento vêm do pilar atual da janela.")

    # ------------------------------------------------------------------ leitura (thread + processo à parte)
    def _rodar(self, texto, func, depois):
        if self.ocupado:
            return
        self.ocupado = True
        self.lb_estado.configure(text=texto, fg="#202020")
        self.configure(cursor="watch")
        self.bt_ler.state(["disabled"])

        def rodar():
            try:
                self.fila.put((depois, func()))
            except Exception as e:                       # noqa: BLE001
                self.fila.put((depois, dict(erro=f"{type(e).__name__}: {e}")))
        threading.Thread(target=rodar, daemon=True).start()

    def _fila(self):
        try:
            while True:
                depois, r = self.fila.get_nowait()
                self.ocupado = False
                self.configure(cursor="")
                self.bt_ler.state(["!disabled"])
                if r.get("erro"):
                    self.lb_estado.configure(text="Erro: " + r["erro"], fg="#b3261e")
                else:
                    depois(r)
        except queue.Empty:
            pass
        self._job = self.after(100, self._fila)

    def destroy(self):
        """Cancela a leitura da fila direto no Tcl (o after_cancel do Python falha em comandos já apagados)."""
        try:
            self.tk.call("after", "cancel", self._job)
        except tk.TclError:
            pass
        super().destroy()

    def escolher_edificio(self):
        ini = self.v_edif.get() or (r"C:\TQS" if os.path.isdir(r"C:\TQS") else "")
        d = filedialog.askdirectory(parent=self, title="Pasta do edifício no TQS", initialdir=ini)
        if d:
            self.v_edif.set(os.path.normpath(d))
            self.listar_plantas()

    def listar_plantas(self):
        edif = self.v_edif.get().strip()
        if not edif:
            return
        if not (os.path.isfile(os.path.join(edif, "EDIFICIO.BDE")) or os.path.isfile(os.path.join(edif, "EDIFICIO.DAT"))):
            self.lb_estado.configure(text="Essa pasta não é de um edifício do TQS (falta o EDIFICIO.BDE).", fg="#b3261e")
            return
        self._rodar("Lendo as plantas do edifício (cópia da raiz)...", lambda: self.leitor("plantas", edif),
                    self._plantas_lidas)

    def _plantas_lidas(self, r):
        self.plantas = [p for p in r.get("plantas", []) if p.get("existe", True)]
        nomes = [p["nome"] for p in self.plantas]
        self.cb_planta.configure(values=nomes)
        if self.v_planta.get() not in nomes:
            self.v_planta.set(nomes[-1] if nomes else "")
        self.lb_estado.configure(text=f"{len(nomes)} planta(s). Escolha a planta e clique em \"Ler a planta\".",
                                 fg="#202020")

    def ler_planta(self):
        edif, pl = self.v_edif.get().strip(), self.v_planta.get().strip()
        if not edif or not pl:
            self.lb_estado.configure(text="Escolha o edifício e a planta.", fg="#9a6400")
            return
        self._rodar(f"Lendo a planta {pl} (cópia) e os esforços da grelha...", lambda: self.leitor("planta", edif, pl),
                    self.carregar)

    # ------------------------------------------------------------------ tabela
    def carregar(self, dados):
        """Mostra a planta lida (também usada pelos testes, sem o TQS)."""
        self.dados = dados
        self.linhas = imp.analisar(dados, self.base)
        self.marcados = {j for j, ln in enumerate(self.linhas) if imp.selecao_padrao(ln)}
        self._preencher()
        g = dados.get("grelha") or {}
        n_int = sum(1 for ln in self.linhas if ln["suportado"] and ln["posicao"] == "interno")
        txt = (f"Planta {dados.get('planta')}: {len(self.linhas)} pilar(es), {n_int} interno(s) retangular(es); "
               f"laje(s): {', '.join(str(lj['titulo']) + ' h=' + format(lj['h'], 'g') for lj in dados.get('lajes', []))}.")
        if g.get("aviso"):
            txt += f"\nEsforços: {g['aviso']}."
        elif g.get("combinacoes"):
            txt += f"\nEsforços da grelha {g.get('nome')}: {len(g['combinacoes'])} combinação(ões) de ELU " + \
                   "(" + ", ".join(str(c["n"]) for c in g["combinacoes"]) + ")."
        self.lb_estado.configure(text=txt, fg="#202020")
        if self.linhas:
            self.tv.selection_set("0")
            self.tv.focus("0")

    def _preencher(self):
        self.tv.delete(*self.tv.get_children())
        for j, ln in enumerate(self.linhas):
            g = imp.governante(ln["esforcos"])
            h = ln["par"].get("h_laje") if ln["par"] else None
            if not ln["suportado"]:
                sit, tag = ln.get("motivo", ""), ("cinza",)
            elif ln["avisos"]:
                sit, tag = ln["avisos"][0], ("aviso",)
            else:
                sit, tag = "ok", ()
            self.tv.insert("", "end", str(j), tags=tag, values=(
                MARCA[j in self.marcados] if ln["suportado"] else "", ln["titulo"], f"{ln['secao']} {ln['dim']}",
                ln["posicao"] or "-", format(h, "g").replace(".", ",") if h else "",
                _br(g["fz"]) if g else "", g["n"] if g else "", _br(g["mx"]) if g else "", _br(g["my"]) if g else "",
                sit))
        self._contar()

    def _contar(self):
        n = len(self.marcados)
        self.lb_contagem.configure(text=f"{n} pilar(es) marcado(s)")

    def _clique(self, e):
        if self.tv.identify_region(e.x, e.y) == "cell":
            self._alternar(self.tv.identify_row(e.y))

    def _alternar(self, iid):
        if not iid:
            return
        j = int(iid)
        if not self.linhas[j]["suportado"]:
            self.lb_estado.configure(text=f"{self.linhas[j]['titulo']}: {self.linhas[j]['motivo']}.", fg="#9a6400")
            return
        self.marcados ^= {j}
        self.tv.set(iid, "sel", MARCA[j in self.marcados])
        self._contar()

    def _marcar_todos(self, marcar):
        self.marcados = {j for j, ln in enumerate(self.linhas) if ln["suportado"]} if marcar else set()
        self._preencher()

    def marcar_internos(self):
        self.marcados = {j for j, ln in enumerate(self.linhas) if imp.selecao_padrao(ln)}
        self._preencher()

    def _mostrar_esforcos(self):
        self.te.delete(*self.te.get_children())
        sel = self.tv.selection()
        if not sel:
            return
        ln = self.linhas[int(sel[0])]
        for e in ln["esforcos"]:
            self.te.insert("", "end", values=(e["n"], e["titulo"], _br(e["fz"]), _br(e["mx"]), _br(e["my"])))
        if not ln["suportado"]:
            txt = ln.get("motivo", "")
        elif ln["avisos"]:
            txt = "; ".join(ln["avisos"])
        else:
            d = f", d = {ln['d']:.1f} cm".replace(".", ",") if ln.get("d") else ""
            txt = f"pilar {ln['posicao']} {ln['dim']} cm{d}, sem avisos"
        self.ajuda.configure(text=f"{ln['titulo']}: {txt}.")

    # ------------------------------------------------------------------ OK
    def aplicar(self):
        if not self.dados:
            raise ValueError("leia uma planta antes")
        sel = [self.linhas[j] for j in sorted(self.marcados)]
        if not sel:
            raise ValueError("nenhum pilar marcado")
        fora = [ln["titulo"] for ln in sel if ln["posicao"] != "interno"]
        if fora and not messagebox.askyesno(
                self.title(), "Pilares de borda ou de canto marcados: " + ", ".join(fora) + ".\n\nO app só detalha "
                "pilares internos; eles seriam detalhados como internos. Importar assim mesmo?", parent=self):
            return None
        pilares = []
        sol = self.v_solucao.get()
        for ln in sel:
            par = dict(ln["par"])
            if sol in ("cobrinha", "conectores"):
                par["solucao"] = sol
            pilares.append(par)
        return dict(pilares=pilares, atualizar=self.v_atualizar.get(), ajustar=self.v_ajustar.get(),
                    origem=dict(edificio=self.dados.get("edificio"), planta=self.dados.get("planta"),
                                data=self.dados.get("data")),
                    avisos={ln["titulo"]: ln["avisos"] for ln in sel if ln["avisos"]})

    def _ok(self):
        try:
            r = self.aplicar()
        except ValueError as e:
            messagebox.showerror(self.title(), str(e).capitalize() + ".", parent=self)
            return
        if r is None:
            return
        self.resultado = r
        self.destroy()
