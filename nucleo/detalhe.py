# -*- coding: utf-8 -*-
"""
Detalhamento de um pilar, sem o TQS: parâmetros normalizados, geometria, ferros numerados e verificações.

Uso:  python -m nucleo.detalhe <projeto.json>
Imprime, para cada pilar, os ferros (posição, quantidade, bitola, comprimento) e as verificações.
"""
import sys

from . import cobrinha, colapso, verificacoes
from .parametros import altura_util, ler_projeto, normalizar


def detalhar(par):
    """Resultado de um pilar: dict com p (parâmetros completos), d, erros, verificacoes, ferros e a geometria da
    solução (cobrinha ou conectores) e do colapso. Com erros, só p e erros."""
    p, erros = normalizar(par)
    res = dict(p=p, erros=erros, verificacoes=[], ferros=[])
    if erros:
        return res
    res["d"] = altura_util(p)
    ferros = []
    if p["solucao"] == "cobrinha":
        cob = cobrinha.detalhar(p)
        res["cobrinha"] = cob
        ferros.append(dict(tipo="cobrinha", bitola=p["cob_bitola"], quant=cob["n_cobrinhas"],
                           comp=round(cob["comprimento"]), descricao="cobrinha (armadura de punção)"))
        ferros.append(dict(tipo="montagem", bitola=p["mont_bitola"], quant=len(cob["mont_pos"]),
                           comp=round(cob["mont_comp"]), descricao="montagem positiva nos vértices de baixo"))
        res["verificacoes"] = verificacoes.cobrinha(p, cob)
    else:
        res["erros"].append("conectores: etapa E3 (ainda não implementada)")
        return res
    col = colapso.detalhar(p)
    res["colapso"] = col
    for g in col:
        ferros.append(dict(tipo="colapso", direcao=g["direcao"], bitola=p["col_bitola"], quant=g["quant"],
                           comp=g["comp"], descricao=f"colapso progressivo, face inferior, em {g['direcao']}"))
    for i, f in enumerate(ferros, 1):
        f["pos"] = i
    res["ferros"] = ferros
    return res


def _bitola(v):
    return f"{v:g}".replace(".", ",")


def relatorio(res):
    p = res["p"]
    linhas = [f"== {p['titulo']} ({p['bx']:g} x {p['by']:g}), laje {p['h_laje']:g}, {p['solucao']}, "
              f"{p['repeticoes']}X"]
    if res["erros"]:
        return "\n".join(linhas + [f"   ERRO: {e}" for e in res["erros"]])
    if "cobrinha" in res:
        c = res["cobrinha"]
        linhas.append(f"   cobrinhas em {c['direcao']}: {c['n_cobrinhas']} linhas ({_esp(c['esp_linhas'])}), "
                      f"{c['n_pernas']} pernas ({_esp(c['esp_pernas'])}), altura pelo eixo {c['altura_eixo']:g}")
    for f in res["ferros"]:
        linhas.append(f"   N{f['pos']}  {f['quant']:>3} ø{_bitola(f['bitola']):<5} C={f['comp']:<5} {f['descricao']}")
    for tipo, txt, ref in res["verificacoes"]:
        linhas.append(f"   {'AVISO' if tipo == 'aviso' else 'ok   '} {txt} ({ref})")
    return "\n".join(linhas)


def _esp(esp):
    """Espaçamentos agrupados: "3x17 18 18 3x17"."""
    out, i = [], 0
    while i < len(esp):
        j = i
        while j + 1 < len(esp) and abs(esp[j + 1] - esp[i]) < 1e-6:
            j += 1
        out.append(f"{j - i + 1}x{esp[i]:g}" if j > i else f"{esp[i]:g}")
        i = j + 1
    return " ".join(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for par in ler_projeto(sys.argv[1])["pilares"]:
        print(relatorio(detalhar(par)))


if __name__ == "__main__":
    main()
