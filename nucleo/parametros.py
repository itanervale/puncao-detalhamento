# -*- coding: utf-8 -*-
"""
Parâmetros de um pilar: padrões (os dos desenhos de referência), normalização, validação e altura útil.

Unidades: comprimentos em cm, bitolas em mm. bx é a dimensão do pilar na horizontal da prancha (eixo x), by na
vertical (eixo y). O projeto (.json) tem o formato {"formato": "puncao-detalhamento", "versao": 1, "pilares": [...]},
e cada pilar guarda só o que difere dos padrões.
"""
import copy
import json
import math

FORMATO, VERSAO = "puncao-detalhamento", 1
SOLUCOES = ("cobrinha", "conectores")
DIRECOES = ("menor", "maior", "x", "y")

PADROES = {
    # Pilar e laje
    "titulo": "P1",
    "repeticoes": 1,          # "1X" no nível 202 (o TQS multiplica os ferros no resumo)
    "bx": 50.0,               # dimensão do pilar na horizontal da prancha (cm)
    "by": 150.0,              # dimensão do pilar na vertical da prancha (cm)
    "h_laje": 27.0,
    "c_sup": 2.5,             # cobrimento superior: a cabeça do pino ou o trecho de cima da cobrinha vão até ele
    "c_inf": 2.5,
    "solucao": "cobrinha",
    "escala": 15.0,
    # Armadura negativa existente (só para a altura útil e o aviso dos vértices da cobrinha)
    "neg_bitola_ext": 10.0,   # camada externa (mm)
    "neg_bitola_int": 10.0,   # camada interna (mm)
    "d": None,                # altura útil (cm); None = calculada (altura_util)
    # Colapso progressivo (face inferior, passando dentro do pilar)
    "col_bitola": 10.0,
    "col_ext": 85.0,          # comprimento além da face (cm)
    "col_n_face_bx": 8,       # barras em cada face de comprimento bx (correm na direção y)
    "col_n_face_by": 3,       # barras em cada face de comprimento by (correm na direção x)
    # Cobrinha (malha ortogonal)
    "cob_s": 17.0,            # espaçamento da malha (cm)
    "cob_s_x": None,          # espaçamento na direção x (None = cob_s)
    "cob_s_y": None,
    "cob_s0": 11.0,           # distância da face à 1ª linha de pernas (cm)
    "cob_linhas": 4,          # linhas de pernas além de cada face, contando a de s0
    "cob_linhas_x": None,     # além das faces perpendiculares a x (None = cob_linhas)
    "cob_linhas_y": None,
    "cob_bitola": 10.0,
    "cob_direcao": "menor",   # cobrinhas paralelas ao lado menor do pilar (decisão P6), ou "maior", "x", "y"
    "mont_bitola": 12.5,      # montagem positiva, uma por fileira de pernas, na dobra de baixo
    "mont_ext": 30.0,         # além da última linha de cobrinhas (cm; 60 no modelo, 30 pelo usuário em 03/11/2026)
    "mont_arred": 5.0,        # comprimento arredondado para cima (cm)
}


def novo_projeto(pilares=None):
    return {"formato": FORMATO, "versao": VERSAO, "pilares": list(pilares or [])}


def ler_projeto(arq):
    with open(arq, encoding="utf-8") as f:
        dados = json.load(f)
    if isinstance(dados, dict) and dados.get("formato") == FORMATO:
        if int(dados.get("versao", 1)) > VERSAO:
            raise ValueError(f"projeto na versão {dados['versao']}; este app lê até a {VERSAO}")
        return dados
    if isinstance(dados, dict) and "pilares" in dados:
        return novo_projeto(dados["pilares"])
    return novo_projeto([dados])                     # um pilar solto


def _num(v, nome, erros, inteiro=False):
    if v is None:
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        erros.append(f"{nome}: valor inválido ({v!r})")
        return None
    return int(round(x)) if inteiro else x


