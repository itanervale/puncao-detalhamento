# -*- coding: utf-8 -*-
"""
Importação do TQS, parte sem o TQS: interpreta o que o leitor (dwg_tqs/leitor_tqs.py) trouxe de uma planta e monta
os pilares do projeto.

- combinações da grelha (o <grelha>.GRE, em texto): só as de ELU entram (título começando por "ELU"; regra do
  usuário de 09/11/2026);
- reações por pilar da listagem do FGREANA ("Reações nos apoio - Pilares - Sistema GLOBAL"): momento X, momento Y
  (tf·m) e força Z (tf), características (a grelha soma os casos com coeficiente 1,0). Ficam só para conferência:
  o app detalha, não dimensiona;
- posição do pilar na laje: interno quando nenhuma borda livre, viga ou contorno fica a menos de 2d da face (o
  contorno C' não é cortado); borda com um lado, canto com dois lados vizinhos. O app só detalha os internos;
- fck: o concreto das lajes da planta (ou o de vigas e lajes do edifício), para o lb do colapso;
- repetições: as da planta no TQS (pavimento tipo repetido 5 vezes = 5X);
- seção: só a retangular entra; girada de 0° ou 90°, bx e by saem da poligonal; em outro ângulo, nos eixos do pilar;
- abertura (furo) a menos de 8d da face (NBR 6118:2026, 19.5.2.3 e Figura 19.6) e capitel no pilar: avisos, porque o
  app ainda não os detalha.

Unidades do TQS: cm, tf e tf·m.
"""
import math
import re
from collections import Counter

from .parametros import PADROES, altura_util, normalizar

BORDAS = ("borda_x", "borda_y", "dist_borda_x", "dist_borda_y")         # pilar de borda ou de canto (E9)
# o que a importação escreve no pilar
GEOMETRIA = ("titulo", "bx", "by", "h_laje", "c_sup", "c_inf", "repeticoes", "fck") + BORDAS
TIPOS_SECAO = {0: "retangular", 1: "L", 2: "U", 3: "circular", 4: "poligonal", 5: "não padrão"}
LADOS = ("esquerda", "baixo", "direita", "cima")
TOL = 0.05                                                           # cm


# ------------------------------------------------------------------ grelha
def combinacoes(texto_gre):
    """[(n, título)] das COMBIN do .GRE. Cada uma é uma linha "COMBIN  n ..." seguida de "  ncasos  título"."""
    out = []
    linhas = texto_gre.splitlines()
    for k, lin in enumerate(linhas):
        m = re.match(r"^COMBIN\s+(\d+)", lin)
        if m and k + 1 < len(linhas):
            t = re.match(r"^\s*\d+\s+(.*?)\s*$", linhas[k + 1])
            out.append((int(m.group(1)), t.group(1) if t else ""))
    return out


def combinacoes_elu(texto_gre):
    return [(n, t) for n, t in combinacoes(texto_gre) if t.upper().startswith("ELU")]


def reacoes(listagem):
    """Reações por pilar de uma listagem do FGREANA -> {pilar: (Mx, My, Fz)} (tf·m, tf·m, tf)."""
    i = listagem.find("Pilares - Sistema GLOBAL")
    if i < 0:
        return {}
    out = {}
    for lin in listagem[i:].splitlines():
        if lin.strip().startswith(("-----", "Total")):
            if out:
                break
            continue
        m = re.match(r"^(\S+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$", lin)
        if m:
            out[m.group(1)] = tuple(float(m.group(j)) for j in (2, 3, 4))
    return out


def governante(esforcos):
    """A combinação de maior força Z (a que mais carrega o pilar), ou None."""
    return max(esforcos, key=lambda e: e["fz"]) if esforcos else None


