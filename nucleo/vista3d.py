# -*- coding: utf-8 -*-
"""
Visualização 3D interativa do detalhamento de um pilar (página HTML com three.js), sem o TQS.

A estrutura, o carregamento do three.js embutido e a abertura numa janela própria vêm do app de vigas protendidas
(_apps/ProtensãoVigas/protensao_3d.py e protensao_3d.html), copiados e adaptados em 10/11/2026 (pedido do usuário:
"as mesmas propriedades do app de Vigas Protendidas"; CLAUDE.md, Independência). A página mostra:
- a laje translúcida (até a borda livre, quando há) e o pilar;
- cada ferro com a bitola real, na cor da posição (N1, N2...): cobrinhas, montagem e colapso progressivo; nos
  conectores, cada pente com os pinos, as cabeças e os trilhos;
- os contornos das linhas de pinos, o C'' da verificação do colapso e os cortes do desenho (A-A, B-B);
- escala vertical de 0,1x a 50x, vistas prontas (3D, planta, inferior, frontal, lateral e os cortes do desenho),
  posições liga/desliga, dados do ferro sob o mouse e uma seção móvel em x ou em y com o desenho 2D em escala real
  (aproximar com a roda, deslocar arrastando); o modelo pode ser cortado na seção.

Coordenadas: as do núcleo (cm, origem no canto inferior esquerdo do pilar, x na horizontal e y na vertical da
prancha) e z a partir da face inferior da laje. As alturas são as dos cortes da prancha (prancha_cobrinha.corte e
prancha_conectores.corte): cobrinha de cobrimento a cobrimento, montagem sobre as dobras de baixo, colapso na face
inferior; pinos a partir do cobrimento inferior, trilhos entre as cabeças de baixo.

A página leva embutido o three.js de vendor/three-0.169.0 (licença MIT) e abre sem internet; sem essa pasta, carrega
de cdn.jsdelivr.net.

Uso:  python visualizar_3d.py <projeto.json> [--saida PASTA] [--pilar TITULO] [--abrir]
"""
import datetime
import html
import json
import math
import os
import subprocess
import webbrowser
from pathlib import Path

from . import colapso as col
from .parametros import cobrimento_borda, posicao
from .textos import limpar_nome

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
MODELO_HTML = os.path.join(AQUI, "vista3d.html")
MARCA = "/*__DADOS__*/null"
MARCA_THREE = "<!--__THREE_LOCAL__-->"
# three.js 0.169.0 (licença MIT, vendor/three-0.169.0/LICENSE), de cdn.jsdelivr.net/npm/three@0.169.0
VENDOR = os.path.join(RAIZ, "vendor", "three-0.169.0")
THREE_LOCAL = (("three-src", "three.module.min.js"), ("three-orbit", "OrbitControls.js"),
               ("three-css2d", "CSS2DRenderer.js"))
MARGEM = 15.0                     # laje além da armadura, nos lados sem borda livre (cm)


def _r2(v):
    return round(float(v), 2) + 0.0                     # + 0.0: sem o "-0.0"


def _bit(v):
    return f"{v:g}".replace(".", ",")


def _face(nome):
    """Nome da face como no texto: "face de baixo", "face direita"."""
    return "face " + {"baixo": "de baixo", "cima": "de cima"}.get(nome, nome)


def _cm(v):
    s = f"{round(v, 1):g}"
    return s.replace(".", ",")


def _recortar(pts, x0, x1, y0, y1):
    """Pedaços de uma polilinha (x, y, z) dentro do retângulo [x0, x1] x [y0, y1] (Liang-Barsky por trecho)."""
    pedacos, atual = [], []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t0, t1 = 0.0, 1.0
        ok = True
        for p_, q_ in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
            if abs(p_) < 1e-12:
                if q_ < 0:
                    ok = False
                    break
                continue
            t = q_ / p_
            if p_ < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
        if not ok or t0 > t1:
            if atual:
                pedacos.append(atual)
                atual = []
            continue
        pa = [a[k] + (b[k] - a[k]) * t0 for k in range(3)]
        pb = [a[k] + (b[k] - a[k]) * t1 for k in range(3)]
        if not atual:
            atual = [pa]
        atual.append(pb)
        if t1 < 1.0 - 1e-9:
            pedacos.append(atual)
            atual = []
    if atual:
        pedacos.append(atual)
    return [[[_r2(v) for v in q] for q in pd] for pd in pedacos if len(pd) > 1]


