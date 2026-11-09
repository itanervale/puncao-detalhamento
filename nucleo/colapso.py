# -*- coding: utf-8 -*-
"""
Armadura contra colapso progressivo: barras retas na face inferior, passando dentro do pilar e col_ext além das
faces. Em cada face, n barras distribuídas por igual, cada uma no meio da sua faixa: posição (i + 1/2)·L/n.
Nos dois modelos: 3 barras na face de 50 (8,33; 25; 41,67) e 8 na de 150 (a cada 18,75, a 1ª em 9,375).

A 1ª posição é a das barras que correm em x (atravessam as faces de comprimento by), como nos dois modelos
(conectores: N1 8 ø10 C=220; cobrinha: N3 3 ø10 C=320).

Verificações (NBR 6118:2026, 19.5.4):
- ancoragem: a armadura que atravessa o contorno C deve estar ancorada além de C' (sem armadura de punção) ou de C''
  (com armadura de punção; regra do usuário de 09/11/2026). C'' fica 2d além da última linha da armadura de punção;
  a parte da barra além dele deve ter pelo menos lb (9.4.2.4, barra reta, boa aderência na face inferior);
- capacidade, com as cargas importadas do TQS: As·fyd >= 1,5·FSd, FSd com γf = 1,2 sobre a maior força Z das
  combinações de ELU (característica), e As a soma das barras que cruzam cada face (uma barra que atravessa o pilar
  cruza duas faces).
"""
import math

FYD = 50.0 / 1.15                     # CA-50, kN/cm2
GAMA_F_CCP = 1.2
TF_KN = 10.0                          # 1 tf = 10 kN, como no LPUNC e no app de cálculo


def _pontas(p, eixo, L):
    """Início e fim das barras que correm ao longo de `eixo`: col_ext além das faces; do lado de uma borda livre,
    no cobrimento dela (Q13: as perpendiculares à borda terminam na borda). Devolve (ini, fim, borda_ini, borda_fim)."""
    from .parametros import cobrimento_borda
    ext, c = p["col_ext"], cobrimento_borda(p)
    neg, pos = ("esquerda", "direita") if eixo == "x" else ("baixo", "cima")
    borda, a = p.get(f"borda_{eixo}") or "", p.get(f"dist_borda_{eixo}") or 0.0
    ini = -a + c if borda == neg else -ext
    fim = L + a - c if borda == pos else L + ext
    return ini, fim, borda == neg, borda == pos


def pino(fi_mm):
    """Diâmetro do pino de dobramento do gancho (cm), NBR 6118:2026, Tabela 9.1, CA-50: 5ø abaixo de ø20, 8ø a
    partir dele."""
    return (8 if fi_mm >= 20 else 5) * fi_mm / 10.0


def gancho_90(fi_mm):
    """Acréscimo ao comprimento de um gancho de 90° (ponta reta de 8ø, NBR 6118:2026, 9.4.2.3) como o TQS calcula
    (ICP090; medido em 09/11/2026 de ø8 a ø20: 8, 10, 12, 16 e 21 cm): 8ø + (π/2 - 1)·R, com R o raio da dobra
    pelo eixo, arredondado ao centímetro em cada gancho."""
    fi = fi_mm / 10.0
    R = pino(fi_mm) / 2 + fi / 2
    return math.floor(8 * fi + (math.pi / 2 - 1) * R + 0.5)


def altura_gancho(fi_mm):
    """Altura do gancho de 90° pelas faces externas (cm): ponta de 8ø mais o raio externo da dobra."""
    return 8 * fi_mm / 10.0 + pino(fi_mm) / 2 + fi_mm / 10.0


def detalhar(p):
    bx, by = p["bx"], p["by"]
    nx, ny = p["col_n_face_by"], p["col_n_face_bx"]       # barras que correm em x / em y
    out = []
    for direcao, quant, L, Lt in (("x", nx, bx, by), ("y", ny, by, bx)):
        ini, fim, b_ini, b_fim = _pontas(p, direcao, L)
        # gancho de 90° (para cima) na ponta que termina na borda livre: opção, sem gancho por padrão (Q13)
        ganchos = (b_ini and p["col_gancho_borda"], b_fim and p["col_gancho_borda"])
        reto = math.ceil(round(fim - ini, 6))             # o trecho reto, pelas faces externas dos ganchos
        comp = reto + sum(ganchos) * gancho_90(p["col_bitola"])
        # faces que a barra cruza e que contam no As (19.5.4): a face voltada para uma borda livre não conta, nem
        # com o pilar recuado (regra do usuário em 09/11/2026: borda = 3 faces, canto = 2)
        faces = int(ini < 0 and not b_ini) + int(fim > L and not b_fim)
        out.append(dict(direcao=direcao, quant=quant, pos=[round((i + 0.5) * Lt / quant, 4) for i in range(quant)],
                        ini=ini, fim=fim, comp=comp, reto=reto, borda_ini=b_ini, borda_fim=b_fim, ganchos=ganchos,
                        faces=faces))
    return out


def area(fi_mm):
    return math.pi * (fi_mm / 10.0) ** 2 / 4