# ------------------------------------------------------------------ geometria
def _dist_ponto_seg(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def _cruzam(a, b, c, d):
    def o(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    return o(a, b, c) * o(a, b, d) < 0 and o(c, d, a) * o(c, d, b) < 0


def _dist_seg_seg(a, b, c, d):
    if _cruzam(a, b, c, d):
        return 0.0
    return min(_dist_ponto_seg(a, c, d), _dist_ponto_seg(b, c, d), _dist_ponto_seg(c, a, b), _dist_ponto_seg(d, a, b))


def _dentro(p, polig):
    x, y, dentro = p[0], p[1], False
    n = len(polig)
    for i in range(n):
        (x1, y1), (x2, y2) = polig[i], polig[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def _fechar(polig):
    pts = [tuple(map(float, p)) for p in polig]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts


def dist_poligono_seg(polig, a, b):
    """Menor distância entre um polígono (o pilar) e um segmento; 0 se o segmento toca ou entra no polígono."""
    pts = _fechar(polig)
    if _dentro(a, pts) or _dentro(b, pts):
        return 0.0
    n = len(pts)
    return min(_dist_seg_seg(pts[i], pts[(i + 1) % n], a, b) for i in range(n))


def dist_poligonos(p1, p2):
    q2 = _fechar(p2)
    if any(_dentro(p, q2) for p in _fechar(p1)) or any(_dentro(p, _fechar(p1)) for p in q2):
        return 0.0
    n = len(q2)
    return min(dist_poligono_seg(p1, q2[i], q2[(i + 1) % n]) for i in range(n))


def caixa(polig):
    xs, ys = [p[0] for p in polig], [p[1] for p in polig]
    return min(xs), min(ys), max(xs), max(ys)


def _lado(polig, a, b):
    """Lado do pilar (esquerda, baixo, direita, cima) voltado para o segmento: pela projeção do centro do pilar no
    segmento, comparada com a meia largura e a meia altura do pilar."""
    x0, y0, x1, y1 = caixa(polig)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((cx - a[0]) * dx + (cy - a[1]) * dy) / L2))
    qx, qy = a[0] + t * dx, a[1] + t * dy
    u = (qx - cx) / max((x1 - x0) / 2, TOL)
    v = (qy - cy) / max((y1 - y0) / 2, TOL)
    if abs(u) >= abs(v):
        return "direita" if u > 0 else "esquerda"
    return "cima" if v > 0 else "baixo"


def posicao(polig, bordas, d):
    """Posição do pilar: ("interno" | "borda" | "canto" | "verificar", {lado: (distância à face, origem)}).
    `bordas`: [(x1, y1, x2, y2, folga, origem)], folga = o que se desconta da distância (meia largura da viga).
    Uma borda conta quando fica a menos de 2d da face do pilar."""
    lados = {}
    for x1, y1, x2, y2, folga, origem in bordas:
        dist = max(dist_poligono_seg(polig, (x1, y1), (x2, y2)) - folga, 0.0)
        if dist < 2 * d - TOL:
            lado = _lado(polig, (x1, y1), (x2, y2))
            if lado not in lados or dist < lados[lado][0]:
                lados[lado] = (dist, origem)
    n = len(lados)
    if n == 0:
        return "interno", lados
    if n == 1:
        return "borda", lados
    if n == 2:
        a, b = (LADOS.index(k) for k in lados)
        return ("canto" if (a - b) % 2 else "verificar"), lados
    return "verificar", lados


def dimensoes(pil):
    """(bx, by, aviso) de um pilar retangular do leitor; bx na horizontal da planta do TQS."""
    ang = (pil.get("ang") or 0.0) % 180
    if min(abs(ang), abs(ang - 90), abs(ang - 180)) < 0.01:
        x0, y0, x1, y1 = caixa(_fechar(pil["polig"]))
        return round(x1 - x0, 2), round(y1 - y0, 2), ""
    return float(pil["b1"]), float(pil["h1"]), (f"pilar girado de {pil['ang']:g}°: bx e by nos eixos do pilar "
                                                f"(b = {pil['b1']:g}, h = {pil['h1']:g})")


def espessura(lajes):
    """h das lajes da planta: (h, aviso). Com espessuras diferentes, a mais comum e um aviso (a interface do TQS
    não dá o contorno de cada laje para achar a do pilar)."""
    hs = [float(lj["h"]) for lj in lajes if lj.get("h")]
    if not hs:
        return None, "a planta não tem lajes"
    cont = Counter(hs)
    h = cont.most_common(1)[0][0]
    if len(cont) > 1:
        return h, ("lajes com espessuras diferentes (" + ", ".join(f"{v:g}" for v in sorted(cont)) +
                   f" cm): h = {h:g} (a mais comum); confira a laje do pilar")
    return h, ""


def cobrimentos(dados, protendida=False):
    c = dados.get("cobrimentos") or {}
    if protendida:
        return c.get("protendida_sup"), c.get("protendida_inf")
    return c.get("sup"), c.get("inf")


# ------------------------------------------------------------------ pilares
def analisar(dados, base=None):
    """Uma linha por pilar da planta lida pelo leitor, com o pilar pronto para o projeto (`par`), a situação e os
    esforços. `base` é o pilar de onde vêm os demais parâmetros (o atual da janela)."""
    base = dict(base or {})
    h, aviso_h = espessura(dados.get("lajes", []))
    prot = any(lj.get("protendida") for lj in dados.get("lajes", []))
    c_sup, c_inf = cobrimentos(dados, prot)
    bordas = [tuple(b) for b in dados.get("bordas", [])]
    furos = dados.get("furos", [])
    capiteis = dados.get("capiteis", [])
    esf = (dados.get("grelha") or {}).get("esforcos", {})
    out = []
    for pil in dados.get("pilares", []):
        titulo = pil["titulo"] or f"P{pil.get('numero', '')}"
        tipo = TIPOS_SECAO.get(pil.get("tipo"), str(pil.get("tipo")))
        linha = dict(titulo=titulo, secao=tipo, polig=pil["polig"], esforcos=esf.get(titulo, []), avisos=[],
                     suportado=True, posicao="", lados={}, par=None, d=None)
        x0, y0, x1, y1 = caixa(_fechar(pil["polig"]))
        linha["centro"] = ((x0 + x1) / 2, (y0 + y1) / 2)
        if tipo != "retangular":
            linha.update(suportado=False, motivo=f"seção {tipo}: o app só detalha pilares retangulares")
            linha["dim"] = f"{pil['b1']:g}" + (f" x {pil['h1']:g}" if tipo != "circular" else " (diâmetro)")
            out.append(linha)
            continue
        bx, by, av = dimensoes(pil)
        girado = bool(av)
        if av:
            linha["avisos"].append(av)
        linha["dim"] = f"{bx:g} x {by:g}"
        par = {k: v for k, v in base.items() if k not in GEOMETRIA and k != "tqs"}
        par.update(titulo=titulo, bx=bx, by=by, repeticoes=max(int(dados.get("repeticao") or 1), 1))
        if h is not None:
            par["h_laje"] = h
        if aviso_h:
            linha["avisos"].append(aviso_h)
        if c_sup is not None:
            par["c_sup"] = c_sup
        if c_inf is not None:
            par["c_inf"] = c_inf
        if dados.get("fck"):
            par["fck"] = float(dados["fck"])
        p, erros = normalizar(par)
        d = altura_util(p) if not erros else None
        linha["d"] = d
        if h is None:
            linha.update(suportado=False, motivo="a planta não tem lajes")
        elif d:
            classe, lados = posicao(pil["polig"], bordas, d)
            linha.update(posicao=classe, lados=lados)
            if classe != "interno":
                lista = ", ".join(f"{k} a {v[0]:.0f} cm ({v[1]})" for k, v in lados.items())
                if classe == "verificar":
                    linha["avisos"].append(f"bordas ou vigas em lados opostos: {lista} (menos de 2d = {2 * d:.0f} "
                                           "cm); o app detalha uma borda livre por direção: importado como interno")
                elif girado:
                    linha["avisos"].append(f"pilar de {classe} girado: {lista}; as bordas não foram passadas ao "
                                           "pilar (importado como interno)")
                else:
                    _bordas_no_pilar(par, lados)
                    linha["bordas"] = True
                    linha["avisos"].append(f"pilar de {classe}: {lista}, a menos de 2d = {2 * d:.0f} cm da face; "
                                           "passado ao pilar como borda livre")
                    if par.get("solucao", PADROES["solucao"]) == "conectores":
                        par["solucao"] = "cobrinha"
                        linha["avisos"].append("conectores em pilar de borda ou de canto ainda não implementados: "
                                               "cobrinha")
            for f in furos:
                df = dist_poligonos(pil["polig"], f["polig"])
                if df < 8 * d - TOL:
                    linha["avisos"].append(f"abertura a {df:.0f} cm da face (menos de 8d = {8 * d:.0f} cm): o app "
                                           "ainda não considera aberturas")
            for c in capiteis:
                if dist_poligonos(pil["polig"], c["polig"]) < TOL:
                    linha["avisos"].append(f"capitel de {c.get('h', 0):g} cm no pilar: o app ainda não detalha "
                                           "capitéis")
        if erros:
            linha["avisos"] += erros
        par["tqs"] = dict(edificio=dados.get("edificio"), planta=dados.get("planta"), numero=pil.get("numero"),
                          centro=[round(c, 2) for c in linha["centro"]], posicao=linha["posicao"],
                          secao=f"{pil['b1']:g} x {pil['h1']:g}", angulo=pil.get("ang", 0.0),
                          avisos=list(linha["avisos"]), esforcos=linha["esforcos"],
                          grelha=(dados.get("grelha") or {}).get("nome"))
        linha["par"] = par
        out.append(linha)
    return out


LIMITES = (("cob_s0", 0.5), ("cob_s", 0.75), ("cob_s_x", 0.75), ("cob_s_y", 0.75), ("con_s0", 0.5), ("con_sr", 0.75))
ROTULOS = dict(cob_s0="s0 da cobrinha", cob_s="espaçamento da malha", cob_s_x="espaçamento em x",
               cob_s_y="espaçamento em y", con_s0="s0 dos conectores", con_sr="sr dos conectores")


def ajustar_limites(par):
    """Traz s0 e os espaçamentos para os limites da NBR 6118:2026 (19.5.3.3 e Figura 19.9): s0 <= 0,5d e sr <= 0,75d,
    arredondados para baixo ao centímetro (o TQS arredonda cada trecho do ferro genérico ao cm; no modelo, d = 23
    dá 11 e 17). Só diminui o que passa do limite; o número de linhas não muda. Vale para as duas soluções, para a
    troca de solução depois não voltar a passar. Devolve (pilar, [mudanças em texto])."""
    p, erros = normalizar(par)
    if erros:
        return dict(par), []
    d = altura_util(p)
    novo, mud = dict(par), []
    for k, f in LIMITES:
        v = p.get(k)
        if v is None or (k in ("cob_s_x", "cob_s_y") and par.get(k) is None):
            continue                                       # s_x e s_y vazios seguem o cob_s
        lim = math.floor(f * d + 1e-9)
        if v > lim + 1e-9:
            novo[k] = float(lim)
            mud.append(f"{ROTULOS[k]} {v:g} -> {lim} ({'0,5' if f == 0.5 else '0,75'}d = "
                       f"{f * d:.2f})".replace(".", ","))
    return novo, mud


def _bordas_no_pilar(par, lados):
    """Passa ao pilar as bordas livres (ou as vigas) a menos de 2d da face: uma por direção (E9)."""
    for lado, (dist, _origem) in lados.items():
        eixo = "x" if lado in ("esquerda", "direita") else "y"
        par[f"borda_{eixo}"] = lado
        par[f"dist_borda_{eixo}"] = round(dist, 1)


def selecao_padrao(linha):
    """Marcados na abertura do diálogo: os internos e, com as bordas passadas ao pilar, os de borda e de canto
    (Q17), sem aviso de abertura ou capitel."""
    return (linha["suportado"] and (linha["posicao"] == "interno" or linha.get("bordas", False))
            and not any(a.startswith(("abertura", "capitel")) for a in linha["avisos"]))


def mesclar(pilares, novos, atualizar=True):
    """Junta os pilares importados ao projeto. Com o mesmo título: atualiza só a geometria e a origem (`tqs`),
    mantendo o detalhamento escolhido (`atualizar`), ou pula. Devolve (pilares, n_novos, n_atualizados, pulados)."""
    pilares = [dict(p) for p in pilares]
    por_titulo = {str({**PADROES, **p}["titulo"]): j for j, p in enumerate(pilares)}
    n_novos = n_atual = 0
    pulados = []
    for q in novos:
        j = por_titulo.get(str(q["titulo"]))
        if j is None:
            pilares.append(dict(q))
            por_titulo[str(q["titulo"])] = len(pilares) - 1
            n_novos += 1
        elif atualizar:
            pilares[j].update({k: q[k] for k in (*GEOMETRIA, "tqs") if k in q})
            for k in BORDAS:                              # o pilar que deixou de ser de borda volta a interno
                if k not in q:
                    pilares[j].pop(k, None)
            n_atual += 1
        else:
            pulados.append(q["titulo"])
    return pilares, n_novos, n_atual, pulados


def resumo_esforcos(esforcos):
    """Texto curto da combinação governante: "comb. 10 (ELU1/...): Fz 53,12 tf, Mx 0,50, My -5,13 tf·m"."""
    g = governante(esforcos)
    if not g:
        return "sem esforços da grelha"
    br = lambda v: f"{v:.2f}".replace(".", ",")              # noqa: E731
    return f"comb. {g['n']} ({g['titulo']}): Fz {br(g['fz'])} tf, Mx {br(g['mx'])}, My {br(g['my'])} tf·m"