def _contorno(bx, by, ax, ay, z, n=12):
    """Retângulo de cantos em quarto de elipse (semieixos ax e ay) afastado ax das faces de x e ay das de y."""
    pts = []
    for cx, cy, a0 in ((bx, by, 0.0), (0.0, by, 90.0), (0.0, 0.0, 180.0), (bx, 0.0, 270.0)):
        for i in range(n + 1):
            a = math.radians(a0 + 90.0 * i / n)
            pts.append((cx + ax * math.cos(a), cy + ay * math.sin(a), z))
    pts.append(pts[0])
    return pts


class _Montador:
    """Grupos (as posições da legenda) e elementos (cada barra, pino, cabeça ou trilho, como polilinha com raio)."""

    def __init__(self):
        self.grupos, self.elems = [], []

    def grupo(self, ident, det, tipo):
        self.grupos.append(dict(id=ident, det=det, tipo=tipo))
        return len(self.grupos) - 1

    def elem(self, g, tipo, pts, r, texto, plano=None):
        e = dict(g=g, k=tipo, r=round(r, 3), p=[[_r2(v) for v in q] for q in pts], t=texto)
        if plano:
            e["pl"] = plano
        self.elems.append(e)


def _ferros(res, tipo):
    return [f for f in res["ferros"] if f["tipo"] == tipo]


def _cobrinha(res, m):
    p, c = res["p"], res["cobrinha"]
    ax, tr = c["direcao"], c["transversal"]
    xy = (lambda u, t: (u, t)) if ax == "x" else (lambda u, t: (t, u))     # noqa: E731
    h, ci, cs = p["h_laje"], p["c_inf"], p["c_sup"]
    fc, fm = p["cob_bitola"] / 10.0, p["mont_bitola"] / 10.0
    z = {"inf": ci + fc / 2, "sup": h - cs - fc / 2}
    # posição de cada peça: as posições agrupam as peças de mesma forma (cobrinha.detalhar), na ordem dos ferros
    formas = {}
    for g, fe in zip(c["posicoes"], _ferros(res, "cobrinha")):
        pc = next(x for x in c["pecas"] if x["pontos"] == g["pontos"])
        gi = m.grupo(f"N{fe['pos']}", f"{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} · {fe['descricao']}",
                     "cobrinha")
        formas[pc["forma"]] = (gi, fe)
    for pc in c["pecas"]:
        gi, fe = formas[pc["forma"]]
        pts = [(*xy(u, pc["linha"]), z[n]) for u, n in pc["pontos"]]
        txt = (f"N{fe['pos']} · {fe['descricao']}\n{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} cm · "
               f"{len(pc['pernas'])} pernas · linha {tr} = {_cm(pc['linha'])}")
        m.elem(gi, "barra", pts, fc / 2, txt, plano=[tr, _r2(pc["linha"])])
    # montagem: uma barra por fileira de pernas, sobre a dobra de baixo
    por_comp = {}
    for g, fe in zip(c["mont_posicoes"], _ferros(res, "montagem")):
        por_comp[g["comp"]] = (m.grupo(f"N{fe['pos']}", f"{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} · "
                                       f"{fe['descricao']}", "montagem"), fe)
    zm = ci + fc + fm / 2
    for b in c["montagem"]:
        gi, fe = por_comp[b["comp"]]
        txt = (f"N{fe['pos']} · {fe['descricao']}\n{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} cm · "
               f"fileira {ax} = {_cm(b['fileira'])}")
        m.elem(gi, "barra", [(*xy(b["pos"], b["ini"]), zm), (*xy(b["pos"], b["fim"]), zm)], fm / 2, txt)
    # colapso: as barras paralelas às cobrinhas na face inferior; as transversais sobre as dobras de baixo
    fcol = p["col_bitola"] / 10.0
    return {ax: ci + fcol / 2, tr: ci + fc + fcol / 2}