def normalizar(par):
    """Parâmetros completos (padrões + os do pilar), com tipos corrigidos. Devolve (p, erros)."""
    p = copy.deepcopy(PADROES)
    p.update({k: v for k, v in (par or {}).items() if v is not None or k in ("d",)})
    erros = []
    inteiros = ("repeticoes", "col_n_face_bx", "col_n_face_by", "cob_linhas", "cob_linhas_x", "cob_linhas_y")
    for k in PADROES:
        if k in ("titulo", "solucao", "cob_direcao"):
            continue
        if p.get(k) is None and PADROES[k] is None:
            continue
        p[k] = _num(p.get(k), k, erros, k in inteiros)
    p["titulo"] = str(p["titulo"]).strip() or "P1"
    if p["solucao"] not in SOLUCOES:
        erros.append(f"solucao: use {' ou '.join(SOLUCOES)}")
    if p["cob_direcao"] not in DIRECOES:
        erros.append(f"cob_direcao: use {', '.join(DIRECOES)}")
    p["cob_s_x"] = p["cob_s_x"] or p["cob_s"]
    p["cob_s_y"] = p["cob_s_y"] or p["cob_s"]
    p["cob_linhas_x"] = p["cob_linhas_x"] or p["cob_linhas"]
    p["cob_linhas_y"] = p["cob_linhas_y"] or p["cob_linhas"]
    if not erros:
        erros += _validar(p)
    return p, erros


def _validar(p):
    erros = []
    for k in ("bx", "by", "h_laje", "escala", "col_bitola", "col_ext", "cob_s_x", "cob_s_y", "cob_s0",
              "cob_bitola", "mont_bitola", "neg_bitola_ext", "neg_bitola_int"):
        if not p[k] or p[k] <= 0:
            erros.append(f"{k} deve ser maior que zero")
    for k in ("c_sup", "c_inf", "mont_ext"):
        if p[k] is None or p[k] < 0:
            erros.append(f"{k} não pode ser negativo")
    for k in ("repeticoes", "col_n_face_bx", "col_n_face_by", "cob_linhas_x", "cob_linhas_y"):
        if p[k] is None or p[k] < 1:
            erros.append(f"{k} deve ser 1 ou mais")
    if not erros and p["solucao"] == "cobrinha" and altura_eixo_cobrinha(p) <= 0:
        erros.append("a cobrinha não cabe na laje: h - cobrimentos - bitola <= 0")
    return erros


def espessura_acima_da_negativa(p):
    """Espessura entre o cobrimento superior e a 1ª camada da negativa (cm): a cabeça do pino ou o trecho de cima
    da cobrinha, que ficam acima da armadura de flexão (19.5.3.3: extremidades ancoradas fora do plano dela)."""
    if p["solucao"] == "cobrinha":
        return p["cob_bitola"] / 10.0
    return p.get("pino_cabeca_esp", 1.0)              # conectores (E3): 0,8 + 0,2 de concordância, do modelo


def altura_util(p):
    """d = (dx + dy)/2 (NBR 6118:2026, 19.5.2.1), com a negativa abaixo da cabeça do pino ou da cobrinha:
    dx = h - c - e - ø1/2 e dy = h - c - e - ø1 - ø2/2, logo d = h - c - e - (3·ø1 + ø2)/4 (PLANO, seção 6.1)."""
    if p.get("d"):
        return float(p["d"])
    e = espessura_acima_da_negativa(p)
    f1, f2 = p["neg_bitola_ext"] / 10.0, p["neg_bitola_int"] / 10.0
    return p["h_laje"] - p["c_sup"] - e - (3 * f1 + f2) / 4


def altura_eixo_cobrinha(p):
    """Altura da cobrinha entre os eixos dos trechos de cima e de baixo (cm): as faces vão de cobrimento a
    cobrimento (decisão P4), logo h - c_sup - c_inf - ø. No modelo R01 (c = 2,0): 27 - 4 - 1 = 22."""
    return p["h_laje"] - p["c_sup"] - p["c_inf"] - p["cob_bitola"] / 10.0


def arred_cima(v, passo):
    return math.ceil(round(v / passo, 6)) * passo if passo else v
