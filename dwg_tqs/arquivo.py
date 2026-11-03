# -*- coding: utf-8 -*-
"""
Desenho novo no padrão dos modelos e gravação em DWG, PDF e DXF.

- novo_desenho: DWG 9/13 ("TQS AGC2 - Desenho de armação", tabela TABPLTA), escala dada, cotas configuradas como as
  dos desenhos de referência (texto no 221; linha, chamadas e símbolo DOT no 253; PADRAO_desenho.md, seção 5).
- salvar: cópia do DWG anterior em <pasta>/anteriores, DWG, PDF (diretório atual na pasta do desenho; revisão
  levada para o fim do nome) e DXF (tabela LTYPE corrigida e, se pedido, cores da plotagem).

Funções de DXF e PDF copiadas de _apps/EstacaEscavada/estaca_dwg.py (_dxf_continuo, _dxf_com_cores, paleta ACI) e
de _apps/TelaSoldada/tela_dwg.py (_pdf_nome) em 03/11/2026; as cores da plotagem vêm de nucleo/niveis.json, sem
ler o C:\\TQSW.
"""
import colorsys
import glob
import json
import os
import re
import shutil
from datetime import datetime

from TQS import TQSDwg

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cotas dos modelos (conferido em 03/11/2026 contra os objetos IPOCOT do PUN_P02): com dimtsz = 0,2114 o símbolo
# DOT sai com os círculos de r = 0,528 e 0,264 da referência (o raio é 2,4973 x dimtsz, na escala 15).
COTA = dict(idmniv=221, idmnic=253, idmnil=253, idmnib=253, dimblk="DOT", dimtxt=0.18, dimexo=0.10,
            dimexe=0.10, dimdle=0.15, dimtsz=0.2114)
# Nível do objeto dos ferros inteligentes nos modelos. O objeto fica no nível atual do desenho na hora da criação, e
# o editor desenha o ferro na cor desse nível: fixe dwg.draw.level = NV_OBJETO_FERRO antes de cada SmartRebar.
NV_OBJETO_FERRO = 220


def novo_desenho(escala=15.0, cota=None):
    dwg = TQSDwg.Dwg()
    dwg.file.New()
    s = dwg.settings
    s.systemId, s.subSystemId, s.scale = TQSDwg.IEDTAB, 13, float(escala)
    dwg.file.LoadColors()
    configurar_cotas(dwg, **(cota or {}))
    return dwg


def configurar_cotas(dwg, **muda):
    dm = dwg.dim
    for k, v in {**COTA, **muda}.items():
        setattr(dm, k, v)


