# -*- coding: utf-8 -*-
"""
Grava nucleo/niveis.json com os atributos de cada nível (0 a 255) do desenho de armação 9/13 do TQS, para a prévia
e o DXF ficarem iguais em qualquer máquina, sem ler o C:\\TQSW em tempo de uso:

- plotagem (TABPLTA.DAT + TABPLTA.MSG + PENAS\\PLOTPENA.PEN): título, pena, cor e espessura da pena, estilo e hachura;
- tela (cor_tela, estilo_tela): a tabela de níveis gravada num desenho de referência (--modelo), lida sem o
  CarregarCores() da interface; é a que o app grava nos desenhos (os modelos têm cores próprias em 34 níveis);
- tela padrão (cor_tela_9_13, estilo_tela_9_13): a de um DWG 9/13 novo, criado só na memória, para comparação.

Formato da TABPLTA (lido em 13/10/2026 no projeto principal): seções PENAS, PESOS, ESTILOS e HACHURAS com 256
caracteres em 3 linhas (80 + 80 + 96), um por nível; "0"-"9" = 0-9 e depois chr(55 + n). Pena n do arquivo = pena
n + 1 na janela do TQS. Hachura h (h > 0) = coluna h - 1 de "HACHURAS EM PLOTTER RASTER" (tipo; ângulo; parâmetro).
A PLOTPENA.PEN tem o nº de penas e, por pena, a cor 0x00BBGGRR e a espessura em mm.

Uso:  python ferramentas/extrair_penas.py [--suporte C:\\TQSW\\SUPORTE\\NGE]
"""
import argparse
import colorsys
import json
import os
import pathlib
import sys
from datetime import date

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SAIDA = os.path.join(RAIZ, "nucleo", "niveis.json")


def _indice(c):
    return int(c) if c.isdigit() else ord(c) - 55


def _secao(linhas, nome):
    i = next(k for k, l in enumerate(linhas) if l.strip().upper().startswith(nome))
    return (linhas[i + 1] + linhas[i + 2] + linhas[i + 3])[:256]


def ler_tabplt(base):
    linhas = open(os.path.join(base, "TABPLT", "TABPLTA.DAT"), "rb").read().decode("cp1252").splitlines()
    pen, est, hac = (_secao(linhas, s) for s in ("PENAS", "ESTILOS", "HACHURAS"))
    i = next(k for k, l in enumerate(linhas) if l.strip().upper() == "HACHURAS EM PLOTTER RASTER")
    tipos, angs, pars = ([float(v) for v in linhas[i + j].split()] for j in (1, 2, 3))
    hachuras = {h + 1: dict(tipo=int(tipos[h]), angulo=angs[h], parametro=pars[h]) for h in range(len(tipos))}
    titulos = {}
    for l in open(os.path.join(base, "TABPLT", "TABPLTA.MSG"), encoding="cp1252").read().splitlines():
        p = l.split(None, 1)
        if p and p[0].isdigit() and int(p[0]) not in titulos:
            titulos[int(p[0])] = p[1].strip() if len(p) > 1 else ""
    pp = open(os.path.join(base, "PENAS", "PLOTPENA.PEN"), encoding="cp1252").read().splitlines()
    n = int(pp[0].split()[0])
    penas = []
    for k in range(n):
        c = int(pp[1 + 2 * k].split()[0], 16)
        penas.append((f"#{c & 255:02x}{c >> 8 & 255:02x}{c >> 16 & 255:02x}", float(pp[2 + 2 * k].split()[0])))
    out = {}
    for nv in range(256):
        ip = _indice(pen[nv])
        cor, esp = penas[ip] if ip < len(penas) else ("#000000", 0.2)
        h = _indice(hac[nv])
        out[nv] = dict(titulo=titulos.get(nv, ""), pena=ip + 1, cor_plot=cor, espessura=esp,
                       estilo_plot=_indice(est[nv]), hachura=h, hachura_def=hachuras.get(h) if h else None)
    return out


