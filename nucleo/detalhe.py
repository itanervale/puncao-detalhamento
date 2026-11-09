# -*- coding: utf-8 -*-
"""
Detalhamento de um pilar, sem o TQS: parâmetros normalizados, geometria, ferros numerados e verificações.

Uso:  python -m nucleo.detalhe <projeto.json>
Imprime, para cada pilar, os ferros (posição, quantidade, bitola, comprimento) e as verificações.
"""
import sys

from . import cobrinha, colapso, conectores, verificacoes
from .parametros import altura_util, ler_projeto, normalizar

DESCRICAO_COBRINHA = {"extremidade": "cobrinha da face para fora",
                      "extremidade_borda": "cobrinha da face até a borda livre",
                      "continua": "cobrinha inteira, ao lado do pilar",
                      "continua_borda": "cobrinha inteira, ao lado do pilar, do lado livre ao da borda",
                      "recuada": "cobrinha diante da face recuada, entre os prolongamentos das faces"}


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
        for g in cob["posicoes"]:
            desc = DESCRICAO_COBRINHA[g["tipo"]]
            ferros.append(dict(tipo="cobrinha", subtipo=g["tipo"], bitola=p["cob_bitola"], quant=g["quant"],
                               comp=round(g["comp"]), pontos=g["pontos"], descricao=desc))
        for g in cob["mont_posicoes"]:
            desc = ("montagem positiva, contínua" if g["tipo"] == "continua"
                    else "montagem positiva, da face do pilar para fora")
            ferros.append(dict(tipo="montagem", subtipo=g["tipo"], bitola=p["mont_bitola"], quant=g["quant"],
                               comp=round(g["comp"]), descricao=desc))
        res["verificacoes"] = verificacoes.cobrinha(p, cob)
    else:
        # Os pentes não são ferros do TQS: o aço deles vai só no quadro (P11).
        con = conectores.detalhar(p)
        res["conectores"] = con
        res["verificacoes"] = verificacoes.conectores(p, con)
    col = colapso.detalhar(p)
    res["colapso"] = col
    res["verificacoes"] += verificacoes.colapso(res)
    for g in col:
        ferros.append(dict(tipo="colapso", direcao=g["direcao"], bitola=p["col_bitola"], quant=g["quant"],
                           comp=g["comp"], descricao=f"colapso progressivo, face inferior, em {g['direcao']}"
                           + (", gancho de 90° na borda livre" if any(g["ganchos"]) else "")))
    if "conectores" in res:
        # Montagem opcional depois do colapso: o N1 e o N2 do colapso ficam como no modelo.
        for g in res["conectores"]["mont_posicoes"]:
            faces = "esquerda e direita" if g["grupo"].startswith("by") else "de baixo e de cima"
            ferros.append(dict(tipo="montagem", subtipo=g["grupo"], bitola=p["mont_bitola"], quant=g["quant"],
                               comp=round(g["comp"]), descricao=f"montagem positiva nos pentes, faces {faces}"))
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
        linhas.append(f"   cobrinhas em {c['direcao']}: {c['n_linhas']} linhas ({_esp(c['esp_linhas'])}), "
                      f"pernas nas linhas ao lado do pilar ({_esp(c['esp_lado'])}), "
                      f"altura pelo eixo {c['altura_eixo']:g}, {c['n_pecas']} peças")
    if "conectores" in res:
        c = res["conectores"]
        faces = ", ".join(f"{k} {v:g}" for k, v in c["espacamento_faces"].items() if v)
        linhas.append(f"   {c['texto_pentes']} ({c['inclinados']} inclinado(s) por canto), "
                      f"contornos a {', '.join(f'{v:g}' for v in c['contornos'])}, entre pentes: {faces}; "
                      f"cantos {c['esp_canto_max']:.1f}")
        for q in c["quadro"][1:]:
            linhas.append(f"   {q}")
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
