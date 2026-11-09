# -*- coding: utf-8 -*-
"""
Conectores tipo pino (pentes Trejor) em arranjo radial. Python puro, sem o TQS.

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

Pilar de borda e de canto (E9; regras do plano, respostas Q10 a Q12 de 09/11/2026), com as bordas de
`parametros` (uma por direção) e o cobrimento da laje na borda (`cobrimento_borda`):
- **face voltada para a borda:** sem pentes; com a opção con_face_recuada (desligada; pedido do usuário em
  09/11/2026), no pilar recuado, pentes com os pinos que cabem: o último pino mais a ponta do pente (meia cabeça e o
  gancho do trilho) até o cobrimento da borda. Pode sair um pente mais curto (outro tipo no quadro); sem pino que
  caiba, a face fica sem pentes;
- **faces perpendiculares à borda:** os pentes da face, com a ponta do lado da borda a con_dist_canto do canto ou,
  se for preciso, afastada até o trilho ficar no cobrimento da borda;
- **inclinados:** só nos cantos internos (as duas faces voltadas para a laje), como no LPUNC;
- **linhas construtivas** (con_construtivas, Q12, desligada): no pilar recuado, um pente a mais em cada face
  perpendicular, além do canto, junto da borda (como o PuncV1);
- os pinos de fora vizinhos através de um canto do lado da borda não entram na verificação de 2d (o contorno
  termina na borda).
"""
import json
import math
import os

from .parametros import altura_util, arred_cima, cobrimento_borda

CATALOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo_trejor.json")
MAX_INCLINADOS = 12                                   # "auto" desiste daí e avisa
TOL_CONSTRUTIVA = 3.0                                 # cm: a linha construtiva só entra se ficar além disso do 1º pente


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


def cabeca_mm(p, cat=None):
    """Diâmetro da cabeça (mm): do catálogo ou, fora dele, na proporção do ø10 (32 mm), só para o desenho."""
    linha = pino_catalogo(p["con_bitola"], cat)
    return linha["cabeca_mm"] if linha else round(3.2 * p["con_bitola"])


def trilhos(p, cat=None):
    """Trilhos: quantidade, bitola e afastamento do eixo do trilho ao eixo dos pinos (encostado nas cabeças; no
    modelo, 1,625 + 0,25 = 1,875 com o trilho de 5 mm; com ø8, 2,0)."""
    return dict(quant=p["con_trilhos"], bitola=p["con_trilho_bitola"],
                afast=round(cabeca_mm(p, cat) / 20.0 + p["con_trilho_bitola"] / 20.0, 6))


def extensoes(p, cat=None):
    """O que o pente ocupa além do eixo dos pinos (cm): (lat, ponta). lat = para os lados (a cabeça ou o trilho);
    ponta = além dos pinos das pontas: meia cabeça e o gancho do trilho (raio 1,6 x o afastamento, como o bloco do
    pente na prancha)."""
    D = cabeca_mm(p, cat) / 10.0
    at, wt = trilhos(p, cat)["afast"], p["con_trilho_bitola"] / 10.0
    return max(D / 2, at + wt / 2), D / 2 + 1.6 * at + wt / 2


