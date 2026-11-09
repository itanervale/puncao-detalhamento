# -*- coding: utf-8 -*-
"""
Detalhamento de armadura de punção: janela no estilo dos editores do TQS (EAG), como a do app de telas soldadas.

Abra pelo "Detalhar Punção.bat" (ou: pythonw janela_puncao.pyw [projeto.json]).

- Menus, barra de acesso rápido e ribbon com as abas Pilar, Cobrinha, Conectores, Colapso, Lote, Exibir e Saídas.
- À esquerda, a árvore do projeto (pilares; no pilar atual, ferros, pentes ou cobrinhas, verificações e vistas) e
  as propriedades do item selecionado.
- No centro, a área CAD (fundo preto com as cores de tela do TQS, ou as cores da plotagem), com as abas Planta,
  Corte, Colapso, Prancha e Tabela: roda = zoom, botão do meio ou direito = deslocar, duplo clique no meio =
  enquadrar; a dica sob o mouse mostra o nível e a medida. Embaixo, as mensagens (verificações) e a barra de status.
- Lote: o projeto tem vários pilares (Lote > Pilar atual, + Pilar, Duplicar, Apagar, Colar do Excel, Importar do
  TQS: dimensões dos pilares, h e cobrimentos da laje; os esforços de ELU da grelha ficam para conferência).
- A prévia é refeita a cada mudança ("Atualizar automaticamente"); a gravação pelo TQS (DWG, PDF e DXF) roda numa
  thread, com o resultado devolvido por uma fila (after() chamado de outra thread quebra o Tk).
"""
import copy
import json
import os
import pathlib
import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nucleo import colapso as ncol                                       # noqa: E402
from nucleo import conectores as nc                                      # noqa: E402
from nucleo import importacao as imp                                     # noqa: E402
from nucleo import prancha_cobrinha, prancha_conectores                  # noqa: E402
from nucleo import relatorio as rel_lote                                 # noqa: E402
from nucleo.detalhe import detalhar                                      # noqa: E402
from nucleo.parametros import (FORMATO, PADROES, VERSAO, altura_util, ler_projeto, novo_projeto,  # noqa: E402
                               posicao)

from . import cad_icones as ic                                           # noqa: E402
from . import cena                                                       # noqa: E402
from .cad_dialogo import Dialogo, fmt, num                               # noqa: E402
from .cad_ribbon import COR_CORPO, BarraRapida, Ribbon                   # noqa: E402
from .cad_vista import Vista                                             # noqa: E402
from .importar import DlgImportar                                        # noqa: E402

APP = "Armaduras de Punção"
NIVEL_COR = {"erro": "#b3261e", "aviso": "#9a6400", "ok": "#2e7d32", "info": "#202020", "cinza": "#707070"}
BITOLAS = ["5", "6,3", "8", "10", "12,5", "16", "20", "25", "32"]
PINOS = [fmt(float(p["bitola_mm"])) for p in nc.catalogo()["pinos"]]
VISTAS = (("planta", "Planta"), ("corte", "Corte"), ("colapso", "Colapso"), ("prancha", "Prancha"),
          ("tabela", "Tabela"))
OPCIONAIS = ("d", "cob_s_x", "cob_s_y", "cob_linhas_x", "cob_linhas_y")    # vazio = automático
TEXTOS = ("titulo", "solucao", "cob_direcao", "con_inclinados", "borda_x", "borda_y")
BORDAS = ("borda_x", "borda_y")
NENHUMA = "nenhuma"                        # o lado sem borda livre, como a janela o mostra
INTEIROS = ("repeticoes", "col_n_face_bx", "col_n_face_by", "cob_linhas", "cob_linhas_x", "cob_linhas_y",
            "con_pinos", "con_n_face_bx", "con_n_face_by", "con_trilhos")
COLUNAS_EXCEL = ("titulo", "bx", "by", "h_laje", "repeticoes", "solucao")
AVISO_IMPORTACAO = ("Programa em fase de testes, recomenda-se a duplicação do edifício.\n\n"
                    "A leitura é feita numa cópia temporária, mas trabalhe de preferência numa duplicata do edifício "
                    "no TQS. Para importar os esforços, a grelha da planta precisa estar processada.")
# Pilar de um projeto novo: os padrões do núcleo (50 x 150, cobrinha; as cobrinhas, paralelas ao lado menor,
# correm em x).
NOVO_PILAR = dict(titulo="P1")


def _kg(bitola, comp_cm, quant):
    return quant * comp_cm / 100.0 * bitola ** 2 * 0.00617


def _posicao_txt(p):
    """Interno, ou a borda livre de cada eixo com a distância da face (E9)."""
    lados = [f"{p[f'borda_{e}']} a {fmt(float(p[f'dist_borda_{e}']))} cm" if p[f"dist_borda_{e}"] else
             f"{p[f'borda_{e}']} (faceando)" for e in ("x", "y") if p[f"borda_{e}"]]
    return posicao(p) + (f": borda {' e '.join(lados)}" if lados else "")