def _conectores(res, m):
    p, c = res["p"], res["conectores"]
    z0, e = p["c_inf"], p["con_cabeca_esp"]
    pino = c["pino"]
    L, D, rf = pino["comprimento_mm"] / 10.0, pino["cabeca_mm"] / 10.0, pino["bitola"] / 20.0
    tr = c["trilhos"]
    wt, at = tr["bitola"] / 10.0, tr["afast"]
    s0, sr = p["con_s0"], p["con_sr"]
    grupos = {}
    for t in c["tipos"]:
        det = (f"{t['quant']} pente(s) · {t['n_pinos']} ø{_bit(pino['bitola'])} com {_bit(pino['comprimento_mm'])} mm "
               f"(cabeça {_bit(pino['cabeca_mm'])} mm) + {tr['quant']} trilhos ø{_bit(tr['bitola'])}")
        grupos[t["n_pinos"]] = (m.grupo(t["nome_bloco"], det, "pente"), t)
    for k, pt in enumerate(c["pentes"], 1):
        gi, t = grupos[pt["n_pinos"]]
        a = math.radians(pt["ang"])
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        onde = {"face": _face(pt["face"]), "canto": pt["face"], "construtiva": f"linha construtiva, {_face(pt['face'])}"}
        base = f"Pente {k} ({t['nome_bloco']}) · {onde.get(pt['tipo'], pt['face'])}"
        # plano do pente (para o duplo clique levar a seção até ele): só os paralelos a x ou a y
        plano = ["y", _r2(pt["y"])] if abs(dy) < 1e-9 else (["x", _r2(pt["x"])] if abs(dx) < 1e-9 else None)
        for i, (x, y) in enumerate(pt["pinos"]):
            dist = s0 + i * sr
            txt = (f"{base}\npino {i + 1} de {pt['n_pinos']} · ø{_bit(pino['bitola'])} com "
                   f"{_bit(pino['comprimento_mm'])} mm · a {_cm(dist)} cm da face")
            m.elem(gi, "pino", [(x, y, z0), (x, y, z0 + L)], rf, txt, plano)
            for za, zb in ((z0, z0 + e), (z0 + L - e, z0 + L)):
                m.elem(gi, "cabeca", [(x, y, za), (x, y, zb)], D / 2,
                       f"{base}\ncabeça do pino {i + 1}: ø{_bit(pino['cabeca_mm'])} mm, {_cm(e)} cm", plano)
        (x1, y1), (x2, y2) = pt["pinos"][0], pt["pinos"][-1]
        for lado in ((-1, 1) if tr["quant"] >= 2 else (1,))[:max(1, tr["quant"])]:
            o = (nx * at * lado, ny * at * lado)
            pts = [(x1 - dx * D / 2 + o[0], y1 - dy * D / 2 + o[1], z0 + wt / 2),
                   (x2 + dx * D / 2 + o[0], y2 + dy * D / 2 + o[1], z0 + wt / 2)]
            m.elem(gi, "trilho", pts, wt / 2, f"{base}\ntrilho ø{_bit(tr['bitola'])} (liga os pinos, entre as cabeças "
                                              f"de baixo)")
    # colapso: N em x na face inferior, sobre as cabeças de baixo; o de y sobre ele (como no corte A-A)
    fcol = p["col_bitola"] / 10.0
    zi = z0 + e
    return {"x": zi + fcol / 2, "y": zi + fcol + fcol / 2}