# --------------------------------------------------------------------------- DXF
def _paleta_aci():
    """Cores RGB da paleta padrão do AutoCAD (índices 1 a 255), a mesma da tela do TQS."""
    pal = {1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 255, 255), 5: (0, 0, 255), 6: (255, 0, 255),
           7: (255, 255, 255), 8: (128, 128, 128), 9: (192, 192, 192)}
    brilho = (255, 204, 153, 127, 76)
    for i in range(10, 250):
        h, k = (i - 10) // 10 * 15 / 360.0, i % 10
        v, s = brilho[k // 2] / 255.0, (1.0 if k % 2 == 0 else 0.5)
        pal[i] = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
    for i, g in zip(range(250, 256), (51, 91, 132, 173, 214, 255)):
        pal[i] = (g, g, g)
    return pal


def _aci_mais_proxima(rgb, pal=_paleta_aci()):
    if max(rgb) < 40:                            # preto: a cor 7, que sai preta no papel
        return 7
    return min((i for i in pal if i != 7), key=lambda i: sum((a - b) ** 2 for a, b in zip(pal[i], rgb)))


def cores_plotagem():
    """Cor ACI de cada nível pela pena da TABPLTA (nucleo/niveis.json)."""
    niv = json.load(open(os.path.join(RAIZ, "nucleo", "niveis.json"), encoding="utf-8"))["niveis"]
    out = {}
    for n, v in niv.items():
        c = v["cor_plot"]
        rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
        out[int(n)] = 7 if rgb == (255, 255, 255) else _aci_mais_proxima(rgb)
    return out


def dxf_com_cores(arq, cores):
    """Cor de cada camada (nível) pela pena da plotagem; nas entidades com cor própria igual à cor original da
    camada, a mesma troca. As cores especiais (ferros por bitola) ficam como o TQS gravou."""
    lin = open(arq, encoding="latin-1", newline="").read().split("\n")
    eol = "\r" if lin and lin[0].endswith("\r") else ""
    val = lambda j: lin[j].rstrip("\r").strip()
    em_layer, nome, camada = False, None, None
    cor_orig, n_trocas = {}, 0
    for j in range(0, len(lin) - 1, 2):
        cod, v = val(j), val(j + 1)
        if cod == "0":
            em_layer, nome, camada = v == "LAYER", None, None
        elif cod == "2" and em_layer:
            nome = v
        elif cod == "8":
            camada = v
        elif cod == "62":
            nv = nome if em_layer else camada
            if nv is None or not nv.isdigit() or int(nv) not in cores or v in ("0", "256"):
                continue
            if em_layer:
                cor_orig[nv] = abs(int(v))
            elif abs(int(v)) != cor_orig.get(nv):
                continue
            sinal = -1 if v.startswith("-") else 1
            lin[j + 1] = f"{sinal * cores[int(nv)]:6d}" + eol
            n_trocas += 1
    open(arq, "w", encoding="latin-1", newline="").write("\n".join(lin))
    return n_trocas


def dxf_continuo(arq):
    """O "Salvar como DXF" do TQS grava duas entradas CONTINUOUS na tabela LTYPE (a 2ª tracejada), e os leitores que
    ficam com a última desenham tudo tracejado. Tira as repetidas e mantém a primeira."""
    lin = open(arq, encoding="latin-1", newline="").read().split("\n")
    val = lambda j: lin[j].rstrip("\r").strip()
    tabela, entradas, ini = None, [], None
    for j in range(0, len(lin) - 1, 2):
        cod, v = val(j), val(j + 1)
        if cod == "0":
            if ini is not None:
                entradas[-1][1] = j
                ini = None
            if v == "TABLE":
                tabela = ""
            elif v == "ENDTAB":
                tabela = None
            elif tabela == "LTYPE" and v == "LTYPE":
                ini = j
                entradas.append([j, None, None])
        elif cod == "2" and tabela == "":
            tabela = v
        elif cod == "2" and ini is not None and entradas[-1][2] is None:
            entradas[-1][2] = v.upper()
    tirar = [(a, b) for a, b, nome in entradas if nome == "CONTINUOUS" and b is not None][1:]
    for a, b in reversed(tirar):
        del lin[a:b]
    if tirar:
        open(arq, "w", encoding="latin-1", newline="").write("\n".join(lin))
    return len(tirar)


# --------------------------------------------------------------------------- PDF
def _pdf_nome(arq):
    """O TQS põe a revisão ("-R00") no 23º caractere de nomes longos; leva a revisão para o fim do nome."""
    d, n = os.path.split(arq)
    st, ext = os.path.splitext(n)
    m = re.search(r"-R\d{2}", st)
    if not m or m.end() == len(st):
        return arq
    dest = os.path.join(d, st[:m.start()] + st[m.end():] + m.group(0) + ext)
    try:
        os.replace(arq, dest)
        return dest
    except OSError:
        return arq


# --------------------------------------------------------------------------- gravação
def salvar(dwg, pasta, nome, pdf=True, dxf=True, dxf_plotagem=True):
    """Grava <pasta>/<nome>.DWG (com cópia do anterior em <pasta>/anteriores), PDF e DXF. Devolve os caminhos."""
    pasta = os.path.abspath(pasta)
    os.makedirs(pasta, exist_ok=True)
    base = os.path.join(pasta, nome)
    if os.path.exists(base + ".DWG"):            # o usuário pode ter editado o desenho no TQS
        ant = os.path.join(pasta, "anteriores")
        os.makedirs(ant, exist_ok=True)
        shutil.copy2(base + ".DWG", os.path.join(ant, f"{nome}_{datetime.now():%Y%m%d_%H%M%S}.DWG"))
    arquivos = {"dwg": base + ".DWG"}
    cwd = os.getcwd()
    os.chdir(pasta)                              # a plotagem em PDF procura o desenho na pasta atual
    try:
        dwg.file.SaveAs(base + ".DWG")
        if pdf:
            antes = set(glob.glob(os.path.join(pasta, "*.PDF")))
            t0 = datetime.now().timestamp()
            dwg.file.SaveAs(base + ".PDF")       # o TQS grava <nome>-R00.PDF
            novos = [p for p in glob.glob(os.path.join(pasta, "*.PDF"))
                     if p not in antes or os.path.getmtime(p) >= t0 - 1]
            if novos:
                arquivos["pdf"] = _pdf_nome(max(novos, key=os.path.getmtime))
        if dxf:
            dwg.file.SaveAs(base + ".DXF")
            if os.path.exists(base + ".DXF"):
                dxf_continuo(base + ".DXF")
                if dxf_plotagem:
                    dxf_com_cores(base + ".DXF", cores_plotagem())
                arquivos["dxf"] = base + ".DXF"
    finally:
        os.chdir(cwd)
    return arquivos