def _br(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def _fz_tqs(par):
    g = imp.governante((par.get("tqs") or {}).get("esforcos"))
    return f"{_br(g['fz'], 2)} (comb. {g['n']})" if g else ""


class DlgColar(Dialogo):
    """Colar do Excel: uma linha por pilar, colunas Título, bx, by, h, repetições e solução (as duas últimas
    opcionais), separadas por tabulação ou ponto e vírgula. O cabeçalho é ignorado. Os demais parâmetros vêm do
    pilar atual."""

    def __init__(self, master, texto):
        super().__init__(master, "Colar pilares do Excel",
                         "Uma linha por pilar: Título; bx; by; h da laje; repetições; solução (cobrinha ou "
                         "conectores). As duas últimas colunas são opcionais. Os demais parâmetros são copiados do "
                         "pilar atual. Uma 1ª linha de cabeçalho é ignorada.")
        fr = self.moldura(self.corpo, "Linhas (Excel: tabulação; ou ponto e vírgula)")
        fr.pack(fill="both", expand=True)
        self.tx = tk.Text(fr, width=70, height=12, font=("Consolas", 9))
        self.tx.pack(fill="both", expand=True)
        self.tx.insert("1.0", texto)
        self.com_ajuda(self.tx, self._ajuda0)

    def aplicar(self):
        return interpretar_colagem(self.tx.get("1.0", "end"))


def mesclar_colagem(base, novos):
    """Pilares colados: os parâmetros do pilar `base` (o atual), menos título, dimensões, h e repetições, com as
    colunas coladas por cima. A solução só muda se a coluna veio preenchida."""
    fora = ("titulo", "bx", "by", "h_laje", "repeticoes", "tqs")         # tqs: origem do pilar atual
    out = []
    for p in novos:
        q = {k: copy.deepcopy(v) for k, v in base.items() if k not in fora}
        q.update(p)
        out.append(q)
    return out


def interpretar_colagem(texto):
    """Linhas coladas -> [dict(titulo, bx, by, h_laje[, repeticoes][, solucao])]. ValueError com a linha ruim."""
    out = []
    for k, lin in enumerate(texto.splitlines(), 1):
        if not lin.strip():
            continue
        cel = [c.strip() for c in (lin.split("\t") if "\t" in lin else lin.split(";"))]
        if len(cel) < 4:
            raise ValueError(f"linha {k}: são precisas pelo menos 4 colunas (título, bx, by, h)")
        try:
            bx, by, h = (float(c.replace(",", ".")) for c in cel[1:4])
        except ValueError:
            if not out:
                continue                                  # cabeçalho
            raise ValueError(f"linha {k}: bx, by e h devem ser números ({lin!r})")
        p = dict(titulo=cel[0] or f"P{k}", bx=bx, by=by, h_laje=h)
        if len(cel) > 4 and cel[4]:
            p["repeticoes"] = int(float(cel[4].replace(",", ".").rstrip("xX")))
        if len(cel) > 5 and cel[5]:
            sol = cel[5].lower()
            if sol.startswith("cob"):
                p["solucao"] = "cobrinha"
            elif sol.startswith("con") or sol.startswith("stud") or sol.startswith("pin"):
                p["solucao"] = "conectores"
            else:
                raise ValueError(f"linha {k}: solução {cel[5]!r} (use cobrinha ou conectores)")
        out.append(p)
    return out


class App(tk.Tk):

    def __init__(self, arquivo=None):
        super().__init__()
        self.withdraw()
        self.title(APP)
        self.geometry("1500x920+30+20")
        self.minsize(1100, 680)
        try:
            ttk.Style(self).theme_use("vista")
        except tk.TclError:
            pass
        st = ttk.Style(self)
        st.configure("Treeview", font=("Segoe UI", 9), rowheight=20)
        st.configure("Arvore.Treeview", font=("Segoe UI", 9), rowheight=21)
        self.iconphoto(True, ic.foto("pente", 32), ic.foto("pente", 16))
        self.projeto = novo_projeto([dict(NOVO_PILAR)])
        self.arq = None
        self.i = 0                                  # pilar atual
        self.res = self.folha = None
        self.info = {}
        self.arquivos = {}                          # por pilar: arquivos gravados pelo TQS
        self.gerados = {}                           # por pilar: o retorno da gravação (comprimentos do TQS)
        self.arq_relatorio = None                   # relatório do lote gravado (TXT e CSV)
        self.modificado = False
        self.ocupado = False
        self.fila = queue.Queue()
        self._sync = False
        self._job = None
        self._enquadrar = True
        self.vista_atual = "prancha"
        self.v = {}
        self.plot = tk.BooleanVar(value=False)
        self.auto = tk.BooleanVar(value=True)
        self.pdf = tk.BooleanVar(value=True)
        self.dxf = tk.BooleanVar(value=True)
        self.pasta = tk.StringVar(value="")
        self.pilar_atual = tk.StringVar(value="")
        self.d_calc = tk.StringVar(value="")
        self._montar()
        self.after(80, self._processar_fila)
        self.protocol("WM_DELETE_WINDOW", self.sair)
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        self.deiconify()
        self.after(200, (lambda: self.abrir(arquivo)) if arquivo else self._inicio)

    # ================================================================== montagem da janela
    def _montar(self):
        self._menus()
        self.barra = BarraRapida(self)
        self.barra.pack(side="top", fill="x")
        for ico, dica, cmd in (("novo", "Novo projeto (Ctrl+N)", self.novo), ("abrir", "Abrir projeto (Ctrl+O)", self.abrir),
                               ("salvar", "Salvar (Ctrl+S)", self.salvar), (None, None, None),
                               ("mais_pilar", "+ Pilar", self.mais_pilar), ("duplicar", "Duplicar pilar", self.duplicar),
                               (None, None, None), ("enquadrar", "Enquadrar (Home)", self.enquadrar),
                               ("cores", "Cores de plotagem / de tela", self._alternar_cores), (None, None, None),
                               ("gerar", "Gerar DWG / PDF / DXF do pilar (Ctrl+G)", self.gerar),
                               ("gerar_lote", "Gerar o lote (Ctrl+Shift+G)", self.gerar_lote)):
            if ico is None:
                self.barra.separador()
            else:
                self.barra.botao(ico, dica, cmd)
        self.rb = Ribbon(self, menu_app=self.menu_app, rotulo_app="Punção")
        self.rb.pack(side="top", fill="x")
        self._ribbon()
        self._barra_status()
        pan = ttk.PanedWindow(self, orient="horizontal")
        pan.pack(side="top", fill="both", expand=True)
        pan.add(self._painel_esquerdo(pan), weight=0)
        pan.add(self._centro(pan), weight=1)
        self.after(320, lambda: pan.sashpos(0, 320))
        for tecla, f in (("<Control-n>", self.novo), ("<Control-o>", self.abrir), ("<Control-s>", self.salvar),
                         ("<Control-S>", self.salvar_como), ("<Control-g>", self.gerar),
                         ("<Control-G>", self.gerar_lote), ("<F5>", self.atualizar), ("<Home>", self.enquadrar),
                         ("<Prior>", lambda: self.ir(self.i - 1)), ("<Next>", lambda: self.ir(self.i + 1))):
            self.bind_all(tecla, lambda e, f=f: self._tecla(e, f))

    def _tecla(self, e, f):
        if isinstance(e.widget, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text)) and \
                e.keysym in ("Home", "Prior", "Next"):
            return
        f()

    def _menus(self):
        mb = tk.Menu(self)
        self.configure(menu=mb)
        m = tk.Menu(mb, tearoff=0)
        self.menu_app = m
        m.add_command(label="Novo projeto", accelerator="Ctrl+N", command=self.novo)
        m.add_command(label="Abrir projeto...", accelerator="Ctrl+O", command=self.abrir)
        ex = tk.Menu(m, tearoff=0)
        for arq in sorted(pathlib.Path(RAIZ, "exemplos").glob("*.json")):
            ex.add_command(label=arq.name, command=lambda a=str(arq): self.abrir(a))
        m.add_cascade(label="Exemplos", menu=ex)
        m.add_separator()
        m.add_command(label="Salvar", accelerator="Ctrl+S", command=self.salvar)
        m.add_command(label="Salvar como...", accelerator="Ctrl+Shift+S", command=self.salvar_como)
        m.add_separator()
        m.add_command(label="Gerar DWG / PDF / DXF do pilar", accelerator="Ctrl+G", command=self.gerar)
        m.add_command(label="Gerar o lote", accelerator="Ctrl+Shift+G", command=self.gerar_lote)
        m.add_separator()
        m.add_command(label="Sair", command=self.sair)
        mb.add_cascade(label="Arquivo", menu=m)
        p = tk.Menu(mb, tearoff=0)
        p.add_command(label="+ Pilar", command=self.mais_pilar)
        p.add_command(label="Duplicar pilar", command=self.duplicar)
        p.add_command(label="Apagar pilar", command=self.apagar)
        p.add_command(label="Importar do TQS...", command=self.importar_tqs)
        p.add_command(label="Colar pilares do Excel...", command=self.colar)
        p.add_separator()
        p.add_command(label="Pilar anterior", accelerator="PgUp", command=lambda: self.ir(self.i - 1))
        p.add_command(label="Pilar seguinte", accelerator="PgDn", command=lambda: self.ir(self.i + 1))
        mb.add_cascade(label="Pilar", menu=p)
        e = tk.Menu(mb, tearoff=0)
        for k, rot in VISTAS:
            e.add_command(label=rot, command=lambda k=k: self.ver(k))
        e.add_separator()
        e.add_command(label="Enquadrar", accelerator="Home", command=self.enquadrar)
        e.add_checkbutton(label="Cores de plotagem (fundo branco)", variable=self.plot, command=self._redesenhar)
        e.add_checkbutton(label="Atualizar automaticamente", variable=self.auto)
        e.add_command(label="Atualizar agora", accelerator="F5", command=self.atualizar)
        mb.add_cascade(label="Exibir", menu=e)
        s = tk.Menu(mb, tearoff=0)
        s.add_command(label="Gerar DWG / PDF / DXF do pilar", accelerator="Ctrl+G", command=self.gerar)
        s.add_command(label="Gerar o lote", accelerator="Ctrl+Shift+G", command=self.gerar_lote)
        s.add_command(label="Relatório do lote (TXT e CSV)", command=self.relatorio_lote)
        s.add_separator()
        s.add_command(label="Abrir o PDF do pilar", command=lambda: self.abrir_saida("pdf"))
        s.add_command(label="Abrir o relatório do lote", command=lambda: self.abrir_saida("relatorio"))
        s.add_command(label="Abrir a pasta de saída", command=lambda: self.abrir_saida("pasta"))
        mb.add_cascade(label="Saídas", menu=s)
        a = tk.Menu(mb, tearoff=0)
        a.add_command(label="Atalhos e comandos", command=self.ajuda)
        a.add_command(label="Sobre", command=lambda: messagebox.showinfo(
            APP, "Detalhamento de armadura de punção de pilares internos em DWG-TQS: cobrinha em malha ortogonal e "
                 "conectores Trejor em arranjo radial.\n\nO app não dimensiona: detalha a armadura definida pelo "
                 "projetista e confere a geometria pela NBR 6118:2026.", parent=self))
        mb.add_cascade(label="Ajuda", menu=a)

    def _V(self, nome, tipo="str"):
        v = tk.BooleanVar() if tipo == "bool" else tk.StringVar()
        self.v[nome] = v
        return v

    def _campo(self, col, chave, rotulo, unidade="", largura=6, dica=None, lr=None):
        return col.campo(rotulo, self._V(chave), largura=largura, unidade=unidade, largura_rot=lr, dica=dica,
                         ao_mudar=lambda: self._mudou(chave))

    def _combo(self, col, chave, rotulo, valores, largura=8, ler=True, dica=None, lr=None):
        return col.combo(rotulo, self._V(chave), valores, largura=largura, ler=ler, largura_rot=lr, dica=dica,
                         ao_mudar=lambda: self._mudou(chave))

    def _ribbon(self):
        rb = self.rb
        # ---------------------------------------------------------------- Pilar
        a = rb.aba("Pilar")
        g = a.grupo("Identificação")
        c = g.coluna()
        self._campo(c, "titulo", "Título", largura=9, lr=9, dica="Nome do pilar no desenho (nível 222).")
        c.spin("Repetições", self._V("repeticoes"), 1, 99, largura=4, largura_rot=9,
               dica="Multiplicador \"Nx\" do nível 202 (o TQS multiplica os ferros no resumo).",
               ao_mudar=lambda: self._mudou("repeticoes"))
        self._combo(c, "solucao", "Solução", ["cobrinha", "conectores"], largura=10, lr=9,
                    dica="Barras dobradas em cobrinha (malha ortogonal) ou conectores Trejor (arranjo radial).")
        g = a.grupo("Pilar (cm)")
        c = g.coluna()
        self._campo(c, "bx", "bx", "cm", dica="Dimensão do pilar na horizontal da prancha.", lr=3)
        self._campo(c, "by", "by", "cm", dica="Dimensão do pilar na vertical da prancha.", lr=3)
        g = a.grupo("Laje (cm)")
        c = g.coluna()
        self._campo(c, "h_laje", "h", "cm", lr=6, dica="Espessura da laje.")
        self._campo(c, "c_sup", "c sup.", "cm", lr=6, dica="Cobrimento superior: a cabeça do pino ou o trecho de "
                    "cima da cobrinha vão até ele.")
        self._campo(c, "c_inf", "c inf.", "cm", lr=6, dica="Cobrimento inferior.")
        c = g.coluna()
        self._campo(c, "fck", "fck", "MPa", lr=4, dica="Concreto da laje: dá o lb da ancoragem das barras de colapso "
                    "além do contorno C'' (NBR 6118, 9.4.2.4). A importação do TQS traz o do edifício.")
        g = a.grupo("Borda livre")
        c = g.coluna()
        self._combo(c, "borda_x", "Em x", [NENHUMA, "esquerda", "direita"], largura=9, lr=5,
                    dica="Borda livre da laje ao lado do pilar, paralela a y (pilar de borda; com a de y, de canto). "
                         "A armadura de punção, a montagem e o colapso vão até o cobrimento da laje nela.")
        self._combo(c, "borda_y", "Em y", [NENHUMA, "baixo", "cima"], largura=9, lr=5,
                    dica="Borda livre paralela a x, embaixo ou em cima do pilar na prancha.")
        c = g.coluna()
        self._campo(c, "dist_borda_x", "Dist.", "cm", lr=4, dica="Distância da face do pilar à borda em x "
                    "(0 = pilar faceando a borda).")
        self._campo(c, "dist_borda_y", "Dist.", "cm", lr=4, dica="Distância da face do pilar à borda em y.")
        g = a.grupo("Altura útil")
        c = g.coluna()
        self._combo(c, "neg_bitola_ext", "Negativa ext.", BITOLAS, largura=5, lr=11,
                    dica="Camada externa da armadura negativa (mm): só para a altura útil.")
        self._combo(c, "neg_bitola_int", "Negativa int.", BITOLAS, largura=5, lr=11,
                    dica="Camada interna da armadura negativa (mm).")
        self._campo(c, "d", "d (vazio = auto)", "cm", lr=13, dica="Altura útil. Vazia, é calculada: d = h - c sup. "
                    "- e - (3 ø1 + ø2)/4, com e = cabeça do pino ou bitola da cobrinha (NBR 6118:2026, 19.5.2.1).")
        c = g.coluna()
        tk.Label(c, textvariable=self.d_calc, font=("Segoe UI", 9), bg=COR_CORPO, fg="#2b5797",
                 justify="left").pack(side="top", anchor="w", padx=4, pady=4)
        g = a.grupo("Desenho")
        c = g.coluna()
        self._campo(c, "escala", "Escala 1:", largura=4, lr=8, dica="Escala da prancha (o modelo é 1:15).")
        # ---------------------------------------------------------------- Cobrinha
        a = rb.aba("Cobrinha")
        g = a.grupo("Malha (cm)")
        c = g.coluna()
        self._campo(c, "cob_s", "Espaçamento", "cm", lr=11, dica="Espaçamento da malha ortogonal (s <= 0,75 d).")
        self._campo(c, "cob_s_x", "Esp. em x", "cm", lr=11, dica="Vazio = o espaçamento geral.")
        self._campo(c, "cob_s_y", "Esp. em y", "cm", lr=11, dica="Vazio = o espaçamento geral.")
        c = g.coluna()
        self._campo(c, "cob_s0", "s0 (da face)", "cm", lr=11, dica="Distância da face à 1ª linha de pernas "
                    "(s0 <= 0,5 d).")
        g = a.grupo("Linhas além das faces")
        c = g.coluna()
        c.spin("Linhas", self._V("cob_linhas"), 1, 20, largura=4, largura_rot=9,
               dica="Linhas de pernas além de cada face, contando a de s0.", ao_mudar=lambda: self._mudou("cob_linhas"))
        self._campo(c, "cob_linhas_x", "Linhas em x", largura=4, lr=9, dica="Vazio = o número geral.")
        self._campo(c, "cob_linhas_y", "Linhas em y", largura=4, lr=9, dica="Vazio = o número geral.")
        g = a.grupo("Barras")
        c = g.coluna()
        self._combo(c, "cob_bitola", "Bitola", BITOLAS, largura=5, lr=8, dica="Bitola da cobrinha (mm), <= h/20.")
        self._combo(c, "cob_direcao", "Direção", ["maior", "menor", "x", "y"], largura=7, lr=8,
                    dica="Cobrinhas paralelas ao lado maior do pilar (padrão) ou ao menor, ou em x ou y.")
        g = a.grupo("Montagem")
        c = g.coluna()
        self._combo(c, "mont_bitola", "Bitola", BITOLAS, largura=5, lr=9, dica="Montagem positiva nas dobras de "
                    "baixo (mm). Também a dos conectores, se ligada.")
        self._campo(c, "mont_ext", "Além (cm)", lr=9, dica="Comprimento além da última linha (cm).")
        self._campo(c, "mont_arred", "Arred. (cm)", lr=9, dica="Comprimento arredondado para cima (cm).")
        c = g.coluna()
        self._campo(c, "mont_min_borda", "Mín. borda", lr=9, dica="Pilar de borda: a montagem ao lado do pilar, da "
                    "face até a borda livre, com menos que isso não é desenhada (borda curta: os vértices ficam na "
                    "armadura da laje).")
        # ---------------------------------------------------------------- Conectores
        a = rb.aba("Conectores")
        g = a.grupo("Pentes (cm)")
        c = g.coluna()
        self._campo(c, "con_s0", "s0 (da face)", "cm", lr=11, dica="Distância da face à 1ª linha de pinos "
                    "(s0 <= 0,5 d).")
        self._campo(c, "con_sr", "sr (entre linhas)", "cm", lr=11, dica="Distância entre linhas de pinos "
                    "(sr <= 0,75 d).")
        c.spin("Pinos/pente", self._V("con_pinos"), 1, 12, largura=4, largura_rot=11,
               dica="Pinos por pente (linhas de pinos; três ou mais).", ao_mudar=lambda: self._mudou("con_pinos"))
        g = a.grupo("Distribuição")
        c = g.coluna()
        c.spin("Face bx", self._V("con_n_face_bx"), 1, 20, largura=4, largura_rot=9,
               dica="Pentes em cada face de comprimento bx (de baixo e de cima).",
               ao_mudar=lambda: self._mudou("con_n_face_bx"))
        c.spin("Face by", self._V("con_n_face_by"), 1, 20, largura=4, largura_rot=9,
               dica="Pentes em cada face de comprimento by (esquerda e direita).",
               ao_mudar=lambda: self._mudou("con_n_face_by"))
        self._campo(c, "con_dist_canto", "Ao canto", "cm", lr=9, dica="Distância do pente ao canto do pilar, ao "
                    "longo da face.")
        c = g.coluna()
        self._combo(c, "con_inclinados", "Inclinados", ["auto", "cruz", "1", "2", "3", "4"], largura=6, ler=False,
                    lr=9, dica="Pentes inclinados por canto: auto = o menor número que deixa os pinos de fora "
                    "vizinhos a <= 2d; cruz = nenhum; ou um número.")
        g = a.grupo("Pino Trejor")
        c = g.coluna()
        self._combo(c, "con_bitola", "Bitola", PINOS, largura=5, lr=9, dica="Pino CA-50 (mm); a cabeça vem do "
                    "catálogo Trejor.")
        self._campo(c, "con_cabeca_esp", "Cabeça", "cm", lr=9, dica="Espessura da cabeça (entra em d): 0,8 + 0,2 de "
                    "concordância, do modelo.")
        self._campo(c, "con_arred_mm", "Arred.", "mm", lr=9, dica="Comprimento do pino arredondado para baixo.")
        g = a.grupo("Trilhos")
        c = g.coluna()
        c.spin("Quant.", self._V("con_trilhos"), 1, 4, largura=4, largura_rot=7,
               dica="Vergalhões que ligam os pinos.", ao_mudar=lambda: self._mudou("con_trilhos"))
        self._combo(c, "con_trilho_bitola", "Bitola", BITOLAS, largura=5, lr=7, dica="Bitola dos trilhos (mm).")
        g = a.grupo("Montagem")
        c = g.coluna()
        c.check("Montagem positiva", self._V("con_montagem", "bool"), ao_mudar=lambda: self._mudou("con_montagem"),
                dica="Opcional e desligada por padrão: o escritório aproveita as barras de flexão da laje (nota 1). "
                     "Ligada: uma barra por linha de pinos em cada face, sobre os trilhos (bitola e comprimento da aba "
                     "Cobrinha > Montagem).")
        # ---------------------------------------------------------------- Colapso
        a = rb.aba("Colapso")
        g = a.grupo("Colapso progressivo (face inferior)")
        c = g.coluna()
        self._combo(c, "col_bitola", "Bitola", BITOLAS, largura=5, lr=10, dica="Bitola das barras (mm).")
        self._campo(c, "col_ext", "Além da face", "cm", lr=10, dica="Comprimento além da face do pilar.")
        c = g.coluna()
        c.spin("Face bx", self._V("col_n_face_bx"), 1, 30, largura=4, largura_rot=8,
               dica="Barras em cada face de comprimento bx (correm em y).", ao_mudar=lambda: self._mudou("col_n_face_bx"))
        c.spin("Face by", self._V("col_n_face_by"), 1, 30, largura=4, largura_rot=8,
               dica="Barras em cada face de comprimento by (correm em x).", ao_mudar=lambda: self._mudou("col_n_face_by"))
        c = g.coluna()
        c.check("Gancho na borda", self._V("col_gancho_borda", "bool"),
                ao_mudar=lambda: self._mudou("col_gancho_borda"),
                dica="Pilar de borda ou de canto: gancho de 90° (ponta de 8ø) nas barras que terminam na borda "
                     "livre. Opcional, desligado por padrão.")
        g = a.grupo("Sugestão (NBR 6118, 19.5.4)")
        g.grande("colapso", "Sugerir no pilar", self.sugerir_colapso, "Com a bitola atual: o nº de barras por face "
                 "pelas cargas do TQS (As·fyd >= 1,5·FSd, FSd = 1,2·Fk, barras que cruzam cada face) e o comprimento "
                 "além da face pela ancoragem além do contorno C'' (a + lb, para cima a 5 cm).")
        g.grande("lote", "Sugerir em todos", lambda: self.sugerir_colapso(todos=True), "A mesma sugestão em todos os "
                 "pilares do projeto.")
        # ---------------------------------------------------------------- Lote
        a = rb.aba("Lote")
        g = a.grupo("Pilar atual")
        c = g.coluna()
        self.cb_pilar = c.combo("Pilar", self.pilar_atual, [], largura=16, largura_rot=5,
                                dica="Pilar mostrado e editado (PgUp / PgDn).", ao_mudar=self._escolher_pilar)
        g.grande("mais_pilar", "+ Pilar", self.mais_pilar, "Pilar novo com os parâmetros do atual.")
        g.grande("duplicar", "Duplicar", self.duplicar, "Cópia do pilar atual.")
        g.grande("apagar", "Apagar", self.apagar, "Apaga o pilar atual do projeto.")
        g = a.grupo("Importar")
        g.grande("importar_tqs", "Importar do TQS", self.importar_tqs, "Pilares de uma planta do TQS (lida numa "
                 "cópia): dimensões, h e cobrimentos da laje, com a escolha dos pilares. Os esforços de ELU da grelha "
                 "ficam no pilar para conferência.")
        g.grande("colar", "Colar do Excel", self.colar, "Linhas Título; bx; by; h; repetições; solução, uma por "
                 "pilar; os demais parâmetros vêm do pilar atual.")
        g = a.grupo("Lote")
        g.grande("lote", "Tabela do lote", lambda: self.ver_tabela("lote"), "Todos os pilares: dimensões, solução, "
                 "pentes ou peças, aço e avisos.")
        g.grande("listar", "Relatório do lote", self.relatorio_lote, "Pilares, ferros, resumo de aço por bitola, "
                 "pentes, avisos e erros em TXT e CSV (Excel), na pasta de saída. Não precisa do TQS: usa os "
                 "comprimentos do TQS dos pilares já gravados e sem mudança; nos outros, os do núcleo.")
        g.grande("gerar_lote", "Gerar o lote", self.gerar_lote, "Um DWG-TQS por pilar (PDF e DXF), pelo TQS, e o "
                 "relatório do lote.")
        # ---------------------------------------------------------------- Exibir
        a = rb.aba("Exibir")
        g = a.grupo("Vistas")
        for k, rot, ico in (("planta", "Planta", "planta"), ("corte", "Corte", "corte"), ("colapso", "Colapso", "colapso"),
                            ("prancha", "Prancha", "prancha"), ("tabela", "Tabela", "tabela")):
            g.grande(ico, rot, lambda k=k: self.ver(k), f"Mostra a vista {rot.lower()}.")
        g = a.grupo("Zoom")
        g.grande("enquadrar", "Enquadrar", self.enquadrar, "Enquadra a vista (Home ou duplo clique no botão do meio).")
        c = g.coluna()
        c.pequeno("ampliar", "Ampliar", lambda: self.vista.zoom(1.25))
        c.pequeno("reduzir", "Reduzir", lambda: self.vista.zoom(0.8))
        g = a.grupo("Cores")
        self.bt_cores = g.grande("cores", "Cores de plotagem", self._alternar_cores,
                                 "Alterna entre as cores de tela do TQS (fundo preto) e as da plotagem (fundo branco, "
                                 "penas da TABPLTA).", alternar=True)
        g = a.grupo("Atualização")
        c = g.coluna()
        c.check("Atualizar automaticamente", self.auto)
        c.pequeno("regerar", "Atualizar agora (F5)", self.atualizar)
        # ---------------------------------------------------------------- Saídas
        a = rb.aba("Saídas")
        g = a.grupo("Pasta e arquivos")
        c = g.coluna()
        c.campo("Pasta", self.pasta, largura=34, largura_rot=5,
                dica="Pasta dos DWG (vazia = saidas\\<projeto>). Um DWG por pilar: PUN_<pilar>.DWG.")
        c.pequeno("pasta", "Escolher a pasta...", self.escolher_pasta)
        c = g.coluna()
        c.check("PDF", self.pdf, dica="Grava também o PDF (pelo TQS, com o carimbo da licença).")
        c.check("DXF", self.dxf, dica="Grava também o DXF (cores da plotagem).")
        g = a.grupo("Gerar")
        g.grande("gerar", "Gerar o pilar", self.gerar, "DWG-TQS do pilar atual, com PDF e DXF, e conferência dos "
                 "comprimentos que o TQS calcula (Ctrl+G).")
        g.grande("gerar_lote", "Gerar o lote", self.gerar_lote, "Todos os pilares e o relatório do lote "
                 "(Ctrl+Shift+G).")
        g.grande("listar", "Relatório do lote", self.relatorio_lote, "TXT e CSV (Excel) com pilares, ferros, aço "
                 "por bitola, pentes e avisos, sem o TQS.")
        g = a.grupo("Abrir")
        c = g.coluna()
        c.pequeno("pdf", "PDF do pilar", lambda: self.abrir_saida("pdf"))
        c.pequeno("listar", "Relatório do lote", lambda: self.abrir_saida("relatorio"))
        c.pequeno("pasta", "Pasta de saída", lambda: self.abrir_saida("pasta"))
        rb.selecionar("Pilar")

    def _painel_esquerdo(self, pai):
        fr = tk.Frame(pai, bg="#ffffff", width=320)
        cab = tk.Frame(fr, bg="#e9edf2")
        cab.pack(fill="x")
        tk.Label(cab, text="  Projeto", font=("Segoe UI", 9, "bold"), bg="#e9edf2", anchor="w", pady=3).pack(side="left")
        pw = ttk.PanedWindow(fr, orient="vertical")
        pw.pack(fill="both", expand=True)
        f1 = tk.Frame(pw, bg="white")
        self.tv = ttk.Treeview(f1, show="tree", style="Arvore.Treeview", selectmode="browse")
        sb = ttk.Scrollbar(f1, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv.pack(side="left", fill="both", expand=True)
        self.tv.tag_configure("aviso", foreground="#9a4a00")
        self.tv.tag_configure("erro", foreground="#b3261e")
        self.tv.tag_configure("cinza", foreground="#808080")
        self.tv.tag_configure("negrito", font=("Segoe UI", 9, "bold"))
        self.tv.bind("<<TreeviewSelect>>", self._ao_selecionar_arvore)
        pw.add(f1, weight=3)
        f2 = tk.Frame(pw, bg="white")
        cab = tk.Frame(f2, bg="#e9edf2")
        cab.pack(fill="x")
        tk.Label(cab, text="  Propriedades", font=("Segoe UI", 9, "bold"), bg="#e9edf2", anchor="w", pady=3).pack(
            side="left")
        self.tp = ttk.Treeview(f2, columns=("v",), show="tree", height=10, selectmode="none")
        self.tp.column("#0", width=130)
        self.tp.column("v", width=180)
        self.tp.pack(fill="both", expand=True)
        pw.add(f2, weight=2)
        return fr

    def _centro(self, pai):
        fr = tk.Frame(pai, bg="#000000")
        pw = ttk.PanedWindow(fr, orient="vertical")
        pw.pack(fill="both", expand=True)
        cima = tk.Frame(pw, bg="#000000")
        self.area = tk.Frame(cima, bg="#000000")
        self.area.pack(side="top", fill="both", expand=True)
        self.vista = Vista(self.area)
        self.vista.ao_mover = self._ao_mover
        self.vista.ao_clicar = self._ao_clicar
        self.vista.ao_menu = self._ao_menu
        self.f_tab = self._vista_tabela(self.area)
        abas = tk.Frame(cima, bg="#dcdcdc")
        abas.pack(side="bottom", fill="x")
        self.abas_vista = {}
        for k, rot in VISTAS:
            lb = tk.Label(abas, text=rot, font=("Segoe UI", 9), bg="#dcdcdc", padx=12, pady=2, cursor="hand2")
            lb.pack(side="left", padx=(0, 1))
            lb.bind("<Button-1>", lambda e, k=k: self.ver(k))
            self.abas_vista[k] = lb
        tk.Label(abas, text="Roda: zoom   Botão do meio ou direito: deslocar   Duplo clique no meio: enquadrar   "
                            "Clique: selecionar", font=("Segoe UI", 8), bg="#dcdcdc", fg="#555555").pack(side="right",
                                                                                                    padx=8)
        pw.add(cima, weight=5)
        baixo = tk.Frame(pw, bg="#ffffff")
        bts = tk.Frame(baixo, bg="#f3f3f3")
        bts.pack(side="right", fill="y")
        ttk.Button(bts, text="Copiar", width=8, command=self._copiar_msgs).pack(padx=4, pady=(4, 2))
        ttk.Button(bts, text="Limpar", width=8, command=self._limpar_msgs).pack(padx=4)
        self.txm = tk.Text(baixo, height=6, font=("Consolas", 9), wrap="word", bd=0, padx=6, pady=3, state="disabled")
        sb = ttk.Scrollbar(baixo, orient="vertical", command=self.txm.yview)
        self.txm.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txm.pack(side="left", fill="both", expand=True)
        for k, c in NIVEL_COR.items():
            self.txm.tag_configure(k, foreground=c)
        pw.add(baixo, weight=1)
        self.after(300, lambda: pw.sashpos(0, max(200, pw.winfo_height() - 130)))
        self.ver(self.vista_atual)
        return fr

    def _vista_tabela(self, pai):
        fr = tk.Frame(pai, bg="#ffffff")
        top = tk.Frame(fr, bg="#f3f3f3")
        top.pack(fill="x")
        self.tab_sel = tk.StringVar(value="ferros")
        for k, rot in (("ferros", "Ferros"), ("pecas", "Pentes / cobrinhas"), ("verificacoes", "Verificações"),
                       ("lote", "Lote")):
            ttk.Radiobutton(top, text=rot, variable=self.tab_sel, value=k, style="Toolbutton",
                            command=self._tabela).pack(side="left", padx=1, pady=3)
        ttk.Button(top, text="Copiar (Excel)", command=self.copiar_tabela).pack(side="right", padx=6)
        self.tt = ttk.Treeview(fr, show="headings")
        sb = ttk.Scrollbar(fr, orient="vertical", command=self.tt.yview)
        self.tt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tt.pack(fill="both", expand=True)
        return fr

    def _barra_status(self):
        sb = tk.Frame(self, bg="#e9e9e9", highlightthickness=1, highlightbackground="#d0d0d0")
        sb.pack(side="bottom", fill="x")
        self.st_msg = tk.Label(sb, text="Pronto", font=("Segoe UI", 9), bg="#e9e9e9", anchor="w")
        self.st_msg.pack(side="left", fill="x", expand=True, padx=6)
        self.pb = ttk.Progressbar(sb, mode="indeterminate", length=120)
        self.st_xy = tk.Label(sb, text="", font=("Consolas", 9), bg="#e9e9e9", width=26, anchor="e")
        self.st_xy.pack(side="right", padx=6)
        self.st_tot = tk.Label(sb, text="", font=("Segoe UI", 9), bg="#e9e9e9", anchor="e")
        self.st_tot.pack(side="right", padx=8)
        self.st_pilar = tk.Label(sb, text="", font=("Segoe UI", 9, "bold"), bg="#e9e9e9", fg="#2b5797")
        self.st_pilar.pack(side="right", padx=8)

    # ================================================================== mensagens e estado
    def msg(self, s, nivel="info"):
        self.txm.configure(state="normal")
        self.txm.insert("end", s + "\n", nivel)
        self.txm.see("end")
        self.txm.configure(state="disabled")

    def _limpar_msgs(self):
        self.txm.configure(state="normal")
        self.txm.delete("1.0", "end")
        self.txm.configure(state="disabled")

    def _copiar_msgs(self):
        self.clipboard_clear()
        self.clipboard_append(self.txm.get("1.0", "end"))

    def status(self, s, nivel="info"):
        self.st_msg.configure(text=s, fg=NIVEL_COR.get(nivel, "#202020"))

    def _titulo(self):
        nome = self._nome_projeto()
        self.title(f"{APP} - [{nome} - {self.arq or '(não salvo)'}]" + (" *" if self.modificado else ""))

    def _nome_projeto(self):
        return os.path.splitext(os.path.basename(self.arq))[0] if self.arq else "sem_nome"

    def _inicio(self):
        self.msg("Detalhamento de armadura de punção (sem dimensionamento). Abra um projeto (Ctrl+O) ou um exemplo "
                 "(Arquivo > Exemplos), ou edite o pilar nas abas do ribbon.", "cinza")
        self._carregar_pilar(enquadrar=True)

    # ================================================================== pilar atual <-> ribbon
    @property
    def pilar(self):
        return self.projeto["pilares"][self.i]

    def _efetivo(self):
        return {**PADROES, **self.pilar}

    def _par_para_ui(self):
        self._sync = True
        try:
            ef = self._efetivo()
            for k, var in self.v.items():
                val = ef.get(k)
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(val))
                elif val is None:
                    var.set("")
                elif k in TEXTOS:
                    var.set(str(val) or (NENHUMA if k in BORDAS else ""))
                else:
                    var.set(fmt(float(val)) if not isinstance(val, int) or k not in INTEIROS else str(val))
            self.pilar_atual.set(self._rotulo_pilar(self.i))
            self.cb_pilar.configure(values=[self._rotulo_pilar(j) for j in range(len(self.projeto["pilares"]))])
        finally:
            self._sync = False

    def _rotulo_pilar(self, j):
        p = {**PADROES, **self.projeto["pilares"][j]}
        return f"{j + 1}. {p['titulo']} ({fmt(float(p['bx']))}x{fmt(float(p['by']))})"

    def _ler_campo(self, k):
        var = self.v[k]
        if isinstance(var, tk.BooleanVar):
            return var.get()
        s = var.get().strip()
        if k in TEXTOS:
            return "" if k in BORDAS and s == NENHUMA else s
        if s == "":
            if k in OPCIONAIS:
                return None
            raise ValueError(f"{k}: vazio")
        x = num(s)
        return int(round(x)) if k in INTEIROS else x

    def _mudou(self, k):
        if self._sync:
            return
        try:
            val = self._ler_campo(k)
        except ValueError:
            self.status(f"Valor inválido em {k}: {self.v[k].get()!r}", "erro")
            return
        p = self.pilar
        antigo = p.get(k, PADROES.get(k))
        if val == antigo:
            return
        if k not in ("titulo", "solucao") and val == PADROES.get(k):
            p.pop(k, None)
        else:
            p[k] = val
        self.modificado = True
        self._titulo()
        if k == "solucao":
            self.rb.selecionar("Cobrinha" if val == "cobrinha" else "Conectores")
        if k in ("titulo", "bx", "by"):
            self._par_para_ui()
        self._agendar()

    def _agendar(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if self.auto.get():
            self._job = self.after(350, self.atualizar)
        else:
            self.status("Parâmetros alterados: Atualizar agora (F5).", "aviso")

    # ================================================================== cálculo e desenho
    def atualizar(self):
        self._job = None
        self.res = detalhar(self.pilar)
        self.folha = None
        p = self.res["p"]
        if not self.res["erros"]:
            try:
                mod = prancha_cobrinha if p["solucao"] == "cobrinha" else prancha_conectores
                self.folha = mod.montar(self.res)
            except NotImplementedError as e:
                self.res["erros"].append(str(e))
            except Exception:
                self.res["erros"].append("erro ao montar a prancha: " + traceback.format_exc().strip().splitlines()[-1])
                self.msg(traceback.format_exc(), "cinza")
        self._mostrar_resultado()

    def _mostrar_resultado(self):
        r, p = self.res, self.res["p"]
        self._limpar_msgs()
        cab = f"{p['titulo']} ({fmt(float(p['bx']))} x {fmt(float(p['by']))}), laje {fmt(float(p['h_laje']))}, " \
              f"{p['solucao']}, {p['repeticoes']}X"
        self.msg(cab, "info")
        for e in r["erros"]:
            self.msg(f"ERRO: {e}", "erro")
        for tipo, txt, ref in r.get("verificacoes", []):
            self.msg(f"{'AVISO' if tipo == 'aviso' else 'ok   '} {txt} ({ref})", "aviso" if tipo == "aviso" else "ok")
        try:
            self.d_calc.set(f"d = {_br(altura_util(p), 2)} cm" + (" (informada)" if p.get("d") else " (calculada)"))
        except Exception:
            self.d_calc.set("")
        aco = sum(_kg(f["bitola"], f["comp"], f["quant"]) for f in r["ferros"])
        self.st_tot.configure(text=f"Aço (ferros do TQS): {_br(aco)} kg x {p['repeticoes']}" if r["ferros"] else "")
        self.st_pilar.configure(text=f"Pilar {self.i + 1} de {len(self.projeto['pilares'])}: {p['titulo']}")
        n_av = sum(1 for v in r.get("verificacoes", []) if v[0] == "aviso")
        if r["erros"]:
            self.status("Erro nos parâmetros (veja as mensagens).", "erro")
        else:
            self.status(f"{p['titulo']}: {len(r['ferros'])} posições, {n_av} aviso(s).", "aviso" if n_av else "ok")
        self._redesenhar()
        self._arvore()
        self._props_pilar()
        if self.vista_atual == "tabela":
            self._tabela()

    def _redesenhar(self):
        self.bt_cores.marcar(self.plot.get())
        if self.folha is None:
            self.vista.limpar()
            self.info = {}
            return
        self.info = cena.desenhar(self.vista, self.folha, "plot" if self.plot.get() else "tela", self.res["ferros"])
        if self._enquadrar:
            self.after_idle(self.enquadrar)
            self._enquadrar = False

    def ver(self, k):
        self.vista_atual = k
        for kk, lb in self.abas_vista.items():
            lb.configure(bg="#ffffff" if kk == k else "#dcdcdc", font=("Segoe UI", 9, "bold" if kk == k else "normal"))
        if k == "tabela":
            self.vista.pack_forget()
            self.f_tab.pack(fill="both", expand=True)
            self._tabela()
        else:
            self.f_tab.pack_forget()
            self.vista.pack(fill="both", expand=True)
            self.after_idle(self.enquadrar)

    def enquadrar(self):
        if self.vista_atual == "tabela" or not self.folha:
            return
        reg = self.folha.regioes.get(self.vista_atual) or self.folha.regioes.get("prancha")
        if reg:
            m = 0.04 * max(reg[2] - reg[0], reg[3] - reg[1])
            self.vista.enquadrar((reg[0] - m, reg[1] - m, reg[2] + m, reg[3] + m), 0.02)

    def _alternar_cores(self):
        self.plot.set(not self.plot.get())
        self._redesenhar()

    def _ao_mover(self, x, y, chave):
        self.st_xy.configure(text=f"x = {_br(x)}  y = {_br(y)} cm")
        if chave and chave in self.info:
            self.status(self.info[chave])

    def _ao_clicar(self, chave, x=None, y=None):
        self.vista.destacar([chave] if chave else [])
        if not chave:
            self._props_pilar()
            return
        if chave.startswith("f:"):
            pos = int(chave[2:])
            fe = next((f for f in self.res["ferros"] if f["pos"] == pos), None)
            if fe:
                self._props_ferro(fe)
                iid = f"ferro:{pos}"
                if self.tv.exists(iid):
                    self._sync_arvore = True
                    self.tv.selection_set(iid)
                    self.tv.see(iid)
                return
        self._props([("Item", self.info.get(chave, chave))])

    def _ao_menu(self, xr, yr, chave, x, y):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Enquadrar", command=self.enquadrar)
        for k, rot in VISTAS[:4]:
            m.add_command(label=f"Vista: {rot}", command=lambda k=k: self.ver(k))
        m.add_separator()
        m.add_checkbutton(label="Cores de plotagem", variable=self.plot, command=self._redesenhar)
        m.add_separator()
        m.add_command(label="Gerar DWG / PDF / DXF do pilar", command=self.gerar)
        m.tk_popup(xr, yr)

    # ================================================================== árvore e propriedades
    def _arvore(self):
        tv = self.tv
        tv.delete(*tv.get_children())
        raiz = tv.insert("", "end", "projeto", text=f"Projeto: {self._nome_projeto()}", image=ic.foto("lote", 16),
                         open=True, tags=("negrito",))
        for j, par in enumerate(self.projeto["pilares"]):
            p = {**PADROES, **par}
            atual = j == self.i
            rot = f"{p['titulo']} ({fmt(float(p['bx']))}x{fmt(float(p['by']))}) - {p['solucao']}, " \
                  f"{p['repeticoes']}X"
            tags = ("negrito",) if atual else ()
            if atual and self.res:
                if self.res["erros"]:
                    tags += ("erro",)
                elif any(v[0] == "aviso" for v in self.res.get("verificacoes", [])):
                    tags += ("aviso",)
            no = tv.insert(raiz, "end", f"pilar:{j}", text=rot, open=atual, tags=tags,
                           image=ic.foto("cobrinha" if p["solucao"] == "cobrinha" else "pente", 16))
            tq = par.get("tqs")
            if atual and tq:
                es = tq.get("esforcos") or []
                nt = tv.insert(no, "end", "tqs", text=f"TQS: {tq.get('planta')}, {tq.get('posicao') or '-'}; "
                               f"esforços de ELU ({len(es)}) para conferência", image=ic.foto("importar_tqs", 16))
                for k, e in enumerate(es):
                    tv.insert(nt, "end", f"esf:{k}", text=f"Comb. {e['n']} {e['titulo']}: Fz {_br(e['fz'], 2)} tf, "
                              f"Mx {_br(e['mx'], 2)}, My {_br(e['my'], 2)} tf·m", tags=("cinza",))
            if not atual or not self.res or self.res["erros"]:
                continue
            r = self.res
            fe = tv.insert(no, "end", "ferros", text=f"Ferros ({len(r['ferros'])} posições)", open=True,
                           image=ic.foto("listar", 16))
            for f in r["ferros"]:
                tv.insert(fe, "end", f"ferro:{f['pos']}", text=f"N{f['pos']}  {f['quant']} ø{fmt(float(f['bitola']))} "
                          f"C={f['comp']} - {f['descricao']}")
            if "conectores" in r:
                c = r["conectores"]
                tv.insert(no, "end", "pecas", text=f"Pentes: {r['p']['repeticoes']} x {c['n_pentes']} {c['nome_bloco']}"
                          f" ({c['inclinados']} inclinado(s) por canto); pino {fmt(c['pino']['comprimento_mm'])} mm",
                          image=ic.foto("pente", 16))
            elif "cobrinha" in r:
                c = r["cobrinha"]
                tv.insert(no, "end", "pecas", text=f"Cobrinhas: {c['n_pecas']} peças em {c['direcao']}, "
                          f"{c['n_linhas']} linhas", image=ic.foto("cobrinha", 16))
            vs = r.get("verificacoes", [])
            n_av = sum(1 for v in vs if v[0] == "aviso")
            ve = tv.insert(no, "end", "verificacoes", text=f"Verificações ({n_av} aviso(s))", open=bool(n_av),
                           image=ic.foto("aviso" if n_av else "ok", 16), tags=("aviso",) if n_av else ())
            for k, (tipo, txt, ref) in enumerate(vs):
                tv.insert(ve, "end", f"verif:{k}", text=txt, tags=("aviso",) if tipo == "aviso" else ("cinza",))
            vi = tv.insert(no, "end", "vistas", text="Vistas", open=False, image=ic.foto("prancha", 16))
            for k, rot in VISTAS:
                tv.insert(vi, "end", f"vista:{k}", text=rot)

    def _ao_selecionar_arvore(self, _=None):
        if getattr(self, "_sync_arvore", False):
            self._sync_arvore = False
            return
        sel = self.tv.selection()
        if not sel:
            return
        iid = sel[0]
        if iid.startswith("pilar:"):
            j = int(iid.split(":")[1])
            if j != self.i:
                self.ir(j)
            else:
                self._props_pilar()
        elif iid.startswith("ferro:"):
            pos = int(iid.split(":")[1])
            fe = next((f for f in self.res["ferros"] if f["pos"] == pos), None)
            if fe:
                self._props_ferro(fe)
                if self.vista_atual == "tabela":
                    self.ver("prancha")
                self.vista.destacar([f"f:{pos}"])
        elif iid.startswith("vista:"):
            self.ver(iid.split(":")[1])
        elif iid.startswith("verif:"):
            tipo, txt, ref = self.res["verificacoes"][int(iid.split(":")[1])]
            self._props([("Situação", "AVISO" if tipo == "aviso" else "ok"), ("Verificação", txt), ("Referência", ref)])
        elif iid == "pecas":
            self.ver_tabela("pecas")
        elif iid == "tqs":
            self._props_tqs()
        elif iid.startswith("esf:"):
            e = self.pilar["tqs"]["esforcos"][int(iid.split(":")[1])]
            self._props([("Combinação", f"{e['n']} - {e['titulo']}"), ("Fz", f"{_br(e['fz'], 2)} tf"),
                         ("Mx", f"{_br(e['mx'], 2)} tf·m"), ("My", f"{_br(e['my'], 2)} tf·m"),
                         ("Origem", "grelha do TQS, característico (conferência)")])

    def _props(self, itens):
        self.tp.delete(*self.tp.get_children())
        for k, v in itens:
            self.tp.insert("", "end", text=k, values=(v,))

    def _props_pilar(self):
        if not self.res:
            return
        r, p = self.res, self.res["p"]
        itens = [("Pilar", p["titulo"]), ("Dimensões", f"{fmt(float(p['bx']))} x {fmt(float(p['by']))} cm"),
                 ("Repetições", f"{p['repeticoes']}X"), ("Laje", f"h = {fmt(float(p['h_laje']))} cm"),
                 ("Cobrimentos", f"{fmt(float(p['c_sup']))} / {fmt(float(p['c_inf']))} cm"), ("Solução", p["solucao"]),
                 ("Posição", _posicao_txt(p))]
        if not r["erros"]:
            itens.append(("Altura útil", f"{_br(r['d'], 2)} cm"))
            aco = sum(_kg(f["bitola"], f["comp"], f["quant"]) for f in r["ferros"])
            itens.append(("Aço dos ferros", f"{_br(aco)} kg por pilar"))
            if "conectores" in r:
                c = r["conectores"]
                itens += [("Pentes", f"{c['n_pentes']} {c['nome_bloco']}"), ("Inclinados", f"{c['inclinados']} por canto"),
                          ("Pino", f"ø{fmt(c['pino']['bitola'])} x {fmt(c['pino']['comprimento_mm'])} mm, "
                                   f"cabeça {c['pino']['cabeca_mm']} mm"),
                          ("Cantos (2d)", f"{_br(c['esp_canto_max'])} / {_br(2 * r['d'])} cm")]
            elif "cobrinha" in r:
                c = r["cobrinha"]
                itens += [("Cobrinhas", f"{c['n_pecas']} peças em {c['direcao']}"),
                          ("Altura (eixo)", f"{fmt(c['altura_eixo'])} cm")]
            itens.append(("Avisos", str(sum(1 for v in r["verificacoes"] if v[0] == "aviso"))))
            tq = self.pilar.get("tqs")
            if tq:
                itens += [("Origem", f"TQS: {os.path.basename(str(tq.get('edificio', '')))} / {tq.get('planta', '')}"),
                          ("Esforços (TQS)", imp.resumo_esforcos(tq.get("esforcos")))]
        else:
            itens.append(("Erros", str(len(r["erros"]))))
        self._props(itens)

    def _props_tqs(self):
        tq = self.pilar.get("tqs") or {}
        itens = [("Edifício", tq.get("edificio", "")), ("Planta", tq.get("planta", "")),
                 ("Pilar no TQS", f"nº {tq.get('numero', '')}, seção {tq.get('secao', '')}, "
                                  f"ângulo {tq.get('angulo', 0):g}°"),
                 ("Centro (cm)", ", ".join(_br(c) for c in tq.get("centro", []))), ("Posição", tq.get("posicao") or "-"),
                 ("Grelha", tq.get("grelha") or "-"), ("Governante (ELU)", imp.resumo_esforcos(tq.get("esforcos")))]
        itens += [("Aviso", a) for a in tq.get("avisos", [])]
        self._props(itens)

    def _props_ferro(self, f):
        tot = f["quant"] * f["comp"] / 100.0
        self._props([("Posição", f"N{f['pos']}"), ("Quantidade", str(f["quant"])),
                     ("Bitola", f"ø{fmt(float(f['bitola']))} mm"), ("Comprimento", f"C={f['comp']} cm"),
                     ("Total", f"{_br(tot, 2)} m"), ("Peso", f"{_br(_kg(f['bitola'], f['comp'], f['quant']), 2)} kg"),
                     ("Descrição", f["descricao"])])

    # ================================================================== tabela
    def ver_tabela(self, k):
        self.tab_sel.set(k)
        self.ver("tabela")

    def _tabela(self):
        k = self.tab_sel.get()
        cols, linhas = self._dados_tabela(k)
        tt = self.tt
        tt.delete(*tt.get_children())
        tt.configure(columns=[c for c, _ in cols])
        def numero(v):
            try:
                float(str(v).replace(",", "."))
                return True
            except ValueError:
                return str(v) == ""
        for j, (c, larg) in enumerate(cols):
            tt.heading(c, text=c)
            direita = linhas and all(numero(lin[j]) for lin in linhas if j < len(lin))
            tt.column(c, width=larg, anchor="e" if direita else "w")
        for lin in linhas:
            tt.insert("", "end", values=lin)

    def _dados_tabela(self, k):
        r = self.res
        if k == "lote":
            cols = [("Pilar", 90), ("Solução", 90), ("bx", 50), ("by", 50), ("h", 50), ("Rep.", 50),
                    ("Armadura de punção", 260), ("Aço (kg)", 80), ("Aço x rep. (kg)", 100), ("Avisos", 60), ("Erros", 50),
                    ("TQS: Fz máx ELU (tf)", 130)]
            linhas = []
            for par in self.projeto["pilares"]:
                rr = detalhar(par)
                p = rr["p"]
                if rr["erros"]:
                    linhas.append((p["titulo"], p["solucao"], fmt(float(p["bx"] or 0)), fmt(float(p["by"] or 0)),
                                   fmt(float(p["h_laje"] or 0)), p["repeticoes"], "; ".join(rr["erros"]), "", "", "",
                                   len(rr["erros"]), _fz_tqs(par)))
                    continue
                if "conectores" in rr:
                    c = rr["conectores"]
                    arm = f"{c['n_pentes']} pentes {c['nome_bloco']}, pino {fmt(c['pino']['comprimento_mm'])} mm"
                else:
                    c = rr["cobrinha"]
                    arm = f"{c['n_pecas']} cobrinhas ø{fmt(float(p['cob_bitola']))}"
                aco = sum(_kg(f["bitola"], f["comp"], f["quant"]) for f in rr["ferros"])
                linhas.append((p["titulo"], p["solucao"], fmt(float(p["bx"])), fmt(float(p["by"])),
                               fmt(float(p["h_laje"])), p["repeticoes"], arm, _br(aco), _br(aco * p["repeticoes"]),
                               sum(1 for v in rr["verificacoes"] if v[0] == "aviso"), 0, _fz_tqs(par)))
            return cols, linhas
        if not r or r["erros"]:
            return [("Mensagem", 600)], [(e,) for e in (r["erros"] if r else ["sem pilar"])]
        if k == "ferros":
            cols = [("Posição", 70), ("Quant.", 60), ("Bitola (mm)", 80), ("C (cm)", 70), ("Total (m)", 80),
                    ("Peso (kg)", 80), ("Descrição", 380)]
            linhas = [(f"N{f['pos']}", f["quant"], fmt(float(f["bitola"])), f["comp"],
                       _br(f["quant"] * f["comp"] / 100, 2), _br(_kg(f["bitola"], f["comp"], f["quant"]), 2),
                       f["descricao"]) for f in r["ferros"]]
            aco = sum(_kg(f["bitola"], f["comp"], f["quant"]) for f in r["ferros"])
            linhas.append(("Total", "", "", "", "", _br(aco, 2), f"por pilar (x {r['p']['repeticoes']})"))
            return cols, linhas
        if k == "pecas":
            if "conectores" in r:
                c = r["conectores"]
                cols = [("Pente", 60), ("Face", 160), ("x (cm)", 80), ("y (cm)", 80), ("Ângulo", 70),
                        ("Pinos", 60), ("Pino de fora (cm)", 160)]
                linhas = [(j + 1, pt["face"], _br(pt["x"], 2), _br(pt["y"], 2), f"{pt['ang'] % 360:g}°",
                           len(pt["pinos"]), f"({_br(pt['pinos'][-1][0], 2)}; {_br(pt['pinos'][-1][1], 2)})")
                          for j, pt in enumerate(c["pentes"])]
                linhas += [("", "Quadro", "", "", "", "", ""), *[("", q, "", "", "", "", "") for q in c["quadro"]]]
                return cols, linhas
            c = r["cobrinha"]
            cols = [("Peça", 60), ("Tipo", 110), ("Linha (cm)", 90), ("Início (cm)", 90), ("Pernas", 70),
                    ("C (cm)", 70)]
            linhas = [(j + 1, pc["tipo"], _br(pc["linha"], 2), _br(pc["ini"], 2), len(pc["pernas"]), round(pc["comp"]))
                      for j, pc in enumerate(c["pecas"])]
            return cols, linhas
        cols = [("Situação", 80), ("Verificação", 560), ("Referência", 300)]
        return cols, [("AVISO" if t == "aviso" else "ok", txt, ref) for t, txt, ref in r["verificacoes"]]

    def copiar_tabela(self):
        cols = self.tt["columns"]
        lin = ["\t".join(self.tt.heading(c)["text"] for c in cols)]
        for it in self.tt.get_children():
            lin.append("\t".join(str(v) for v in self.tt.item(it)["values"]))
        self.clipboard_clear()
        self.clipboard_append("\n".join(lin))
        self.status("Tabela copiada (cole no Excel).", "ok")

    # ================================================================== lote
    def ir(self, j):
        n = len(self.projeto["pilares"])
        if not 0 <= j < n:
            return
        self.i = j
        self._carregar_pilar(enquadrar=True)

    def _carregar_pilar(self, enquadrar=False):
        self._par_para_ui()
        self._enquadrar = enquadrar
        self._titulo()
        self.atualizar()

    def _escolher_pilar(self):
        rot = self.pilar_atual.get()
        try:
            self.ir(int(rot.split(".")[0]) - 1)
        except ValueError:
            pass

    def _titulo_livre(self, base):
        usados = {str({**PADROES, **p}["titulo"]) for p in self.projeto["pilares"]}
        if base not in usados:
            return base
        k = 2
        while f"{base}-{k}" in usados:
            k += 1
        return f"{base}-{k}"

    def mais_pilar(self):
        novo = copy.deepcopy(self.pilar)
        novo.pop("tqs", None)                           # o pilar novo não é o do TQS
        n = len(self.projeto["pilares"]) + 1
        novo["titulo"] = self._titulo_livre(f"P{n}")
        self.projeto["pilares"].insert(self.i + 1, novo)
        self._editado(f"Pilar {novo['titulo']} criado com os parâmetros de {self._efetivo()['titulo']}.")
        self.ir(self.i + 1)

    def duplicar(self):
        novo = copy.deepcopy(self.pilar)
        novo["titulo"] = self._titulo_livre(str(self._efetivo()["titulo"]))
        self.projeto["pilares"].insert(self.i + 1, novo)
        self._editado(f"Pilar duplicado: {novo['titulo']}.")
        self.ir(self.i + 1)

    def apagar(self):
        if len(self.projeto["pilares"]) == 1:
            messagebox.showinfo(APP, "O projeto precisa de pelo menos um pilar.", parent=self)
            return
        t = self._efetivo()["titulo"]
        if not messagebox.askyesno(APP, f"Apagar o pilar {t} do projeto?", parent=self):
            return
        del self.projeto["pilares"][self.i]
        self._editado(f"Pilar {t} apagado.")
        self.ir(min(self.i, len(self.projeto["pilares"]) - 1))

    def importar_tqs(self):
        """Pilares de uma planta do TQS (DlgImportar): os novos entram no fim; os de mesmo nome são atualizados
        (geometria e origem) ou pulados. Um projeto novo e intocado perde o pilar de exemplo."""
        if not messagebox.askokcancel(APP, AVISO_IMPORTACAO, icon="warning", parent=self):
            return
        r = DlgImportar(self, self.pilar, inicial=self.projeto.get("origem_tqs")).mostrar()
        if not r:
            return
        intocado = not self.arq and not self.modificado and self.projeto["pilares"] == [NOVO_PILAR]
        base = [] if intocado else self.projeto["pilares"]
        pilares, n_novos, n_atual, pulados = imp.mesclar(base, r["pilares"], r["atualizar"])
        if not pilares:
            self.msg("Nada importado: os pilares já estão no projeto.", "aviso")
            return
        ajustes, colapsos = {}, {}
        importados = {str(q["titulo"]) for q in r["pilares"]} - set(pulados)
        for k, q in enumerate(pilares):
            if str(q.get("titulo")) not in importados:
                continue
            if r.get("ajustar"):                   # nos novos e nos atualizados, com o d da laje importada
                pilares[k], mud = imp.ajustar_limites(q)
                if mud:
                    ajustes[q["titulo"]] = mud
            if r.get("colapso"):                   # depois do ajuste: C'' depende da última linha
                res = detalhar(pilares[k])
                if not res["erros"]:
                    mud, txt = ncol.sugerir(res)
                    pilares[k] = {**pilares[k], **mud}
                    colapsos[q["titulo"]] = txt
        self.projeto["pilares"] = pilares
        self.projeto["origem_tqs"] = r["origem"]
        tit = str(r["pilares"][0]["titulo"])
        # Primeiro o pilar (a atualização refaz as mensagens com as verificações dele); depois o resumo da importação.
        self.ir(next((k for k, q in enumerate(pilares) if str(q.get("titulo")) == tit), 0))
        resumo = (f"Importados do TQS ({r['origem']['planta']}): {n_novos} novo(s), {n_atual} atualizado(s)" +
                  (f"; pulados (já no projeto): {', '.join(pulados)}" if pulados else "") +
                  (f"; {len(ajustes)} ajustado(s) aos limites da NBR 6118" if ajustes else "") + ".")
        self._editado(resumo)
        for tit, avs in r["avisos"].items():
            for a in avs:
                self.msg(f"{tit}: {a}", "aviso")
        for tit, mud in ajustes.items():
            self.msg(f"{tit}: ajustado à NBR 6118: {'; '.join(mud)}", "ok")
        for tit, txt in colapsos.items():
            self.msg(f"{tit}: colapso sugerido: {'; '.join(txt)}", "ok")
        self.status(resumo, "ok")

    def sugerir_colapso(self, todos=False):
        """Colapso do pilar atual (ou de todos): nº de barras por face pelas cargas do TQS, com a bitola atual, e
        comprimento além da face pela ancoragem além de C'' (colapso.sugerir)."""
        alvo = range(len(self.projeto["pilares"])) if todos else [self.i]
        linhas, n = [], 0
        for j in alvo:
            par = self.projeto["pilares"][j]
            res = detalhar(par)
            tit = res["p"]["titulo"]
            if res["erros"]:
                linhas.append((tit, "não sugerido: " + "; ".join(res["erros"]), "erro"))
                continue
            mud, txt = ncol.sugerir(res)
            mud = {k: v for k, v in mud.items() if res["p"].get(k) != v}
            par.update(mud)
            n += bool(mud)
            linhas.append((tit, "; ".join(txt) + ("" if mud else " (sem mudança)"), "ok"))
        if n:
            self.modificado = True
        self._carregar_pilar()                     # refaz a prévia e as mensagens; a sugestão vem depois
        for tit, txt, nivel in linhas:
            self.msg(f"{tit}: colapso sugerido: {txt}", nivel)
        self.status(f"Colapso sugerido: {n} pilar(es) alterado(s) de {len(linhas)}.", "ok")

    def colar(self):
        try:
            texto = self.clipboard_get()
        except tk.TclError:
            texto = ""
        novos = DlgColar(self, texto).mostrar()
        if not novos:
            return
        for q in mesclar_colagem(self.pilar, novos):
            q["titulo"] = self._titulo_livre(str(q["titulo"]))
            self.projeto["pilares"].append(q)
        self._editado(f"{len(novos)} pilar(es) colado(s) do Excel.")
        self.ir(len(self.projeto["pilares"]) - len(novos))

    def _editado(self, s):
        self.modificado = True
        self._titulo()
        self.msg(s, "info")

    # ================================================================== arquivos
    def _confirmar_descartar(self):
        if not self.modificado:
            return True
        r = messagebox.askyesnocancel(APP, "Salvar as alterações do projeto?", parent=self)
        if r is None:
            return False
        if r:
            return self.salvar()
        return True

    def novo(self):
        if not self._confirmar_descartar():
            return
        self.projeto = novo_projeto([dict(NOVO_PILAR)])
        self.arq, self.i, self.modificado, self.arquivos = None, 0, False, {}
        self.gerados, self.arq_relatorio = {}, None
        self.pasta.set("")
        self._limpar_msgs()
        self._carregar_pilar(enquadrar=True)

    def abrir(self, arquivo=None):
        if not self._confirmar_descartar():
            return
        arquivo = arquivo or filedialog.askopenfilename(
            parent=self, title="Abrir projeto", initialdir=os.path.join(RAIZ, "exemplos"),
            filetypes=[("Projeto de punção", "*.json"), ("Todos", "*.*")])
        if not arquivo:
            return
        try:
            proj = ler_projeto(arquivo)
            if not proj["pilares"]:
                raise ValueError("o projeto não tem pilares")
        except Exception as e:
            messagebox.showerror(APP, f"Não foi possível abrir {arquivo}:\n{e}", parent=self)
            return
        self.projeto, self.arq, self.i, self.modificado, self.arquivos = proj, os.path.abspath(arquivo), 0, False, {}
        self.gerados, self.arq_relatorio = {}, None
        self.pasta.set(proj.get("pasta_saida", ""))
        self._limpar_msgs()
        self._carregar_pilar(enquadrar=True)
        self.msg(f"Projeto aberto: {self.arq} ({len(proj['pilares'])} pilar(es)).", "cinza")

    def _gravar(self, arq):
        proj = dict(self.projeto, formato=FORMATO, versao=VERSAO)
        if self.pasta.get().strip():
            proj["pasta_saida"] = self.pasta.get().strip()
        else:
            proj.pop("pasta_saida", None)
        pathlib.Path(arq).write_text(json.dumps(proj, ensure_ascii=False, indent=1), encoding="utf-8")
        self.arq, self.modificado = os.path.abspath(arq), False
        self._titulo()
        self._arvore()
        self.status(f"Salvo: {self.arq}", "ok")
        return True

    def salvar(self):
        return self._gravar(self.arq) if self.arq else self.salvar_como()

    def salvar_como(self):
        arq = filedialog.asksaveasfilename(parent=self, title="Salvar projeto", defaultextension=".json",
                                           initialdir=os.path.dirname(self.arq) if self.arq else RAIZ,
                                           initialfile=f"{self._nome_projeto()}.json",
                                           filetypes=[("Projeto de punção", "*.json")])
        return self._gravar(arq) if arq else False

    def sair(self):
        if self._confirmar_descartar():
            self.destroy()

    def destroy(self):
        """Cancela os after() pendentes (enquadrar, fila, atualização), que disparariam com a janela já fechada."""
        try:
            jobs = self.tk.splitlist(self.tk.call("after", "info"))
        except tk.TclError:
            jobs = ()
        for job in jobs:                     # direto no Tcl: o after_cancel do Python falha em comandos já apagados
            try:
                self.tk.call("after", "cancel", job)
            except tk.TclError:
                pass
        super().destroy()

    # ================================================================== saídas (TQS, numa thread)
    def _pasta_saida(self):
        return self.pasta.get().strip() or os.path.join(RAIZ, "saidas", self._nome_projeto())

    def escolher_pasta(self):
        d = filedialog.askdirectory(parent=self, title="Pasta dos DWG", initialdir=self._pasta_saida())
        if d:
            self.pasta.set(d)
            self.modificado = True
            self._titulo()

    def _trabalho(self, texto, func, depois):
        if self.ocupado:
            self.status("Aguarde: há uma gravação em andamento.", "aviso")
            return
        self.ocupado = True
        self.status(texto)
        self.pb.pack(side="right", padx=6)
        self.pb.start(12)
        self.configure(cursor="watch")

        def rodar():
            try:
                self.fila.put((depois, func(), None))
            except Exception:
                self.fila.put((depois, None, traceback.format_exc()))
        threading.Thread(target=rodar, daemon=True).start()

    def _processar_fila(self):
        try:
            while True:
                depois, r, erro = self.fila.get_nowait()
                self.ocupado = False
                self.pb.stop()
                self.pb.pack_forget()
                self.configure(cursor="")
                if erro:
                    self.msg(erro.strip().splitlines()[-1], "erro")
                    self.msg(erro, "cinza")
                    self.status("Erro na gravação (veja as mensagens).", "erro")
                else:
                    depois(r)
        except queue.Empty:
            pass
        self.after(80, self._processar_fila)

    def _gerar_pilares(self, pilares, pasta, pdf, dxf):
        from dwg_tqs import prancha                     # só aqui: precisa do TQS
        out = []
        for par in pilares:
            res = detalhar(par)
            if res["erros"]:
                out.append((res["p"]["titulo"], None, res["erros"]))
                continue
            g = prancha.gerar(res, pasta, pdf=pdf, dxf=dxf)
            out.append((res["p"]["titulo"], g, None))
        return out

    def _gerados(self, saida):
        for titulo, g, erros in saida:
            if erros:
                self.msg(f"{titulo}: não gravado ({'; '.join(erros)})", "erro")
                continue
            self.arquivos[titulo] = g["arquivos"]
            self.gerados[titulo] = g
            nomes = ", ".join(os.path.basename(v) for k, v in g["arquivos"].items() if k != "aviso")
            self.msg(f"{titulo}: {nomes}", "ok")
            if g["arquivos"].get("aviso"):
                self.msg(f"{titulo}: {g['arquivos']['aviso']}", "aviso")
            self.msg(f"   ferros pelo TQS: {g['tabela_tqs']} -> " +
                     ("confere com o núcleo" if g["confere"] else f"DIFERE do núcleo {g['esperado']}"),
                     "ok" if g["confere"] else "erro")
        ok = sum(1 for _, g, e in saida if g)
        self.status(f"Gravado(s) {ok} de {len(saida)} pilar(es) em {self._pasta_saida()}.", "ok" if ok == len(saida) else "aviso")

    def _pode_gerar(self):
        try:
            import TQS  # noqa: F401
        except ImportError:
            messagebox.showerror(APP, "A gravação precisa do TQS (TQSPythonInterface). A prévia funciona sem ele.",
                                 parent=self)
            return False
        return True

    def gerar(self):
        if not self._pode_gerar():
            return
        if self.res and self.res["erros"]:
            messagebox.showerror(APP, "Corrija os erros do pilar antes de gerar.", parent=self)
            return
        # As variáveis do Tk só podem ser lidas na thread principal: tudo o que a thread usa é lido aqui.
        pilares, pasta, pdf, dxf = [copy.deepcopy(self.pilar)], self._pasta_saida(), self.pdf.get(), self.dxf.get()
        self._trabalho(f"Gravando {self._efetivo()['titulo']} pelo TQS...",
                       lambda: self._gerar_pilares(pilares, pasta, pdf, dxf), self._gerados)

    def gerar_lote(self):
        if not self._pode_gerar():
            return
        n = len(self.projeto["pilares"])
        pilares, pasta, pdf, dxf = (copy.deepcopy(self.projeto["pilares"]), self._pasta_saida(), self.pdf.get(),
                                    self.dxf.get())
        self._trabalho(f"Gravando o lote ({n} pilares) pelo TQS...",
                       lambda: self._gerar_pilares(pilares, pasta, pdf, dxf), self._lote_gerado)

    def _lote_gerado(self, saida):
        self._gerados(saida)
        self.relatorio_lote(abrir=False)

    def relatorio_lote(self, abrir=True):
        """Relatório do lote (TXT e CSV) na pasta de saída. Usa os comprimentos do TQS dos pilares gravados nesta
        sessão e sem mudança desde então; nos outros, os do núcleo."""
        itens = []
        for par in self.projeto["pilares"]:
            res = detalhar(par)
            g = self.gerados.get(res["p"]["titulo"])
            if g and not res["erros"]:
                esperado = sorted((f["pos"], f["quant"], round(f["bitola"], 1), f["comp"]) for f in res["ferros"])
                if esperado != g["esperado"]:
                    g = None                            # o pilar mudou depois da gravação
            itens.append(rel_lote.item(res, g if not res["erros"] else None))
        nome = self._nome_projeto()
        r = rel_lote.montar(itens, projeto=nome, arquivo=self.arq)
        try:
            arqs = rel_lote.gravar(r, self._pasta_saida(), nome)
        except OSError as e:
            self.msg(f"Relatório não gravado: {e}", "erro")
            self.status("Relatório não gravado (o arquivo está aberto em outro programa?).", "erro")
            return None
        self.arq_relatorio = arqs
        fonte = (f"comprimentos do TQS em {r['n_tqs']} de {r['n']} pilar(es)" if r["n_tqs"]
                 else "comprimentos do núcleo")
        self.msg(f"Relatório do lote: {', '.join(os.path.basename(v) for v in arqs.values())} ({fonte}; "
                 f"{len(r['avisos'])} aviso(s), {len(r['erros'])} erro(s)) em {self._pasta_saida()}", "ok")
        self.status(f"Relatório do lote gravado em {self._pasta_saida()}.", "ok")
        if abrir:
            os.startfile(arqs["txt"])
        return arqs

    def abrir_saida(self, tipo):
        if tipo == "pasta":
            pasta = self._pasta_saida()
            if os.path.isdir(pasta):
                os.startfile(pasta)
            else:
                self.status("A pasta de saída ainda não existe (gere o pilar).", "aviso")
            return
        if tipo == "relatorio":
            if self.arq_relatorio and os.path.exists(self.arq_relatorio["txt"]):
                os.startfile(self.arq_relatorio["txt"])
            else:
                self.status("Grave o relatório antes (Lote > Relatório do lote).", "aviso")
            return
        arqs = self.arquivos.get(self._efetivo()["titulo"], {})
        if arqs.get(tipo) and os.path.exists(arqs[tipo]):
            os.startfile(arqs[tipo])
        else:
            self.status("Gere o pilar antes (Ctrl+G).", "aviso")

    # ================================================================== ajuda e erros
    def ajuda(self):
        messagebox.showinfo(APP, "Atalhos\n\nCtrl+N / Ctrl+O / Ctrl+S: novo, abrir, salvar\nCtrl+G: gerar o pilar "
                                 "(DWG, PDF, DXF)\nCtrl+Shift+G: gerar o lote\nF5: atualizar a prévia\nHome: enquadrar\n"
                                 "PgUp / PgDn: pilar anterior / seguinte\n\nNa área de desenho: roda = zoom, botão do "
                                 "meio ou direito = deslocar, duplo clique no meio = enquadrar, clique = selecionar "
                                 "(um ferro aparece nas propriedades), botão direito parado = menu.", parent=self)

    def report_callback_exception(self, exc, val, tb):
        texto = "".join(traceback.format_exception(exc, val, tb))
        try:
            self.msg(f"Erro: {val}", "erro")
            self.msg(texto, "cinza")
            pasta = os.path.join(RAIZ, "saidas")
            os.makedirs(pasta, exist_ok=True)
            with open(os.path.join(pasta, "erros_janela.log"), "a", encoding="utf-8") as f:
                f.write(texto + "\n")
        except Exception:
            pass
        messagebox.showerror(APP, f"Erro: {val}\n(detalhes nas mensagens e em saidas\\erros_janela.log)", parent=self)


def main(arquivo=None):
    App(arquivo).mainloop()
