# -*- coding: utf-8 -*-
"""Prancha de um pilar em DWG-TQS (mais PDF e DXF), com a conferência dos comprimentos que o TQS calcula."""
from nucleo import prancha_cobrinha, prancha_conectores
from nucleo.textos import limpar_nome

from . import arquivo, gravar


def gerar(res, pasta, nome=None, pdf=True, dxf=True):
    p = res["p"]
    if res["erros"]:
        raise ValueError("; ".join(res["erros"]))
    modulo = prancha_cobrinha if p["solucao"] == "cobrinha" else prancha_conectores
    folha = modulo.montar(res)
    dwg = arquivo.novo_desenho(p["escala"])
    ferros = gravar.desenhar(dwg, folha)
    tab = gravar.tabela(ferros)
    nome = nome or limpar_nome(f"PUN_{p['titulo']}")
    arqs = arquivo.salvar(dwg, pasta, nome, pdf=pdf, dxf=dxf)
    esperado = sorted((f["pos"], f["quant"], round(f["bitola"], 1), f["comp"]) for f in res["ferros"])
    return dict(arquivos=arqs, tabela_tqs=tab, esperado=esperado, confere=tab == esperado, folha=folha)
