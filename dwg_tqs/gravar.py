# -*- coding: utf-8 -*-
"""
Transcreve uma folha de primitivas (nucleo/folha.py) para um DWG-TQS: blocos, linhas, polilinhas, círculos, arcos,
textos, cotas (IPOCOT) e ferros inteligentes (IPOFER). Devolve os ferros criados, para ler os comprimentos que o
TQS calcula.
"""
import math

from TQS import TQSDwg as T

from . import arquivo
from nucleo.textos import txt_tqs


def _atributos(d, p):
    d.level = p["n"]
    d.style = -1 if p.get("s") is None else p["s"]
    d.color = -1 if p.get("c") is None else p["c"]


def _primitiva(dwg, p):
    d = dwg.draw
    t = p["t"]
    if t in ("Linha", "Polyline", "Circulo", "Arco", "Texto"):
        _atributos(d, p)
    if t == "Linha":
        (x1, y1), (x2, y2) = p["xy"]
        d.Line(x1, y1, x2, y2)
    elif t == "Polyline":
        d.PolyEnterXY([list(v) for v in p["xy"]])
        d.PolylineFilled() if p.get("fill") else d.Polyline()
    elif t == "Circulo":
        d.Circle(p["x"], p["y"], p["r"])
    elif t == "Arco":
        d.Arc(p["x"], p["y"], p["r"], p["a1"], p["a2"])
    elif t == "Texto":
        if p["txt"].strip():
            d.Text(p["x"], p["y"], p["h"], p["a"], txt_tqs(p["txt"]))
    elif t == "Bloco":
        d.level, d.style, d.color = p["n"], -1, -1
        d.BlockInsert(p["b"], p["x"], p["y"], p["sx"], p["sy"], p["ang"])
    d.style, d.color = -1, -1


def _cota(dwg, p):
    nt, nl = p["niveis"]
    arquivo.configurar_cotas(dwg, idmniv=nt, idmnic=nl, idmnil=nl, idmnib=nl)
    dm = dwg.dim
    dm.dimlfc = p.get("fator", 1.0)
    if p.get("txt") is not None:
        dm.dimtxu = txt_tqs(p["txt"]) if p["txt"] else " "
    (x1, y1), (x2, y2), (x3, y3) = p["p1"], p["p2"], p["p3"]
    modo = p["modo"]
    if modo == "h":
        dm.DimHorizontal(x1, y1, x2, y2, x3, y3)
    elif modo == "v":
        dm.DimVertical(x1, y1, x2, y2, x3, y3)
    elif modo == "a":
        dm.DimAligned(x1, y1, x2, y2, x3, y3)
    else:
        dm.DimInclined(x1, y1, x2, y2, x3, y3, p["ang"])
    dm.dimlfc = 1.0


# Atributos dos ferros pelo desenho de referência PUN_P02-R01 (PADRAO_desenho.md, seção 6 e 10)
ATRIB_GEN = dict(bendTotalLengthMode=2, bendBendLengthMode=2, bendRadiusDisplay=0, bendDimRadius=1,
                 bendDimPerimeter=1, bendTickDisplay=0, textHeigth=0.2, straightBarTextPosition=2,
                 straightBarTextDirection=0)
ATRIB_RETO = dict(bendDimRadius=1, bendDimPerimeter=1, bendTickDisplay=0, textHeigth=0.2,
                  straightBarTextPosition=2, straightBarTextDirection=0)


def _ferro(dwg, f):
    dwg.draw.level = arquivo.NV_OBJETO_FERRO        # o editor desenha o ferro na cor do nível do objeto
    r = T.SmartRebar(dwg)
    gen = f["tipo"] == "gen"
    r.type = T.ICPFGN if gen else T.ICPFRT
    r.mark, r.quantity, r.multiplier = f["mark"], f["quant"], 1
    r.diameter, r.spacing, r.cover = f["bitola"], 0.0, f.get("cobrimento", 3.0)
    r.leftHook = r.rightHook = T.ICPSGA
    if not gen:
        r.straightBarMainLength = f["comp"]
        r.straightBarZone = f.get("zona", T.ICPPOS)
    for k, v in {**(ATRIB_GEN if gen else ATRIB_RETO), **f.get("atributos", {})}.items():
        setattr(r, k, v)
    for j, i in enumerate(f["ins"]):
        r.RebarLine(i["x"], i["y"], i.get("ang", 0.0), i.get("esc", 1.0), i.get("ident", 1), i.get("idobra", 1),
                    i.get("ipatas", 1 if not gen else 0), 0, i["nivel"], -1, -1)
        if gen and j == 0:
            for x, y in f["pontos"]:
                r.GenRebarPoint(x, y, 0.0, 0, 1, -1)
    r.leaderLine = 0
    if f.get("texto"):
        tx = f["texto"]
        r.RebarTextDisplayPosition(tx["x"], tx["y"], tx.get("h", 0.2), tx.get("ang", 0.0), 0,
                                   T.ICPCENTR_ESQUERD, T.ICPQUEBR_SEMQUEBRA)
    return r


def desenhar(dwg, folha):
    """Grava a folha no desenho aberto. Devolve [(SmartRebar, spec)]."""
    for nome, prims in folha.blocos.items():
        if prims is None:                            # bloco da biblioteca do TQS
            dwg.draw.BlockLoadFromDwg(nome)
            continue
        dwg.draw.BlockOpen(nome, 0.0, 0.0)
        for p in prims:
            _primitiva(dwg, p)
        dwg.draw.BlockClose()
    arquivo.aplicar_tabela_niveis(dwg)               # o BlockLoadFromDwg volta a tabela de níveis à padrão
    ferros = []
    for p in folha.prims:
        if p["t"] == "Cota":
            _cota(dwg, p)
        elif p["t"] == "Ferro":
            ferros.append((_ferro(dwg, p), p))
        else:
            _primitiva(dwg, p)
    arquivo.configurar_cotas(dwg)
    return ferros


def tabela(ferros):
    """Ferros como o TQS calculou: [(posição, quantidade, bitola, comprimento)]."""
    out = []
    for r, _ in ferros:
        for i in range(r.RebarScheduleNumDescr()):
            info = r.RebarScheduleInfo(i)
            out.append((info[0], info[2], round(info[1], 1), round(info[8])))
    return sorted(out)
