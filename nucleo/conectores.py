# -*- coding: utf-8 -*-
"""
Conectores tipo pino (pentes Trejor) em arranjo radial, pilar interno. Python puro, sem o TQS.

Convenções (as da cobrinha): comprimentos em cm, bitolas em mm, origem no canto inferior esquerdo do pilar,
bx na horizontal e by na vertical da prancha.

Pente: con_pinos pinos de cabeça dupla em linha, a s0 + i·sr da face (ou do canto), ligados por con_trilhos
vergalhões. O ponto do pente é o 1º pino, e o ângulo aponta para fora do pilar (como o bloco `PUN 3P 17 cm` do
modelo, que tem o 1º pino na origem e os outros em +x).

- **Pentes das faces:** con_n_face_bx em cada face de comprimento bx (as de baixo e de cima) e con_n_face_by em cada
  face de comprimento by (esquerda e direita), distribuídos por igual entre as distâncias ao canto (con_dist_canto);
  um só fica no meio da face. Modelo P02 (50 x 150): 5, 40, 75, 110, 145 nas faces de 150 e 5, 25, 45 nas de 50.
- **Pentes inclinados (P9):** k por canto, saindo do canto, com os ângulos repartidos por igual entre as direções
  das duas faces (k = 1: a 45°). "auto" escolhe o menor k que deixa os pinos de fora vizinhos a <= 2d
  (NBR 6118:2026, 19.5.3.4 e Figura 19.8); "cruz" = nenhum inclinado. No P02, k = 1, e os pinos de fora do pente
  inclinado e do pente da face a 5 cm do canto ficam a 39,1 (a cota "39" do modelo), contra 2d = 45.
- **Pino:** h - c_sup - c_inf, arredondado para baixo a con_arred_mm, mínimo de 110 mm (catálogo; P4). A cabeça
  vem do catálogo (ø10: 32 mm).
- **Contornos:** retângulos de cantos arredondados afastados s0 + i·sr do pilar (nível 200 no modelo).
"""
import json
import math
import os

from .parametros import altura_util

CATALOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo_trejor.json")
MAX_INCLINADOS = 12                                   # "auto" desiste daí e avisa


def catalogo():
    with open(CATALOGO, encoding="utf-8") as f:
        return json.load(f)


def pino_catalogo(bitola, cat=None):
    """Linha do catálogo para a bitola (mm), ou None se a Trejor não fabrica."""
    cat = cat or catalogo()
    for linha in cat["pinos"]:
        if abs(linha["bitola_mm"] - bitola) < 1e-6:
            return linha
    return None


def comprimento_pino(p, cat=None):
    """(comprimento em mm, comprimento livre em mm): h - c_sup - c_inf, arredondado para baixo, e o mínimo."""
    cat = cat or catalogo()
    livre = (p["h_laje"] - p["c_sup"] - p["c_inf"]) * 10.0
    passo = p["con_arred_mm"]
    L = math.floor(round(livre / passo, 6)) * passo
    return L, livre, cat["comprimento_min_mm"]


def posicoes_face(L, n, dc):
    """Posições dos pentes ao longo de uma face de comprimento L: n por igual de dc a L - dc (um só: no meio)."""
    if n == 1:
        return [L / 2.0]
    passo = (L - 2.0 * dc) / (n - 1)
    return [round(dc + i * passo, 6) for i in range(n)]


def _faces(p):
    """As quatro faces no sentido anti-horário a partir da de baixo: (nome, origem, direção ao longo, ângulo para
    fora, comprimento, nº de pentes). A direção ao longo vai de um canto ao seguinte."""
    bx, by = p["bx"], p["by"]
    nbx, nby = p["con_n_face_bx"], p["con_n_face_by"]
    return [
        ("baixo", (0.0, 0.0), (1.0, 0.0), 270.0, bx, nbx),
        ("direita", (bx, 0.0), (0.0, 1.0), 0.0, by, nby),
        ("cima", (bx, by), (-1.0, 0.0), 90.0, bx, nbx),
        ("esquerda", (0.0, by), (0.0, -1.0), 180.0, by, nby),
    ]


def _cantos(p):
    """Cantos no sentido anti-horário a partir do inferior esquerdo: (nome, ponto, ângulo da face anterior,
    ângulo da face seguinte). Os ângulos são as direções para fora das duas faces do canto, em ordem crescente."""
    bx, by = p["bx"], p["by"]
    return [
        ("inferior esquerdo", (0.0, 0.0), 180.0, 270.0),
        ("inferior direito", (bx, 0.0), 270.0, 360.0),
        ("superior direito", (bx, by), 0.0, 90.0),
        ("superior esquerdo", (0.0, by), 90.0, 180.0),
    ]


def _pente(face, origem, ang, s0):
    """Pente com o 1º pino a s0 da origem, na direção ang (graus)."""
    a = math.radians(ang)
    x, y = origem[0] + s0 * math.cos(a), origem[1] + s0 * math.sin(a)
    return dict(face=face, base=origem, ang=ang % 360.0, x=round(x, 6), y=round(y, 6))


def _pinos(pente, s0, sr, n):
    a = math.radians(pente["ang"])
    bx, by = pente["base"]
    return [(bx + (s0 + i * sr) * math.cos(a), by + (s0 + i * sr) * math.sin(a)) for i in range(n)]


