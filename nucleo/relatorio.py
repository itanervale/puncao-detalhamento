# -*- coding: utf-8 -*-
"""
Relatório do lote (E6), sem o TQS: pilares, ferros, pentes, aço e avisos de um projeto, em três arquivos:
- RELATORIO_<projeto>.txt: legível, com os pilares, os ferros de cada um, o resumo de aço por bitola (com as
  repetições), os pentes Trejor somados, os avisos e os erros;
- RELATORIO_<projeto>_pilares.csv e RELATORIO_<projeto>_ferros.csv: para o Excel (ponto e vírgula, vírgula decimal,
  UTF-8 com BOM).

Quando o pilar foi gravado pelo TQS, os comprimentos dos ferros são os que o TQS calculou (dwg_tqs.prancha.gerar:
tabela_tqs) e o relatório diz se conferem com o núcleo; sem o TQS, são os do núcleo. A massa linear é a nominal da
ABNT NBR 7480 (ø² · 0,006165 kg/m nas bitolas fora da tabela).

Uso:
    itens = [item(detalhar(par), tqs) for par in pilares]      # tqs = o retorno de prancha.gerar, ou None
    rel = montar(itens, projeto="lote", arquivo="lote.json")
    arquivos = gravar(rel, pasta)
"""
import csv
import math
import os
from datetime import datetime

from .textos import limpar_nome

# Massa linear nominal (kg/m), ABNT NBR 7480, Tabela B.1 (barras e fios)
MASSA = {5.0: 0.154, 6.3: 0.245, 8.0: 0.395, 10.0: 0.617, 12.5: 0.963, 16.0: 1.578, 20.0: 2.466, 22.0: 2.984,
         25.0: 3.853, 32.0: 6.313, 40.0: 9.865}


def massa_linear(bitola):
    """kg/m da barra de bitola (mm)."""
    for b, m in MASSA.items():
        if abs(b - bitola) < 1e-6:
            return m
    return round(bitola ** 2 * math.pi / 4 * 7850e-6, 3)


