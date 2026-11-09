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
BORDAS_X = ("", "esquerda", "direita")
BORDAS_Y = ("", "baixo", "cima")


def posicao(p):
    """"interno", "borda" ou "canto", pelas bordas livres do pilar."""
    n = bool(p.get("borda_x")) + bool(p.get("borda_y"))
    return ("interno", "borda", "canto")[n]


def cobrimento_borda(p):
    """Cobrimento na borda livre: o da laje (Q15); o maior entre o superior e o inferior."""
    return max(p["c_sup"], p["c_inf"])

PADROES = {
    # Pilar e laje
    "titulo": "P1",
    "repeticoes": 1,          # "1X" no nível 202 (o TQS multiplica os ferros no resumo)
    "bx": 50.0,               # dimensão do pilar na horizontal da prancha (cm)
    "by": 150.0,              # dimensão do pilar na vertical da prancha (cm)
    "h_laje": 27.0,
    "c_sup": 2.5,             # cobrimento superior: a cabeça do pino ou o trecho de cima da cobrinha vão até ele
    "c_inf": 2.5,
    "fck": 25.0,              # concreto da laje (MPa): lb da ancoragem do colapso além de C'' (9.4.2.4)
    "solucao": "cobrinha",
    "escala": 15.0,
    # Borda livre (E9): uma por eixo, para não haver lados opostos; cobrimento na borda = o da laje (Q15)
    "borda_x": "",            # "", "esquerda" ou "direita": borda livre paralela a y, ao lado do pilar
    "borda_y": "",            # "", "baixo" ou "cima": borda livre paralela a x
    "dist_borda_x": 0.0,      # distância da face do pilar à borda (cm); 0 = faceando
    "dist_borda_y": 0.0,
    "col_gancho_borda": False,  # gancho nas barras de colapso que terminam na borda (Q13: opção, sem por padrão)
    # Armadura negativa existente (só para a altura útil e o aviso dos vértices da cobrinha)
    "neg_bitola_ext": 10.0,   # camada externa (mm)
    "neg_bitola_int": 10.0,   # camada interna (mm)
    "d": None,                # altura útil (cm); None = calculada (altura_util)
    # Colapso progressivo (face inferior, passando dentro do pilar)
    "col_bitola": 10.0,
    "col_ext": 85.0,          # comprimento além da face (cm)
    "col_n_face_bx": 3,       # barras em cada face de comprimento bx (correm na direção y); pilar padrão 50 x 150:
    "col_n_face_by": 8,       # 3 na face de 50 e 8 na de 150, como no P02 (pedido do usuário em 09/11/2026)
    # Cobrinha (malha ortogonal)
    "cob_s": 17.0,            # espaçamento da malha (cm)
    "cob_s_x": None,          # espaçamento na direção x (None = cob_s)
    "cob_s_y": None,
    "cob_s0": 11.0,           # distância da face à 1ª linha de pernas (cm)
    "cob_linhas": 4,          # linhas de pernas além de cada face, contando a de s0
    "cob_linhas_x": None,     # além das faces perpendiculares a x (None = cob_linhas)
    "cob_linhas_y": None,
    "cob_bitola": 10.0,
    "cob_direcao": "maior",   # cobrinhas paralelas ao lado maior do pilar (pedido do usuário em 09/11/2026; antes,
                              # ao menor: decisão P6), ou "menor", "x", "y"
    "mont_bitola": 12.5,      # montagem positiva, uma por fileira de pernas, na dobra de baixo
    "mont_ext": 30.0,         # além da última linha de cobrinhas (cm; 60 no modelo, 30 pelo usuário em 03/11/2026)
    "mont_arred": 5.0,        # comprimento arredondado para cima (cm)
    "mont_min_borda": 30.0,   # montagem ao lado do pilar, da face até a borda livre: abaixo disso não é desenhada
                              # (borda curta; os vértices ficam na armadura da laje; decisão do usuário, 09/11/2026)
    # Conectores (pentes Trejor, arranjo radial)
    "con_s0": 11.0,           # distância da face à 1ª linha de pinos (cm)
    "con_sr": 17.0,           # distância entre linhas de pinos (cm)
    "con_pinos": 3,           # pinos por pente (linhas de pinos)
    "con_n_face_bx": 3,       # pentes em cada face de comprimento bx (faces horizontais da prancha)
    "con_n_face_by": 5,       # pentes em cada face de comprimento by (faces verticais da prancha)
    "con_dist_canto": 5.0,    # distância do pente ao canto do pilar, ao longo da face (cm)
    "con_inclinados": "auto",  # pentes inclinados por canto: "auto" (o menor nº com <= 2d), "cruz" (0) ou um número
    "con_bitola": 10.0,       # pino CA-50 (mm); a cabeça vem do catálogo
    "con_cabeca_esp": 1.0,    # espessura da cabeça (cm): 0,8 + 0,2 de concordância, do modelo (Q3)
    "con_arred_mm": 5.0,      # comprimento do pino arredondado para baixo (mm; P4)
    "con_trilhos": 2,         # vergalhões que ligam os pinos
    "con_trilho_bitola": 8.0,
    "con_montagem": False,    # montagem positiva nos conectores: opcional, desligada (P7)
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
    inteiros = ("repeticoes", "col_n_face_bx", "col_n_face_by", "cob_linhas", "cob_linhas_x", "cob_linhas_y",
                "con_pinos", "con_n_face_bx", "con_n_face_by", "con_trilhos")
    for k in PADROES:
        if k in ("titulo", "solucao", "cob_direcao", "con_inclinados", "con_montagem", "borda_x", "borda_y",
                 "col_gancho_borda"):
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
    inc = str(p["con_inclinados"]).strip().lower()
    if inc in ("auto", "cruz"):
        p["con_inclinados"] = inc
    else:
        n = _num(inc, "con_inclinados", erros, inteiro=True)
        p["con_inclinados"] = n if n is not None else "auto"
    p["con_montagem"] = bool(p["con_montagem"]) and str(p["con_montagem"]).lower() not in ("0", "false", "nao")
    p["col_gancho_borda"] = bool(p["col_gancho_borda"]) and str(p["col_gancho_borda"]).lower() not in ("0", "false",
                                                                                                         "nao")
    for k, validos in (("borda_x", BORDAS_X), ("borda_y", BORDAS_Y)):
        v = str(p[k] or "").strip().lower()
        if v in ("nenhuma", "-"):                       # como a janela mostra o lado sem borda
            v = ""
        if v not in validos:
            erros.append(f"{k}: use {', '.join(repr(b) for b in validos)}")
        p[k] = v
    if not erros:
        erros += _validar(p)
    return p, erros


def _validar(p):
    erros = []
    for k in ("bx", "by", "h_laje", "escala", "col_bitola", "col_ext", "cob_s_x", "cob_s_y", "cob_s0",
              "cob_bitola", "mont_bitola", "neg_bitola_ext", "neg_bitola_int"):
        if not p[k] or p[k] <= 0:
            erros.append(f"{k} deve ser maior que zero")
    if not p["fck"] or not 0 < p["fck"] <= 90:
        erros.append("fck deve ficar entre 0 e 90 MPa")
    for k in ("c_sup", "c_inf", "mont_ext", "mont_min_borda", "dist_borda_x", "dist_borda_y"):
        if p[k] is None or p[k] < 0:
            erros.append(f"{k} não pode ser negativo")
    if (p["borda_x"] or p["borda_y"]) and p["solucao"] == "conectores":
        erros.append("conectores em pilar de borda ou de canto: ainda não implementado (E9: a cobrinha primeiro)")
    for k in ("repeticoes", "col_n_face_bx", "col_n_face_by", "cob_linhas_x", "cob_linhas_y"):
        if p[k] is None or p[k] < 1:
            erros.append(f"{k} deve ser 1 ou mais")
    if not erros and p["solucao"] == "cobrinha" and altura_eixo_cobrinha(p) <= 0:
        erros.append("a cobrinha não cabe na laje: h - cobrimentos - bitola <= 0")
    if p["solucao"] == "conectores":
        for k in ("con_s0", "con_sr", "con_bitola", "con_cabeca_esp", "con_trilho_bitola", "con_arred_mm"):
            if not p[k] or p[k] <= 0:
                erros.append(f"{k} deve ser maior que zero")
        for k in ("con_pinos", "con_n_face_bx", "con_n_face_by"):
            if p[k] is None or p[k] < 1:
                erros.append(f"{k} deve ser 1 ou mais")
        if p["con_dist_canto"] is None or p["con_dist_canto"] < 0:
            erros.append("con_dist_canto não pode ser negativo")
        for k, L in (("con_n_face_bx", p["bx"]), ("con_n_face_by", p["by"])):
            if p[k] and p[k] > 1 and p["con_dist_canto"] * 2 >= L:
                erros.append(f"{k}: a distância ao canto não deixa lugar para {p[k]} pentes na face de {L:g}")
        if isinstance(p["con_inclinados"], int) and p["con_inclinados"] < 0:
            erros.append("con_inclinados: use auto, cruz ou um número de 0 em diante")
    return erros


def espessura_acima_da_negativa(p):
    """Espessura entre o cobrimento superior e a 1ª camada da negativa (cm): a cabeça do pino ou o trecho de cima
    da cobrinha, que ficam acima da armadura de flexão (19.5.3.3: extremidades ancoradas fora do plano dela)."""
    if p["solucao"] == "cobrinha":
        return p["cob_bitola"] / 10.0
    return p["con_cabeca_esp"]                        # conectores: 0,8 + 0,2 de concordância, do modelo (Q3)


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