def arranjo(p, k):
    """Pentes em volta do pilar, com k inclinados por canto, na ordem em que aparecem girando no sentido
    anti-horário a partir do canto inferior esquerdo (assim pentes vizinhos ficam juntos na lista)."""
    s0, dc = p["con_s0"], p["con_dist_canto"]
    faces = _faces(p)
    cantos = _cantos(p)
    pentes = []
    for i, (nome, o, u, ang, L, n) in enumerate(faces):
        nome_c, pc, a1, a2 = cantos[i]
        for j in range(1, k + 1):                     # inclinados do canto que abre esta face
            pentes.append(_pente(f"canto {nome_c}", pc, a1 + (a2 - a1) * j / (k + 1), s0))
        for t in posicoes_face(L, n, dc):
            base = (o[0] + u[0] * t, o[1] + u[1] * t)
            pentes.append(_pente(nome, base, ang, s0))
    return pentes                                     # a face esquerda fecha a volta no canto inferior esquerdo


def vizinhos_externos(p, pentes):
    """Pinos de fora de pentes vizinhos (a lista dá a volta): [dict(i, j, dist, canto)]. canto = False quando os
    dois pentes são da mesma face (o espaçamento ali depende do nº de pentes da face, não dos inclinados)."""
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    ext = [_pinos(pt, s0, sr, n)[-1] for pt in pentes]
    out = []
    for i in range(len(ext)):
        j = (i + 1) % len(ext)
        fi, fj = pentes[i]["face"], pentes[j]["face"]
        out.append(dict(i=i, j=j, dist=math.dist(ext[i], ext[j]),
                        canto=not (fi == fj and not fi.startswith("canto"))))
    return out


def _maior(viz, canto):
    vals = [v["dist"] for v in viz if v["canto"] == canto]
    return max(vals) if vals else 0.0


def inclinados(p, d):
    """Nº de pentes inclinados por canto: o pedido, nenhum ("cruz") ou o menor que deixa os pinos de fora
    vizinhos, nos cantos, a <= 2d ("auto"). Os espaçamentos ao longo das faces não dependem disso e são
    verificados à parte."""
    modo = p["con_inclinados"]
    if modo == "cruz":
        return 0
    if isinstance(modo, int):
        return modo
    for k in range(0, MAX_INCLINADOS + 1):
        if _maior(vizinhos_externos(p, arranjo(p, k)), True) <= 2 * d + 1e-9:
            return k
    return MAX_INCLINADOS


def detalhar(p):
    """Geometria dos conectores de um pilar interno. Devolve um dict com:
    pentes (lista de dict face, base, ang, x, y, pinos), n_pentes, inclinados, k_atende, contornos (afastamentos
    das linhas de pinos), espacamento_faces ({nome: passo}), vizinhos (pinos de fora de pentes vizinhos:
    i, j, distância), esp_externo_max, pino (bitola, cabeça, comprimento, livre, mínimo), trilhos, nome_bloco e
    quadro (linhas do quadro "ARMADURA DE COMBATE À PUNÇÃO")."""
    d = altura_util(p)
    cat = catalogo()
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    k = inclinados(p, d)
    pentes = arranjo(p, k)
    for pt in pentes:
        pt["pinos"] = [(round(x, 6), round(y, 6)) for x, y in _pinos(pt, s0, sr, n)]
    viz = vizinhos_externos(p, pentes)
    L, livre, minimo = comprimento_pino(p, cat)
    linha = pino_catalogo(p["con_bitola"], cat)
    # Fora do catálogo, a cabeça fica na proporção do ø10 (32 mm), só para o desenho; a verificação avisa.
    cabeca = linha["cabeca_mm"] if linha else round(3.2 * p["con_bitola"])
    esp_faces = {}
    for nome, _o, _u, _a, Lf, nf in _faces(p):
        pos = posicoes_face(Lf, nf, p["con_dist_canto"])
        esp_faces[nome] = round(pos[1] - pos[0], 6) if len(pos) > 1 else None
    pino = dict(bitola=p["con_bitola"], cabeca_mm=cabeca, comprimento_mm=L, livre_mm=livre, minimo_mm=minimo,
                no_catalogo=linha is not None, cabeca_esp=p["con_cabeca_esp"])
    # Eixo do trilho encostado nas cabeças (no modelo, 1,625 + 0,25 = 1,875 com o trilho de 5 mm; com ø8, 2,0).
    trilhos = dict(quant=p["con_trilhos"], bitola=p["con_trilho_bitola"],
                   afast=round(cabeca / 20.0 + p["con_trilho_bitola"] / 20.0, 6))
    rep = p["repeticoes"]
    quadro = ["ARMADURA DE COMBATE À PUNÇÃO",
              f"QUANTIDADE: {rep} x {len(pentes)} PENTES",
              f"DESCRIÇÃO: {n} {{ {_mm(p['con_bitola'])} mm (CA-50)",
              f"com {_mm(L)} mm + {p['con_trilhos']} {{ {_mm(p['con_trilho_bitola'])} mm (CA-50)"]
    return dict(d=d, pentes=pentes, n_pentes=len(pentes), inclinados=k,
                contornos=[round(s0 + i * sr, 6) for i in range(n)], espacamento_faces=esp_faces,
                vizinhos=viz, esp_canto_max=_maior(viz, True), esp_face_max=_maior(viz, False),
                esp_externo_max=max(v["dist"] for v in viz), pino=pino, trilhos=trilhos,
                nome_bloco=f"PUN {n}P {_mm(sr)} cm", quadro=quadro)


def _mm(v):
    return f"{v:g}".replace(".", ",")