def _n(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def _b(v):
    return f"{v:g}".replace(".", ",")


# ------------------------------------------------------------------------------------------- dados
def item(res, tqs=None):
    """Um pilar do relatório: o resultado de nucleo.detalhe.detalhar e, se gravado, o retorno de
    dwg_tqs.prancha.gerar (tabela_tqs, confere, arquivos)."""
    return dict(res=res, tqs=tqs)


def _ferros(it):
    """Ferros do pilar: [(pos, quant, bitola, comp, descricao)] e a fonte ("TQS" ou "núcleo")."""
    res, tqs = it["res"], it["tqs"]
    desc = {f["pos"]: f["descricao"] for f in res["ferros"]}
    if tqs and tqs.get("tabela_tqs"):
        return [(pos, q, b, c, desc.get(pos, "")) for pos, q, b, c in tqs["tabela_tqs"]], "TQS"
    return [(f["pos"], f["quant"], f["bitola"], f["comp"], f["descricao"]) for f in res["ferros"]], "núcleo"


def _armadura(res):
    p = res["p"]
    if "conectores" in res:
        c = res["conectores"]
        incl = "em cruz" if c["inclinados"] == 0 else f"{c['inclinados']} inclinado(s) por canto"
        return (f"{c['n_pentes']} pentes {c['nome_bloco']} ({incl}); pino ø{_b(c['pino']['bitola'])} x "
                f"{_b(c['pino']['comprimento_mm'])} mm, cabeça {c['pino']['cabeca_mm']} mm; "
                f"{c['trilhos']['quant']} trilhos ø{_b(c['trilhos']['bitola'])}")
    c = res["cobrinha"]
    return f"{c['n_pecas']} cobrinhas ø{_b(p['cob_bitola'])} em {c['direcao']}, {c['n_linhas']} linhas"


def montar(itens, projeto="", arquivo=None, data=None):
    """Relatório do lote: dict com o cabeçalho, as linhas dos pilares e dos ferros, o resumo de aço por bitola, os
    pentes somados, os avisos, os erros e o texto completo."""
    data = data or datetime.now()
    pilares, ferros, avisos, erros = [], [], [], []
    bitolas, pentes = {}, {}
    n_tqs = n_dif = 0
    for it in itens:
        res, tqs = it["res"], it["tqs"]
        p = res["p"]
        rep = p["repeticoes"]
        linha = dict(pilar=p["titulo"], rep=rep, bx=p["bx"], by=p["by"], h=p["h_laje"], solucao=p["solucao"])
        if res["erros"]:
            erros += [(p["titulo"], e) for e in res["erros"]]
            pilares.append(dict(linha, d=None, armadura="; ".join(res["erros"]), aco=None, aco_rep=None,
                                avisos=0, erros=len(res["erros"]), fonte="", conferencia="", dwg="não gravado"))
            continue
        lista, fonte = _ferros(it)
        aco = 0.0
        for pos, q, b, c, d in lista:
            tot = q * c / 100.0
            kg = tot * massa_linear(b)
            aco += kg
            ferros.append(dict(pilar=p["titulo"], rep=rep, pos=pos, quant=q, bitola=b, comp=c, total=tot, kg=kg,
                               kg_rep=kg * rep, descricao=d, fonte=fonte))
            s = bitolas.setdefault(float(b), [0.0, 0.0])
            s[0] += tot * rep
            s[1] += kg * rep
        if "conectores" in res:
            c = res["conectores"]
            chave = (c["nome_bloco"], c["pino"]["bitola"], c["pino"]["comprimento_mm"], c["pino"]["cabeca_mm"],
                     c["trilhos"]["quant"], c["trilhos"]["bitola"], c["pino"]["no_catalogo"])
            g = pentes.setdefault(chave, dict(pentes=0, pinos=0, pilares=[]))
            g["pentes"] += c["n_pentes"] * rep
            g["pinos"] += c["n_pentes"] * len(c["pentes"][0]["pinos"]) * rep
            g["pilares"].append(p["titulo"])
        vs = [v for v in res["verificacoes"] if v[0] == "aviso"]
        avisos += [(p["titulo"], txt, ref) for _, txt, ref in vs]
        conf = ""
        if tqs:
            n_tqs += 1
            conf = "confere" if tqs.get("confere") else "difere"
            n_dif += 0 if tqs.get("confere") else 1
        dwg = os.path.basename(tqs["arquivos"]["dwg"]) if tqs and tqs.get("arquivos", {}).get("dwg") else ""
        pilares.append(dict(linha, d=res["d"], armadura=_armadura(res), aco=aco, aco_rep=aco * rep, avisos=len(vs),
                            erros=0, fonte=fonte, conferencia=conf, dwg=dwg or "não gravado"))
    resumo = [dict(bitola=b, total=v[0], kg=v[1]) for b, v in sorted(bitolas.items())]
    conectores = [dict(bloco=k[0], pino=k[1], comprimento_mm=k[2], cabeca_mm=k[3], trilhos=k[4], trilho_bitola=k[5],
                       catalogo=k[6], **v) for k, v in sorted(pentes.items(), key=lambda kv: (kv[0][0], kv[0][2]))]
    n = len(pilares)
    rel = dict(projeto=projeto, arquivo=arquivo, data=data, pilares=pilares, ferros=ferros, resumo=resumo,
               conectores=conectores, avisos=avisos, erros=erros, n_tqs=n_tqs, n_difere=n_dif,
               n_conectores=sum(1 for q in pilares if q["solucao"] == "conectores"),
               n_cobrinha=sum(1 for q in pilares if q["solucao"] == "cobrinha"),
               n_com_rep=sum(q["rep"] for q in pilares), n=n)
    rel["texto"] = texto(rel)
    return rel


# ------------------------------------------------------------------------------------------- texto
def texto(rel):
    L = []
    L.append("ARMADURAS DE PUNÇÃO - RELATÓRIO DO LOTE")
    L.append("=" * 100)
    L.append(f"Projeto: {rel['projeto']}" + (f" ({rel['arquivo']})" if rel["arquivo"] else ""))
    L.append(f"Data: {rel['data']:%d/%m/%Y %H:%M}")
    L.append(f"Pilares: {rel['n']} ({rel['n_conectores']} com conectores, {rel['n_cobrinha']} com cobrinha); "
             f"com as repetições: {rel['n_com_rep']}")
    if rel["n_tqs"]:
        nd = rel["n_difere"]
        conf = ("todos conferem com o núcleo" if not nd else
                f"{nd} {'difere' if nd == 1 else 'diferem'} do núcleo")
        resto = "; nos demais, pelo núcleo" if rel["n_tqs"] < rel["n"] else ""
        L.append(f"Comprimentos dos ferros: pelo TQS em {rel['n_tqs']} de {rel['n']} pilar(es) ({conf}){resto}.")
    else:
        L.append("Comprimentos dos ferros: pelo núcleo (os pilares não foram gravados pelo TQS neste relatório).")
    L.append("O app não dimensiona: detalha a armadura definida pelo projetista e confere a geometria pela "
             "NBR 6118:2026.")
    L.append("")
    L.append("PILARES")
    L.append("-" * 100)
    L.append(f"{'Pilar':<10}{'Rep.':>5}  {'Pilar (cm)':<12}{'h':>4}  {'Solução':<11}{'d (cm)':>7}  "
             f"{'Aço (kg)':>9}{'x rep.':>9}{'Avisos':>8}  DWG")
    for q in rel["pilares"]:
        dim = f"{_b(q['bx'])} x {_b(q['by'])}"
        d = _n(q["d"], 2) if q["d"] is not None else "-"
        aco = _n(q["aco"]) if q["aco"] is not None else "-"
        acor = _n(q["aco_rep"]) if q["aco_rep"] is not None else "-"
        L.append(f"{q['pilar']:<10}{q['rep']:>5}  {dim:<12}{_b(q['h']):>4}  {q['solucao']:<11}{d:>7}  "
                 f"{aco:>9}{acor:>9}{q['avisos']:>8}  {q['dwg']}" + (f" ({q['conferencia']})" if q["conferencia"]
                                                                       else ""))
        L.append(f"{'':<10}     {q['armadura']}")
    L.append("")
    L.append("FERROS (por pilar; o aço dos pentes fica no quadro dos conectores)")
    L.append("-" * 100)
    atual = None
    for f in rel["ferros"]:
        if f["pilar"] != atual:
            atual = f["pilar"]
            L.append(f"{atual} ({f['rep']}X), comprimentos pelo {f['fonte']}")
        L.append(f"   N{f['pos']:<3}{f['quant']:>4} ø{_b(f['bitola']):<5} C={f['comp']:<5}"
                 f"{_n(f['total'], 2):>8} m{_n(f['kg'], 2):>9} kg   {f['descricao']}")
    L.append("")
    L.append("RESUMO DE AÇO (ferros inteligentes, com as repetições)")
    L.append("-" * 100)
    L.append(f"{'Bitola':<10}{'Comprimento (m)':>16}{'Peso (kg)':>12}")
    for r in rel["resumo"]:
        L.append(f"ø{_b(r['bitola']):<9}{_n(r['total'], 2):>16}{_n(r['kg']):>12}")
    tot_m, tot_kg = sum(r["total"] for r in rel["resumo"]), sum(r["kg"] for r in rel["resumo"])
    L.append(f"{'Total':<10}{_n(tot_m, 2):>16}{_n(tot_kg):>12}")
    if rel["conectores"]:
        L.append("")
        L.append("CONECTORES (pentes Trejor, com as repetições; aço pelo fabricante)")
        L.append("-" * 100)
        L.append(f"{'Pente':<16}{'Pino':<24}{'Trilhos':<12}{'Pentes':>8}{'Pinos':>8}  Pilares")
        for c in rel["conectores"]:
            pino = f"ø{_b(c['pino'])} x {_b(c['comprimento_mm'])} mm"
            if not c["catalogo"]:
                pino += " (fora do catálogo)"
            L.append(f"{c['bloco']:<16}{pino:<24}{str(c['trilhos']) + ' ø' + _b(c['trilho_bitola']):<12}"
                     f"{c['pentes']:>8}{c['pinos']:>8}  {', '.join(c['pilares'])}")
        L.append(f"{'Total':<52}{sum(c['pentes'] for c in rel['conectores']):>8}"
                 f"{sum(c['pinos'] for c in rel['conectores']):>8}")
    L.append("")
    L.append(f"AVISOS ({len(rel['avisos'])})")
    L.append("-" * 100)
    if rel["avisos"]:
        for pilar, txt, ref in rel["avisos"]:
            L.append(f"{pilar}: {txt} ({ref})")
    else:
        L.append("Nenhum.")
    if rel["erros"]:
        L.append("")
        L.append(f"ERROS ({len(rel['erros'])}): pilares sem desenho")
        L.append("-" * 100)
        for pilar, e in rel["erros"]:
            L.append(f"{pilar}: {e}")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------------------------- arquivos
def _seguro(v):
    """Célula de texto que o Excel leria como fórmula (=, +, -, @, tabulação ou quebra de linha no início) ganha um
    apóstrofo: os títulos e as descrições vêm do projeto ou da colagem, que podem vir de fora."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return "'" + v
    return v


def _csv(arq, cab, linhas, texto=()):
    """CSV para o Excel; as colunas de índice em `texto` passam por _seguro."""
    with open(arq, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        for lin in linhas:
            w.writerow([_seguro(v) if i in texto else v for i, v in enumerate(lin)])


def gravar(rel, pasta, nome=None):
    """Grava o TXT e os dois CSV na pasta. Devolve {txt, pilares, ferros}: os caminhos."""
    os.makedirs(pasta, exist_ok=True)
    base = os.path.join(pasta, "RELATORIO_" + limpar_nome(nome or rel["projeto"] or "projeto"))
    arqs = dict(txt=base + ".txt", pilares=base + "_pilares.csv", ferros=base + "_ferros.csv")
    with open(arqs["txt"], "w", encoding="utf-8", newline="\r\n") as f:
        f.write(rel["texto"])

    def num(v, casas=2):
        return "" if v is None else _n(v, casas)
    _csv(arqs["pilares"],
         ["Pilar", "Repetições", "bx (cm)", "by (cm)", "h (cm)", "Solução", "d (cm)", "Armadura de punção",
          "Aço (kg)", "Aço x rep. (kg)", "Avisos", "Erros", "Comprimentos", "Conferência TQS", "DWG"],
         [[q["pilar"], q["rep"], _b(q["bx"]), _b(q["by"]), _b(q["h"]), q["solucao"], num(q["d"]), q["armadura"],
           num(q["aco"]), num(q["aco_rep"]), q["avisos"], q["erros"], q["fonte"], q["conferencia"], q["dwg"]]
          for q in rel["pilares"]], texto=(0, 5, 7, 12, 13, 14))
    _csv(arqs["ferros"],
         ["Pilar", "Repetições", "Posição", "Quantidade", "Bitola (mm)", "C (cm)", "Comprimento total (m)",
          "Peso (kg)", "Peso x rep. (kg)", "Descrição", "Comprimentos"],
         [[f["pilar"], f["rep"], f"N{f['pos']}", f["quant"], _b(f["bitola"]), f["comp"], num(f["total"]),
           num(f["kg"]), num(f["kg_rep"]), f["descricao"], f["fonte"]] for f in rel["ferros"]], texto=(0, 9, 10))
    return arqs