def _montagem_conectores(res, m):
    """Montagem opcional, sobre os trilhos (depois do colapso, na ordem dos ferros)."""
    p, c = res["p"], res["conectores"]
    fm = p["mont_bitola"] / 10.0
    zm = p["c_inf"] + c["trilhos"]["bitola"] / 10.0 + fm / 2
    por_grupo = {}
    for fe in _ferros(res, "montagem"):
        por_grupo[fe["subtipo"]] = (m.grupo(f"N{fe['pos']}", f"{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} · "
                                            f"{fe['descricao']}", "montagem"), fe)
    for b in c["montagem"]:
        gi, fe = por_grupo[b["grupo"]]
        txt = (f"N{fe['pos']} · {fe['descricao']}\n{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} cm · "
               f"a {_cm(b['dist'])} cm da {_face(b['face'])}")
        m.elem(gi, "barra", [(*b["p1"], zm), (*b["p2"], zm)], fm / 2, txt)


def _colapso(res, m, zcol):
    p = res["p"]
    fcol = p["col_bitola"] / 10.0
    alt = col.altura_gancho(p["col_bitola"])
    for g, fe in zip(res["colapso"], _ferros(res, "colapso")):
        gi = m.grupo(f"N{fe['pos']}", f"{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} · {fe['descricao']}",
                     "colapso")
        z = zcol[g["direcao"]]
        zg = z + alt - fcol                      # topo do gancho de 90° (pelo eixo)
        for pos in g["pos"]:
            xy = (lambda s, pos=pos: (s, pos)) if g["direcao"] == "x" else (lambda s, pos=pos: (pos, s))  # noqa
            pts = [(*xy(g["ini"]), z), (*xy(g["fim"]), z)]
            if g["ganchos"][0]:
                pts.insert(0, (*xy(g["ini"]), zg))
            if g["ganchos"][1]:
                pts.append((*xy(g["fim"]), zg))
            txt = (f"N{fe['pos']} · {fe['descricao']}\n{fe['quant']} ø{_bit(fe['bitola'])} C={fe['comp']} cm · "
                   f"de {g['direcao']} = {_cm(g['ini'])} a {_cm(g['fim'])}")
            m.elem(gi, "barra", pts, fcol / 2, txt)


def _cortes_desenho(res):
    """Os cortes da prancha: [dict(letra, eixo, v)], eixo = a coordenada constante do plano."""
    if "cobrinha" in res:
        from .prancha_cobrinha import Prancha
        pr = Prancha(res)
        tr = res["cobrinha"]["transversal"]
        return [dict(letra="A", eixo=tr, v=_r2(pr.t_frente)), dict(letra="B", eixo=tr, v=_r2(pr.t_lado))]
    from .prancha_conectores import Prancha
    return [dict(letra="A", eixo="y", v=_r2(Prancha(res).y_corte))]