def ler_tela(modelo):
    """Tabela de níveis de tela: a gravada no desenho de referência e a padrão de um DWG 9/13 novo (só na memória).
    Devolve também a pena que o TQS dá a cada nível, para conferir a leitura da TABPLTA."""
    from TQS import TQSDwg as T
    sys.path.insert(0, RAIZ)
    from ferramentas.ler_modelo import ler
    dwg = T.Dwg()
    dwg.file.New()
    dwg.settings.systemId, dwg.settings.subSystemId = 9, 13
    dwg.file.LoadColors()
    lt = T.LevelsTable(dwg)
    tela = {nv: dict(cor_tela_9_13=lt.GetColor(str(nv)), estilo_tela_9_13=lt.GetStyle(str(nv))) for nv in range(256)}
    dwg.plotting.LoadPlottingTable()
    pena_tqs = {nv: dwg.plotting.AttributeRead(nv)[0] for nv in range(256)}
    dwg.file.Close()
    if modelo and os.path.exists(modelo):
        niv = ler(modelo)["niveis"]
        for nv in range(256):
            tela[nv].update(cor_tela=niv[nv]["cor"], estilo_tela=niv[nv]["estilo"])
    else:                                            # sem o modelo: mantém a tabela já gravada no niveis.json
        atual = json.loads(pathlib.Path(SAIDA).read_text(encoding="utf-8"))["niveis"]
        for nv in range(256):
            tela[nv].update(cor_tela=atual[str(nv)]["cor_tela"], estilo_tela=atual[str(nv)]["estilo_tela"])
        print("AVISO: modelo não encontrado; cores de tela mantidas do niveis.json atual")
    return tela, pena_tqs


def paleta_aci():
    """Paleta de tela do TQS (a mesma do AutoCAD, índices 1 a 255). Copiada de _apps/EstacaEscavada/estaca_dwg.py."""
    pal = {1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 255, 255), 5: (0, 0, 255), 6: (255, 0, 255),
           7: (255, 255, 255), 8: (128, 128, 128), 9: (192, 192, 192)}
    brilho = (255, 204, 153, 127, 76)
    for i in range(10, 250):
        h, k = (i - 10) // 10 * 15 / 360.0, i % 10
        v, s = brilho[k // 2] / 255.0, (1.0 if k % 2 == 0 else 0.5)
        pal[i] = tuple(round(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))
    for i, g in zip(range(250, 256), (51, 91, 132, 173, 214, 255)):
        pal[i] = (g, g, g)
    return {i: "#%02x%02x%02x" % rgb for i, rgb in pal.items()}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--suporte", default=r"C:\TQSW\SUPORTE\NGE")
    ap.add_argument("--modelo", default=os.path.join(RAIZ, "DesenhosReferencia", "PUN_P02.DWG"),
                    help="desenho de referência de onde vem a tabela de níveis de tela")
    a = ap.parse_args()
    plot = ler_tabplt(a.suporte)
    tela, pena_tqs = ler_tela(a.modelo)
    difs = [nv for nv in range(256) if pena_tqs[nv] + 1 != plot[nv]["pena"]]
    if difs:
        print("AVISO: pena diferente da lida pelo TQS nos níveis", difs)
    niveis = {nv: {**plot[nv], **tela[nv]} for nv in range(256)}
    dados = {"fonte": f"TABPLTA.DAT, TABPLTA.MSG e PENAS\\PLOTPENA.PEN de {a.suporte}; tela (cor_tela, "
                      f"estilo_tela) da tabela de níveis de {os.path.basename(a.modelo)}; tela padrão de um DWG 9/13 "
                      f"novo (TQSPythonInterface). Extraído em {date.today():%d/%m/%Y}.",
             "observacao": "pena começa em 1, como na janela do TQS; estilo 0 contínuo, 1 tracejado, 2 pontilhado, "
                           "3 traço-ponto, 4 traço-dois-pontos; estilo_tela -1 = padrão; cor_tela e estilo_tela são "
                           "os que o app grava nos desenhos (iguais nos dois desenhos de referência)",
             "paleta_tela": paleta_aci(), "niveis": niveis}
    with open(SAIDA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    print("gravado", SAIDA, "| penas conferidas com o TQS:", "ok" if not difs else f"{len(difs)} diferenças")


if __name__ == "__main__":
    main()