def posicoes_face(L, n, dc, dc_fim=None):
    """Posições dos pentes ao longo de uma face de comprimento L, de dc a L - dc_fim (dc_fim = dc, se omitido; um só:
    no meio). Os espaços são em centímetros inteiros, com a sobra no espaço do meio (ou metade em cada um dos dois do
    meio), como as linhas da cobrinha: face de 80 com 4 pentes a 5 dos cantos = 23 / 24 / 23, em vez de 23,33 (o TQS
    escreveria "23.3" nas cotas)."""
    if n == 1:
        return [L / 2.0]
    dc_fim = dc if dc_fim is None else dc_fim
    m = n - 1
    vao = L - dc - dc_fim
    base = math.floor(round(vao / m, 6))
    esp = [float(base)] * m
    resto = round(vao - base * m, 6)
    if m % 2:
        esp[m // 2] += resto
    else:
        esp[m // 2 - 1] += resto / 2
        esp[m // 2] += resto / 2
    pos, x = [dc], dc
    for e in esp:
        x += e
        pos.append(round(x, 6))
    return pos


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
    ângulo da face seguinte). Os ângulos são as direções para fora das duas faces do canto, em ordem crescente.
    O canto i fica entre a face i - 1 e a face i de _faces."""
    bx, by = p["bx"], p["by"]
    return [
        ("inferior esquerdo", (0.0, 0.0), 180.0, 270.0),
        ("inferior direito", (bx, 0.0), 270.0, 360.0),
        ("superior direito", (bx, by), 0.0, 90.0),
        ("superior esquerdo", (0.0, by), 90.0, 180.0),
    ]


def bordas_faces(p):
    """Faces voltadas para uma borda livre: {nome da face: distância da face à borda}. As faces têm os nomes dos
    lados da borda ("esquerda", "direita", "baixo", "cima")."""
    out = {}
    for eixo in ("x", "y"):
        lado = p.get(f"borda_{eixo}") or ""
        if lado:
            out[lado] = p.get(f"dist_borda_{eixo}") or 0.0
    return out


def _meio_cima(v):
    """Para cima a 0,5 cm."""
    return math.ceil(round(v * 2, 6)) / 2.0


def _pente(face, origem, ang, s0, tipo="face", n_pinos=None, seq=0.0):
    """Pente com o 1º pino a s0 da origem, na direção ang (graus). tipo: "face", "canto" ou "construtiva"; seq = a
    posição ao longo do contorno do pilar (face i: i + t/L; canto i: i), para achar os cantos entre vizinhos."""
    a = math.radians(ang)
    x, y = origem[0] + s0 * math.cos(a), origem[1] + s0 * math.sin(a)
    return dict(face=face, base=origem, ang=ang % 360.0, x=round(x, 6), y=round(y, 6), tipo=tipo, n_pinos=n_pinos,
                seq=seq)


def _pinos(pente, s0, sr, n):
    a = math.radians(pente["ang"])
    bx, by = pente["base"]
    n = pente.get("n_pinos") or n
    return [(bx + (s0 + i * sr) * math.cos(a), by + (s0 + i * sr) * math.sin(a)) for i in range(n)]


def pinos_na_face(p, face, cat=None):
    """Pinos de cada pente da face: con_pinos ou, na face voltada para a borda, com con_face_recuada, os que cabem até
    o cobrimento dela (o último pino mais a ponta do pente). 0 = a face fica sem pentes."""
    bordas = bordas_faces(p)
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    if face not in bordas:
        return n
    if not p.get("con_face_recuada"):                  # opção, desligada por padrão (pedido de 09/11/2026)
        return 0
    _lat, ponta = extensoes(p, cat)
    lim = bordas[face] - cobrimento_borda(p) - ponta
    return sum(1 for i in range(n) if s0 + i * sr <= lim + 1e-9)


def arranjo(p, k, cat=None):
    """Pentes em volta do pilar, com k inclinados por canto interno, na ordem em que aparecem girando no sentido
    anti-horário a partir do canto inferior esquerdo (assim pentes vizinhos ficam juntos na lista)."""
    s0, dc = p["con_s0"], p["con_dist_canto"]
    faces = _faces(p)
    cantos = _cantos(p)
    bordas = bordas_faces(p)
    nomes = [f[0] for f in faces]
    lat = extensoes(p, cat)[0] if bordas else 0.0
    c = cobrimento_borda(p)
    pentes = []
    for i, (nome, o, u, ang, L, n) in enumerate(faces):
        nome_c, pc, a1, a2 = cantos[i]
        ant, seg = nomes[i - 1], nomes[(i + 1) % 4]
        if ant not in bordas and nome not in bordas:   # inclinados só nos cantos internos
            for j in range(1, k + 1):                 # inclinados do canto que abre esta face
                pentes.append(_pente(f"canto {nome_c}", pc, a1 + (a2 - a1) * j / (k + 1), s0, tipo="canto",
                                     seq=float(i)))
        m = pinos_na_face(p, nome, cat)
        if m == 0:
            continue
        # do lado de uma borda, o trilho do pente da ponta fica no cobrimento dela
        ini = dc if ant not in bordas else max(dc, _meio_cima(c + lat - bordas[ant]))
        fim = dc if seg not in bordas else max(dc, _meio_cima(c + lat - bordas[seg]))
        ts = [(t, "face") for t in posicoes_face(L, n, ini, fim)]
        if p.get("con_construtivas"):                  # Q12: junto da borda, além do canto (pilar recuado)
            if ant in bordas:
                t = _meio_cima(c + lat - bordas[ant])
                if t < ts[0][0] - TOL_CONSTRUTIVA:
                    ts.insert(0, (t, "construtiva"))
            if seg in bordas:
                t = L - _meio_cima(c + lat - bordas[seg])
                if t > ts[-1][0] + TOL_CONSTRUTIVA:
                    ts.append((t, "construtiva"))
        for t, tipo in ts:
            base = (o[0] + u[0] * t, o[1] + u[1] * t)
            seq = i + min(max(t / L, 0.0), 1.0 - 1e-9)
            pentes.append(_pente(nome, base, ang, s0, tipo=tipo, n_pinos=m, seq=seq))
    return pentes                                     # a face esquerda fecha a volta no canto inferior esquerdo


def _t(pente, o, u):
    """Posição do pente ao longo da face (origem o, direção u)."""
    return round((pente["base"][0] - o[0]) * u[0] + (pente["base"][1] - o[1]) * u[1], 6)


def _cantos_internos(p):
    """Cantos (índices de _cantos) com as duas faces voltadas para a laje."""
    bordas = bordas_faces(p)
    nomes = [f[0] for f in _faces(p)]
    return {i for i in range(4) if nomes[i - 1] not in bordas and nomes[i] not in bordas}


def vizinhos_externos(p, pentes):
    """Pinos de fora de pentes vizinhos (a lista dá a volta): [dict(i, j, dist, canto, borda)]. canto = False quando os
    dois pentes são da mesma face (o espaçamento ali depende do nº de pentes da face, não dos inclinados); borda =
    True quando entre os dois há um canto do lado de uma borda livre (ali o contorno termina na borda e não há 2d a
    verificar)."""
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    ext = [_pinos(pt, s0, sr, n)[-1] for pt in pentes]
    internos = _cantos_internos(p)
    out = []
    for i in range(len(ext)):
        j = (i + 1) % len(ext)
        fi, fj = pentes[i]["face"], pentes[j]["face"]
        sa, sb = pentes[i].get("seq", 0.0), pentes[j].get("seq", 0.0)
        if sb < sa - 1e-9 or (j == 0 and len(ext) > 1):
            sb += 4.0
        cruzados = [c % 4 for c in range(math.floor(sa) + 1, math.floor(sb + 1e-9) + 1)]
        out.append(dict(i=i, j=j, dist=math.dist(ext[i], ext[j]),
                        canto=not (fi == fj and not fi.startswith("canto")),
                        borda=any(c not in internos for c in cruzados)))
    return out


def _maior(viz, canto):
    vals = [v["dist"] for v in viz if v["canto"] == canto and not v.get("borda")]
    return max(vals) if vals else 0.0


def inclinados(p, d):
    """Nº de pentes inclinados por canto interno: o pedido, nenhum ("cruz") ou o menor que deixa os pinos de fora
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


def _limites_laje(p):
    """Até onde a montagem pode ir em x e em y: (x0, x1, y0, y1), no cobrimento das bordas livres (None = sem
    borda desse lado)."""
    b, c = bordas_faces(p), cobrimento_borda(p)
    return (-b["esquerda"] + c if "esquerda" in b else None, p["bx"] + b["direita"] - c if "direita" in b else None,
            -b["baixo"] + c if "baixo" in b else None, p["by"] + b["cima"] - c if "cima" in b else None)


def montagem(p, pentes=None):
    """Montagem positiva opcional (Q7; desligada por padrão: o escritório aproveita as barras de flexão da laje,
    nota 1). Uma barra reta por linha de pinos em cada face, paralela a ela e apoiada nos trilhos, dos pentes de um
    canto aos do outro e mont_ext além (no cobrimento de uma borda livre), com o comprimento arredondado para cima a
    mont_arred. Devolve (barras, posições): barras = [dict(face, grupo, dist, p1, p2, comp)], em que dist é o
    afastamento da face e grupo é "by" (faces esquerda e direita) ou "bx" (de baixo e de cima), com um número quando
    o grupo tem barras de comprimentos diferentes (pilar de borda)."""
    if not p["con_montagem"]:
        return [], []
    s0, sr, n, ext = p["con_s0"], p["con_sr"], p["con_pinos"], p["mont_ext"]
    bordas = bordas_faces(p)
    lim = _limites_laje(p)
    barras = []
    for nome, o, u, ang, L, nf in _faces(p):
        if bordas:
            ts = [_t(pt, o, u) for pt in (pentes or []) if pt["face"] == nome]
            n_lin = pinos_na_face(p, nome)
        else:
            ts, n_lin = posicoes_face(L, nf, p["con_dist_canto"]), n
        if not ts or not n_lin:
            continue
        t0, t1 = min(ts) - ext, max(ts) + ext
        if bordas:                                    # no cobrimento da borda livre
            eixo = 0 if u[1] == 0 else 1
            lo, hi = lim[2 * eixo], lim[2 * eixo + 1]
            q0, q1 = sorted((o[eixo] + u[eixo] * t0, o[eixo] + u[eixo] * t1))
            q0, q1 = max(q0, lo) if lo is not None else q0, min(q1, hi) if hi is not None else q1
            t0, t1 = sorted(((q0 - o[eixo]) * u[eixo], (q1 - o[eixo]) * u[eixo]))
        comp = arred_cima(t1 - t0, p["mont_arred"])
        if not bordas:
            t0 -= (comp - (t1 - t0)) / 2                   # a sobra do arredondamento, metade em cada ponta
            t1 = t0 + comp
        grupo = "by" if nome in ("esquerda", "direita") else "bx"
        a = math.radians(ang)
        for i in range(n_lin):
            dist = s0 + i * sr
            off = (dist * math.cos(a), dist * math.sin(a))
            p1 = (round(o[0] + u[0] * t0 + off[0], 6), round(o[1] + u[1] * t0 + off[1], 6))
            p2 = (round(o[0] + u[0] * t1 + off[0], 6), round(o[1] + u[1] * t1 + off[1], 6))
            barras.append(dict(face=nome, grupo=grupo, dist=dist, p1=p1, p2=p2, comp=comp))
    posicoes = []
    for g in ("by", "bx"):
        comps = sorted({b["comp"] for b in barras if b["grupo"] == g}, reverse=True)
        for j, comp in enumerate(comps):
            nome_g = g if j == 0 else f"{g}{j + 1}"
            for b in barras:
                if b["grupo"] == g and b["comp"] == comp:
                    b["grupo"] = nome_g
            posicoes.append(dict(grupo=nome_g, quant=sum(1 for b in barras if b["grupo"] == nome_g), comp=comp))
    return barras, posicoes


def detalhar(p):
    """Geometria dos conectores de um pilar. Devolve um dict com:
    pentes (lista de dict face, base, ang, x, y, tipo, n_pinos, pinos), n_pentes, tipos (um por nº de pinos: n_pinos,
    quant, nome_bloco), nome_bloco (o do pente completo), texto_pentes, inclinados, contornos (afastamentos das linhas
    de pinos), espacamento_faces ({nome: passo}), vizinhos (pinos de fora de pentes vizinhos: i, j, distância, canto,
    borda), esp_externo_max, pino (bitola, cabeça, comprimento, livre, mínimo), trilhos, bordas e quadro (linhas do
    quadro "ARMADURA DE COMBATE À PUNÇÃO")."""
    d = altura_util(p)
    cat = catalogo()
    s0, sr, n = p["con_s0"], p["con_sr"], p["con_pinos"]
    k = inclinados(p, d)
    pentes = arranjo(p, k, cat)
    for pt in pentes:
        pt["n_pinos"] = pt["n_pinos"] or n
        pt["pinos"] = [(round(x, 6), round(y, 6)) for x, y in _pinos(pt, s0, sr, n)]
    viz = vizinhos_externos(p, pentes)
    L, livre, minimo = comprimento_pino(p, cat)
    linha = pino_catalogo(p["con_bitola"], cat)
    cabeca = cabeca_mm(p, cat)
    esp_faces = {}
    for nome, o, u, _a, Lf, nf in _faces(p):
        if bordas_faces(p):
            pos = sorted(_t(pt, o, u) for pt in pentes if pt["face"] == nome and pt["tipo"] == "face")
        else:
            pos = posicoes_face(Lf, nf, p["con_dist_canto"])
        esp_faces[nome] = round(pos[1] - pos[0], 6) if len(pos) > 1 else None
    pino = dict(bitola=p["con_bitola"], cabeca_mm=cabeca, comprimento_mm=L, livre_mm=livre, minimo_mm=minimo,
                no_catalogo=linha is not None, cabeca_esp=p["con_cabeca_esp"])
    mont, mont_pos = montagem(p, pentes)
    rep = p["repeticoes"]
    contagem = {}
    for pt in pentes:
        contagem[pt["n_pinos"]] = contagem.get(pt["n_pinos"], 0) + 1
    tipos = [dict(n_pinos=m, quant=q, nome_bloco=nome_bloco(m, sr)) for m, q in sorted(contagem.items(), reverse=True)]
    quadro = ["ARMADURA DE COMBATE À PUNÇÃO"]
    for t in tipos:
        rotulo = "PENTES" if len(tipos) == 1 else f"PENTES {t['nome_bloco']}"
        quadro += [f"QUANTIDADE: {rep} x {t['quant']} {rotulo}",
                   f"DESCRIÇÃO: {t['n_pinos']} {{ {_mm(p['con_bitola'])} mm (CA-50)",
                   f"com {_mm(L)} mm + {p['con_trilhos']} {{ {_mm(p['con_trilho_bitola'])} mm (CA-50)"]
    texto = " + ".join(f"{t['quant']} pentes {t['nome_bloco']}" for t in tipos)
    return dict(d=d, pentes=pentes, n_pentes=len(pentes), tipos=tipos, nome_bloco=nome_bloco(n, sr),
                texto_pentes=texto, inclinados=k,
                contornos=[round(s0 + i * sr, 6) for i in range(n)], espacamento_faces=esp_faces,
                vizinhos=viz, esp_canto_max=_maior(viz, True), esp_face_max=_maior(viz, False),
                esp_externo_max=max(v["dist"] for v in viz), pino=pino, trilhos=trilhos(p, cat),
                bordas=bordas_faces(p), quadro=quadro, montagem=mont, mont_posicoes=mont_pos)


def nome_bloco(n_pinos, sr):
    """Nome do bloco do pente, como no modelo: "PUN 3P 17 cm"."""
    return f"PUN {n_pinos}P {_mm(sr)} cm"


def _mm(v):
    return f"{v:g}".replace(".", ",")