def lb_basico(fi_mm, fck, boa_aderencia=True):
    """Comprimento de ancoragem básico (cm), NBR 6118:2026, 9.4.2.4: lb = (ø/4)·(fyd/fbd) >= 25ø, com
    fbd = η1·η2·η3·fctd (η1 = 2,25 barra nervurada; η2 = 1,0 boa aderência ou 0,7; η3 = 1,0 até ø32) e
    fctd = 0,7·fct,m/1,4 (fct,m = 0,3·fck^(2/3) até C50; 2,12·ln(1 + 0,11·fck) acima)."""
    fctm = 0.3 * fck ** (2 / 3) if fck <= 50 else 2.12 * math.log(1 + 0.11 * fck)
    fctd = 0.7 * fctm / 1.4
    eta3 = 1.0 if fi_mm < 32 else (132 - fi_mm) / 100
    fbd = 2.25 * (1.0 if boa_aderencia else 0.7) * eta3 * fctd           # MPa
    fi = fi_mm / 10.0
    return max(fi / 4 * (FYD * 10) / fbd, 25 * fi)


def ultima_linha(res):
    """Distância da face do pilar à última linha da armadura de punção, por direção das barras de colapso (as que
    correm em x saem pelas faces perpendiculares a x). Cobrinha: a perna ou a linha mais afastada, só nos lados
    livres (do lado de uma borda, a barra termina na borda e não há C''); conectores: o último contorno de pinos."""
    if "conectores" in res:
        u = res["conectores"]["contornos"][-1]
        return {"x": u, "y": u}
    c = res["cobrinha"]
    ax, tr = c["direcao"], c["transversal"]
    al = c["alcance"]
    longe = lambda *v: max(x for x in v if x is not None)                # noqa: E731
    return {ax: longe(al["u-"], al["u+"]), tr: longe(al["t-"], al["t+"])}


def ancoragem(res):
    """Ancoragem das barras de colapso além de C'' em cada direção: dict(direcao -> dict(ult, a, lb, disponivel,
    ok, minimo)), a = distância da face a C'' e minimo = col_ext necessário (a + lb)."""
    p, d = res["p"], res["d"]
    lb = lb_basico(p["col_bitola"], p["fck"])
    out = {}
    for direcao, ult in ultima_linha(res).items():
        a = ult + 2 * d
        disp = p["col_ext"] - a
        out[direcao] = dict(ult=ult, a=a, lb=lb, disponivel=disp, ok=disp >= lb - 1e-6, minimo=a + lb)
    return out


def esforco(p):
    """A combinação de maior força Z importada do TQS (característica, tf) ou None."""
    es = (p.get("tqs") or {}).get("esforcos") or []
    return max(es, key=lambda e: e["fz"]) if es else None


def capacidade(p):
    """Verificação de As·fyd >= 1,5·FSd com as cargas do TQS: dict(n, fk, fsd, as_nec, as_ef, ok) ou None."""
    g = esforco(p)
    if not g:
        return None
    fk = g["fz"] * TF_KN
    fsd = GAMA_F_CCP * fk
    as_nec = 1.5 * fsd / FYD
    # cada barra conta uma vez por face que cruza: duas no interno; uma na perpendicular à borda (faceando ou recuada)
    as_ef = sum(b["quant"] * b["faces"] for b in detalhar(p)) * area(p["col_bitola"])
    return dict(n=g["n"], titulo=g["titulo"], fk=fk, fsd=fsd, as_nec=as_nec, as_ef=as_ef, ok=as_ef >= as_nec - 1e-9)


def sugerir(res, minimo_face=2, arred=5.0):
    """Colapso sugerido para o pilar, com a bitola atual: nº de barras por face pelas cargas do TQS (se houver),
    repartido na proporção dos lados (no mínimo `minimo_face` por face), e o comprimento além da face pela ancoragem
    além de C'' (a + lb, para cima a `arred`). Devolve (mudanças {chave: valor}, [textos])."""
    p = res["p"]
    mud, txt = {}, []
    cap = capacidade(p)
    if cap:
        a1 = area(p["col_bitola"])
        em_x, em_y = detalhar(p)                            # faces que cada barra cruza (2; 1 junto da borda)
        f_x, f_y = em_x["faces"], em_y["faces"]
        As = lambda nbx, nby: (nby * f_x + nbx * f_y) * a1               # noqa: E731
        n = max(math.ceil(cap["as_nec"] / (2 * a1) - 1e-9), 2 * minimo_face)
        bx, by = p["bx"], p["by"]
        n_bx = max(minimo_face, int(n * bx / (bx + by) + 0.5))
        n_by = max(minimo_face, n - n_bx)
        while As(n_bx, n_by) < cap["as_nec"] - 1e-9:
            if n_by * bx <= n_bx * by:                      # a face proporcionalmente menos armada
                n_by += 1
            else:
                n_bx += 1
        mud.update(col_n_face_bx=n_bx, col_n_face_by=n_by)
        txt.append(f"{n_bx} barras em cada face de {_br(bx)} e {n_by} em cada face de {_br(by)} ø{_br(p['col_bitola'])}"
                   f": As = {_br(As(n_bx, n_by), 2)} >= {_br(cap['as_nec'], 2)} cm2 "
                   f"(Fk = {_br(cap['fk'] / TF_KN, 2)} tf, comb. {cap['n']})")
    else:
        txt.append("sem cargas do TQS no pilar: só o comprimento pela ancoragem")
    anc = ancoragem(res)
    ext = math.ceil(max(v["minimo"] for v in anc.values()) / arred - 1e-9) * arred
    mud["col_ext"] = float(ext)
    a = max(v["a"] for v in anc.values())
    txt.append(f"{_br(ext)} cm além da face: C'' a {_br(a, 1)} cm + lb = {_br(anc['x']['lb'], 1)} cm")
    return mud, txt


def _br(v, casas=None):
    s = f"{v:.{casas}f}" if casas is not None else f"{v:g}"
    return s.replace(".", ",")