def dados_3d(res, projeto=""):
    """Geometria e dados do pilar para a página (cm). res = nucleo.detalhe.detalhar(par), sem erros."""
    if res["erros"]:
        raise ValueError("Corrija antes de ver em 3D:\n\n" + "\n".join(res["erros"]))
    p = res["p"]
    m = _Montador()
    if "cobrinha" in res:
        _colapso(res, m, _cobrinha(res, m))
    else:
        _colapso(res, m, _conectores(res, m))
        _montagem_conectores(res, m)
    bx, by, h = p["bx"], p["by"], p["h_laje"]
    # laje: até a borda livre ou MARGEM além da armadura
    xs = [q[0] for e in m.elems for q in e["p"]] + [0.0, bx]
    ys = [q[1] for e in m.elems for q in e["p"]] + [0.0, by]
    lim = [min(xs) - MARGEM, max(xs) + MARGEM, min(ys) - MARGEM, max(ys) + MARGEM]
    bordas = []
    for eixo, lados, k in (("x", ("esquerda", "direita"), 0), ("y", ("baixo", "cima"), 2)):
        lado, a = p.get(f"borda_{eixo}") or "", p.get(f"dist_borda_{eixo}") or 0.0
        if lado == lados[0]:
            lim[k] = -a
        elif lado == lados[1]:
            lim[k + 1] = (bx if eixo == "x" else by) + a
        if lado:
            bordas.append(dict(lado=lado, a=_r2(a)))
    lim = [_r2(v) for v in lim]
    # contornos: linhas de pinos (conectores) e o C'' da verificação do colapso (2d além da última linha)
    contornos = []
    if "conectores" in res:
        for s in res["conectores"]["contornos"]:
            contornos += _recortar(_contorno(bx, by, s, s, h / 2), *lim)
    anc = col.ancoragem(res)
    ax_, ay_ = anc["x"]["a"], anc["y"]["a"]
    cpp = _recortar(_contorno(bx, by, ax_, ay_, 0.05), *lim)
    d = res["d"]
    if "cobrinha" in res:
        c = res["cobrinha"]
        solucao = f"cobrinhas em {c['direcao']}, {c['n_linhas']} linhas, {c['n_pecas']} peças"
    else:
        c = res["conectores"]
        solucao = f"{c['texto_pentes']}, {c['inclinados']} inclinado(s) por canto"
    return dict(
        projeto=projeto, titulo=p["titulo"], repeticoes=p["repeticoes"], posicao=posicao(p),
        solucao=p["solucao"], resumo_solucao=solucao,
        bx=bx, by=by, h=h, c_sup=p["c_sup"], c_inf=p["c_inf"], d=_r2(d), cb=cobrimento_borda(p),
        laje=lim, bordas=bordas, pilar_ext=_r2(max(40.0, 1.2 * h)),
        grupos=m.grupos, elems=m.elems, contornos=contornos,
        cpp=dict(ax=_r2(ax_), ay=_r2(ay_), linhas=cpp), cortes=_cortes_desenho(res),
        ferros=[dict(pos=f["pos"], quant=f["quant"], bitola=f["bitola"], comp=f["comp"], descricao=f["descricao"])
                for f in res["ferros"]],
        avisos=[f"{t} ({ref})" for tipo, t, ref in res["verificacoes"] if tipo == "aviso"],
        gerado=datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))


def _three_local():
    """three.js de vendor/ como blocos de texto da página (ela os importa por blob e abre sem internet). Vazio se
    faltar algum arquivo: a página usa o cdn.jsdelivr.net."""
    blocos = []
    for ident, arq in THREE_LOCAL:
        caminho = os.path.join(VENDOR, arq)
        if not os.path.exists(caminho):
            return ""
        with open(caminho, encoding="utf-8") as f:
            js = f.read()
        if "</script" in js.lower() or "<!--" in js:          # encerrariam o bloco <script> no meio do código
            return ""
        blocos.append(f'<script type="text/plain" id="{ident}">\n{js}\n</script>')
    return "\n".join(blocos)


def html_3d(dados):
    with open(MODELO_HTML, encoding="utf-8") as f:
        modelo = f.read()
    js = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\u0021--")
    titulo = html.escape(f"{dados['titulo']} - punção 3D")
    return modelo.replace(MARCA, js).replace("__TITULO__", titulo).replace(MARCA_THREE, _three_local())


def nome_arquivo(p):
    return limpar_nome(f"PUN_{p['titulo']}") + "-3D.html"


def gravar(res, pasta, projeto=""):
    """Grava PUN_<pilar>-3D.html na pasta. Devolve o caminho. ValueError com os erros do pilar."""
    dados = dados_3d(res, projeto)
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome_arquivo(res["p"]))
    Path(caminho).write_text(html_3d(dados), encoding="utf-8")
    return caminho


def _navegador_app():
    """Edge ou Chrome (abrem a página numa janela própria, sem barra de endereço), ou None."""
    bases = [os.environ.get(k) for k in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    for rel in (("Microsoft", "Edge", "Application", "msedge.exe"), ("Google", "Chrome", "Application", "chrome.exe")):
        for base in bases:
            if base and os.path.exists(os.path.join(base, *rel)):
                return os.path.join(base, *rel)
    return None


def abrir(caminho):
    """Abre a página numa janela própria (modo aplicativo do Edge ou do Chrome) ou no navegador padrão."""
    uri = Path(caminho).resolve().as_uri()
    exe = _navegador_app()
    if exe:
        try:
            subprocess.Popen([exe, f"--app={uri}", "--window-size=1500,920"])
            return
        except OSError:
            pass
    webbrowser.open(uri)
