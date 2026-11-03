# -*- coding: utf-8 -*-
"""
Despeja um DWG-TQS em JSON: informações do desenho, tabela de níveis, entidades (com o bloco em que estão),
ferros inteligentes (atributos, tabela, inserções, pontos do ferro genérico) e cotas. Só leitura: o desenho é
copiado para uma pasta temporária e a cópia é que é aberta (abrir pelo TQS pode gravar arquivos de trabalho).
O desenho é aberto sem o CarregarCores() do File.Open (dwg_tqs.arquivo.abrir_sem_cores): a tabela de níveis e as
cores das entidades são as gravadas no arquivo, as que o editor do TQS mostra.

Uso:  python ferramentas/ler_modelo.py <desenho.DWG> [<outro.DWG> ...] [--saida PASTA]
Grava <PASTA>/<desenho>.json (padrão: saidas/modelos) e imprime um resumo por nível.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

ATRIB_FERRO = ("type", "mark", "quantity", "multiplier", "diameter", "spacing", "cover", "comment", "ribbed",
               "leftHook", "rightHook", "bendType", "bendRadius", "bendTotalLengthMode", "bendBendLengthMode",
               "bendRadiusDisplay", "bendDimRadius",
               "bendDimPerimeter", "bendTickDisplay", "textHeigth", "distributionTextHeigth",
               "straightBarMainLength", "straightBarLeftLength", "straightBarRightLength", "straightBarZone",
               "straightBarBendType", "straightBarTextDirection", "straightBarTextPosition",
               "straightBarContinuous", "mirrorMode", "alternatingMode", "leaderLine", "leaderLineDistance",
               "stirrupType", "circularStirrupRadius")


def _valor(v):
    return v if isinstance(v, (int, float, str)) or v is None else str(v)


def ferro(rb):
    """Atributos e geometria de um ferro inteligente (IPOFER)."""
    d = {}
    for k in ATRIB_FERRO:
        try:
            d[k] = _valor(getattr(rb, k))
        except Exception as ex:                       # atributo que não se aplica ao tipo do ferro
            d[k] = "ERRO " + type(ex).__name__
    d["tabela"] = [list(rb.RebarScheduleInfo(i)) for i in range(rb.RebarScheduleNumDescr())]
    d["insercoes"] = []
    for i in range(rb.GetInsertionNumber()):
        (x, y, ang, esc, ident, idobra, ipatas, explode, nivel, estilo, cor) = rb.GetInsertionData(i)[:11]
        npts = rb.GetInsertionPoints(i)[0]
        d["insercoes"].append(dict(x=x, y=y, ang=ang, esc=esc, ident=ident, idobra=idobra, ipatas=ipatas,
                                   explode=explode, nivel=nivel, estilo=estilo, cor=cor,
                                   pts=[list(rb.GetInsertionPoint(i, j)[:2]) for j in range(npts)]))
    d["pontos_gen"] = [list(rb.GetGenRebarPoint(i)) for i in range(rb.GetGenRebarPoints())]
    d["faixas"] = [list(rb.GetRebarDistrInfo(i)) for i in range(rb.GetRebarDistrNum())]
    return d


def ler(arq):
    """Lê o DWG (uma cópia) e devolve o dicionário do despejo."""
    from TQS import TQSDwg as T                       # só aqui: o resto da ferramenta roda sem o TQS
    from dwg_tqs.arquivo import abrir_sem_cores
    tmp = tempfile.mkdtemp(prefix="pun_ler_")
    copia = os.path.join(tmp, os.path.basename(arq))
    shutil.copy2(arq, copia)
    cwd = os.getcwd()
    try:
        os.chdir(tmp)
        dwg = T.Dwg()
        abrir_sem_cores(dwg, copia)
        dwg.settings.levelsReadMode = 0               # lê também os níveis desligados
        info = {"arquivo": os.path.basename(arq)}
        for k in ("systemId", "subSystemId", "rebarDrawing"):
            info[k] = getattr(dwg.settings, k, None)
        info["escala"] = getattr(dwg.settings, "scale", None)
        try:
            info["limites"] = list(dwg.limits.DwgLimits())
        except Exception:
            info["limites"] = None
        lt = T.LevelsTable(dwg)
        niveis = {}
        for n in range(256):                          # nível como texto: com número, a interface muda o nível atual
            niveis[n] = dict(cor=lt.GetColor(str(n)), estilo=lt.GetStyle(str(n)), ligado=lt.IsOn(str(n)))
        ents, pilha = [], []
        it = dwg.iterator
        it.Begin()
        while True:
            t = it.Next()
            if t == T.DWGTYPE_EOF:
                break
            e = {"t": it.elementName, "n": it.level, "c": it.color, "s": it.style}
            if t not in (T.DWGTYPE_BLOCKEND, T.DWGTYPE_OBJECTEND):
                rgb = it.colorRGB
                if rgb:                                   # cor RGB própria da entidade (0 = não tem)
                    e["rgb"] = rgb
                if it.hasPlotData:                        # pena, peso e estilo de plotagem próprios
                    e["plot"] = [it.plotPen, it.plotWeight, it.plotStyle]
            if t == T.DWGTYPE_LINE:
                e["xy"] = it.xy
            elif t == T.DWGTYPE_TEXT:
                e.update(x=it.x1, y=it.y1, h=it.textHeight, a=it.textAngle, txt=it.text)
            elif t in (T.DWGTYPE_POLYLINE, T.DWGTYPE_CURVE):
                e["xy"] = it.xy
                if t == T.DWGTYPE_POLYLINE:
                    e["fill"] = it.isFilled
            elif t == T.DWGTYPE_CIRCLE:
                e.update(x=it.xc, y=it.yc, r=it.radius)
            elif t == T.DWGTYPE_ARC:
                e.update(x=it.xc, y=it.yc, r=it.radius, a1=it.startAngle, a2=it.endAngle)
            elif t == T.DWGTYPE_BLOCK:
                e.update(b=it.blockName, x=it.x1, y=it.y1, sx=it.xScale, sy=it.yScale, ang=it.insertAngle)
            elif t == T.DWGTYPE_OBJECT:
                e["obj"] = it.objectName
                if it.objectName == "IPOFER" and it.smartRebar is not None:
                    e["ferro"] = ferro(it.smartRebar)
            if pilha and t not in (T.DWGTYPE_BLOCKEND,):
                e["dentro"] = pilha[-1]
            if t == T.DWGTYPE_BLOCK:
                pilha.append(it.blockName)
            elif t == T.DWGTYPE_BLOCKEND and pilha:
                pilha.pop()
            elif t == T.DWGTYPE_OBJECT:
                pilha.append("<" + it.objectName + ">")
            elif t == T.DWGTYPE_OBJECTEND and pilha:
                pilha.pop()
            ents.append(e)
        dwg.file.Close()
    finally:
        os.chdir(cwd)
        shutil.rmtree(tmp, ignore_errors=True)
    return {"info": info, "niveis": niveis, "ents": ents}


def resumo(d):
    ents = d["ents"]
    linhas = [f"{d['info']}", f"  entidades: {len(ents)}  {dict(Counter(e['t'] for e in ents))}"]
    por = {}
    for e in ents:
        por.setdefault(e["n"], Counter())[e["t"]] += 1
    for n in sorted(por, key=lambda v: (isinstance(v, str), v)):
        nv = d["niveis"].get(n, {})
        linhas.append(f"  nível {n:>3}  cor {nv.get('cor', '?'):>3} estilo {nv.get('estilo', '?'):>2}  {dict(por[n])}")
    linhas.append("  blocos: " + str(dict(Counter(e["b"] for e in ents if "b" in e))))
    for e in ents:
        if "ferro" in e:
            f = e["ferro"]
            tab = f["tabela"][0] if f["tabela"] else []
            linhas.append(f"  ferro N{f['mark']}: tipo {f['type']}, {f['quantity']} {f['diameter']} "
                          f"C={tab[8] if tab else '?'}, inserções nos níveis {[i['nivel'] for i in f['insercoes']]}")
    return "\n".join(linhas)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dwg", nargs="+")
    ap.add_argument("--saida", default=os.path.join(RAIZ, "saidas", "modelos"))
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    for arq in a.dwg:
        d = ler(os.path.abspath(arq))
        nome = os.path.splitext(os.path.basename(arq))[0]
        with open(os.path.join(a.saida, nome + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, default=str)
        print(f"== {nome}\n{resumo(d)}")


if __name__ == "__main__":
    main()
