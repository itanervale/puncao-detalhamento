# -*- coding: utf-8 -*-
"""
E0: teste de gravação pela interface do TQS. Refaz cada desenho de referência a partir do despejo
(ferramentas/ler_modelo.py), sem copiar o arquivo:

- ferros inteligentes recriados com os atributos lidos (o TQS recalcula quantidade e comprimento);
- cotas recriadas como objetos IPOCOT pelos pontos de definição, com os níveis de cada uma;
- blocos definidos a partir da 1ª inserção e inseridos nas mesmas posições; o $CORTEA vem da biblioteca do TQS;
- demais linhas, polilinhas, círculos, arcos e textos no nível, estilo e cor originais.

Grava saidas/e0/REPLICA_<desenho>.DWG, PDF e DXF, lê de volta e compara com o despejo do modelo. Se a réplica
fica igual, o caminho de gravação (níveis, estilos, blocos, cotas, ferros) está validado para a E2 e a E4.

Uso:  python dwg_tqs/teste_gravacao.py [<despejo.json> ...]   (padrão: saidas/modelos/PUN_P02*.json)
Requer os despejos dos modelos (ferramentas/ler_modelo.py DesenhosReferencia/*.DWG).
"""
import glob
import json
import math
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from TQS import TQSDwg as T                                          # noqa: E402
from dwg_tqs import arquivo                                          # noqa: E402
from ferramentas import ler_modelo, comparar                         # noqa: E402
from nucleo.textos import txt_tqs                                    # noqa: E402

# Blocos da biblioteca do TQS: carregados pelo caminho sem a extensão, o bloco fica com o mesmo nome do modelo
# (com o caminho com extensão, ficaria "$CORTEA"; conferido em 03/11/2026).
BLOCOS_TQS = ("C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA",)
# Atributos dos ferros copiados do despejo (os demais não se aplicam ou são calculados pelo TQS).
# No modelo da cobrinha, C=450 = soma dos trechos pelo eixo: bendTotalLengthMode = bendBendLengthMode = 2 (soma
# simples) e bendRadiusDisplay = 0 (raio de dobra aplicado manualmente); com os padrões, o TQS dá 427 ou 473.
ATRIB_FERRO = ("bendType", "bendRadius", "bendTotalLengthMode", "bendBendLengthMode", "bendRadiusDisplay",
               "bendDimRadius", "bendDimPerimeter",
               "bendTickDisplay", "textHeigth", "distributionTextHeigth", "straightBarTextDirection",
               "straightBarTextPosition", "straightBarContinuous", "mirrorMode", "alternatingMode")


# --------------------------------------------------------------------------- leitura do despejo
def filhos(ents, i):
    """Entidades diretas do bloco/objeto que começa em ents[i] e o índice do fim dele."""
    prof, out, j = 0, [], i + 1
    while j < len(ents):
        t = ents[j]["t"]
        if t in ("Bloco", "Objeto"):
            if prof == 0:
                out.append(ents[j])
            prof += 1
        elif t in ("Fim de bloco", "Fim de objeto"):
            if prof == 0:
                return out, j
            prof -= 1
        elif prof == 0:
            out.append(ents[j])
        j += 1
    return out, j


def para_local(e, ins):
    """Entidade em coordenadas globais -> coordenadas do bloco (1ª inserção, escala positiva)."""
    a = math.radians(ins["ang"])
    c, s = math.cos(-a), math.sin(-a)
    sx, sy = ins["sx"], ins["sy"]

    def p(x, y):
        dx, dy = x - ins["x"], y - ins["y"]
        return [(c * dx - s * dy) / sx, (s * dx + c * dy) / sy]
    f = dict(e)
    if e.get("xy"):
        f["xy"] = [p(x, y) for x, y in e["xy"]]
    if "x" in e and e["t"] != "Bloco":
        f["x"], f["y"] = p(e["x"], e["y"])
    if "r" in e:
        f["r"] = e["r"] / abs(sx)
    if e["t"] == "Arco":
        f["a1"], f["a2"] = e["a1"] - ins["ang"], e["a2"] - ins["ang"]
    if e["t"] == "Texto":
        f["a"] = e["a"] - ins["ang"]
    return f


# --------------------------------------------------------------------------- desenho
def desenhar(dwg, e, niveis):
    d = dwg.draw
    n = e["n"]
    d.level = n
    d.style = e.get("s", -1) if e.get("s", -1) != niveis.get(str(n), {}).get("estilo") else -1
    d.color = e["c"] if e.get("c") not in (None, niveis.get(str(n), {}).get("cor")) else -1
    t = e["t"]
    if t == "Linha":
        (x1, y1), (x2, y2) = e["xy"][0], e["xy"][-1]
        d.Line(x1, y1, x2, y2)
    elif t in ("Polyline", "Curva"):
        d.PolyEnterXY([list(v) for v in e["xy"]])
        d.PolylineFilled() if e.get("fill") else d.Polyline()
    elif t == "Circulo":
        d.Circle(e["x"], e["y"], e["r"])
    elif t == "Arco":
        d.Arc(e["x"], e["y"], e["r"], e["a1"], e["a2"])
    elif t == "Texto":
        txt = txt_tqs(e["txt"].replace("\r", "").replace("\n", ""))
        if txt.strip():
            d.Text(e["x"], e["y"], e["h"], e["a"], txt)
    d.style, d.color = -1, -1


def definir_blocos(dwg, ents, niveis):
    feitos = set()
    for i, e in enumerate(ents):
        if e["t"] != "Bloco" or e["b"] in feitos:
            continue
        nome = e["b"]
        feitos.add(nome)
        if nome in BLOCOS_TQS:
            if dwg.draw.BlockLoadFromDwg(nome) != 0:
                print("  AVISO: bloco do TQS não carregado:", nome)
            continue
        inst = next((ents[k] for k in range(i, len(ents)) if ents[k]["t"] == "Bloco" and ents[k]["b"] == nome
                     and ents[k]["sx"] > 0 and ents[k]["sy"] > 0), e)
        conteudo, _ = filhos(ents, ents.index(inst))
        dwg.draw.BlockOpen(nome, 0.0, 0.0)
        for f in conteudo:
            if f["t"] not in ("Bloco", "Objeto"):
                desenhar(dwg, para_local(f, inst), niveis)
        dwg.draw.BlockClose()


def nome_bloco(dwg_nome):
    """O BlockLoadFromDwg dá ao bloco o nome do arquivo sem a extensão; o modelo o guarda com o caminho."""
    return dwg_nome


def texto_tqs_medida(med):
    """Como o TQS escreve a medida de uma cota: inteiro, ou com uma casa quando há fração ("39.1", "37.5")."""
    t = f"{med:.1f}"
    return t[:-2] if t.endswith(".0") else t


def nota(dwg, e, filhos_nota, niveis):
    """Chamada com flecha: no modelo, objeto de cota com a polilinha terminando na flecha (ponta, asa, ponta, asa).
    Refeita como polilinha comum: o DimNote da interface também grava uma polilinha comum (flecha no 1º ponto), e
    depois dele o iterador em memória derruba o Python (testado em 03/11/2026)."""
    if not any(f["t"] == "Polyline" for f in filhos_nota):
        return False
    for f in filhos_nota:
        if f["t"] in ("Polyline", "Texto"):
            desenhar(dwg, f, niveis)
    return True


def cota(dwg, e, filhos_cota, niveis):
    """Refaz uma cota IPOCOT pelos pontos de definição (linhas de comprimento zero) e pelo símbolo."""
    pts = [f["xy"][0] for f in filhos_cota if f.get("xy") and f["xy"][0] == f["xy"][-1]]
    circ = sorted({(round(f["x"], 4), round(f["y"], 4)) for f in filhos_cota if f["t"] == "Circulo"})
    txt = [f for f in filhos_cota if f["t"] == "Texto"]
    linhas = [f for f in filhos_cota if f.get("xy") and f["xy"][0] != f["xy"][-1]]
    if not circ:
        return nota(dwg, e, filhos_cota, niveis)
    if len(pts) < 2 or len(circ) < 2:
        return False
    nv_lin = linhas[0]["n"] if linhas else 253
    arquivo.configurar_cotas(dwg, idmniv=txt[0]["n"] if txt else e["n"], idmnic=nv_lin, idmnil=nv_lin,
                             idmnib=nv_lin)
    (x1, y1), (x2, y2) = pts[0], pts[1]
    (cx1, cy1), (cx2, cy2) = circ[0], circ[-1]
    dm = dwg.dim
    if txt:
        valor = txt[0]["txt"].strip()
        if valor != texto_tqs_medida(math.hypot(cx2 - cx1, cy2 - cy1)):
            dm.dimtxu = txt_tqs(valor)          # texto fixo (ex.: "39" numa medida de 39,1)
    else:
        dm.dimtxu = " "
    ang_cota = math.degrees(math.atan2(cy2 - cy1, cx2 - cx1)) % 180
    ang_pts = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
    if abs(cy1 - cy2) < 1e-3:
        dm.DimHorizontal(x1, y1, x2, y2, cx1, cy1)
    elif abs(cx1 - cx2) < 1e-3:
        dm.DimVertical(x1, y1, x2, y2, cx1, cy1)
    elif min(abs(ang_cota - ang_pts), 180 - abs(ang_cota - ang_pts)) < 0.05:
        dm.DimAligned(x1, y1, x2, y2, cx1, cy1)
    else:                                       # cota inclinada num ângulo dado (os "39" entre pentes)
        dm.DimInclined(x1, y1, x2, y2, cx1, cy1, ang_cota)
    return True


def ferro(dwg, f, filhos_ferro=None):
    r = T.SmartRebar(dwg)
    r.type = f["type"]
    r.mark, r.quantity, r.multiplier = f["mark"], f["quantity"], f["multiplier"]
    r.diameter, r.spacing, r.cover = f["diameter"], f["spacing"], f["cover"]
    if f["type"] == T.ICPFRT:
        r.straightBarMainLength = f["straightBarMainLength"]
        r.straightBarLeftLength = f["straightBarLeftLength"]
        r.straightBarRightLength = f["straightBarRightLength"]
        r.straightBarZone = f["straightBarZone"]
    r.leftHook, r.rightHook = f["leftHook"], f["rightHook"]
    for k in ATRIB_FERRO:
        if isinstance(f.get(k), (int, float)):
            setattr(r, k, f[k])
    for j, i in enumerate(f["insercoes"]):
        r.RebarLine(i["x"], i["y"], i["ang"], i["esc"], i["ident"], i["idobra"], i["ipatas"], i["explode"],
                    i["nivel"], i["estilo"], i["cor"])
        if f["type"] == T.ICPFGN and j == 0:
            for x, y, z, iarc, idobra, indfrt in f["pontos_gen"]:
                r.GenRebarPoint(x, y, z, iarc, idobra, indfrt)
    r.leaderLine = f["leaderLine"]
    if isinstance(f.get("leaderLineDistance"), float):
        r.leaderLineDistance = f["leaderLineDistance"]
    pos = posicao_texto(f["mark"], filhos_ferro or [])
    if pos:                                      # texto principal onde o autor o deixou (ex.: vertical ao lado)
        x, y, h, ang = pos
        r.RebarTextDisplayPosition(x, y, h / dwg.settings.scale, ang, 0, T.ICPCENTR_ESQUERD, T.ICPQUEBR_SEMQUEBRA)
    return r


def posicao_texto(mark, filhos_ferro):
    """Início do texto principal do ferro ("17 N1 { 10 C=450"): o 1º dos textos do nível 1 alinhados com "N<mark>"."""
    txts = [f for f in filhos_ferro if f["t"] == "Texto" and f["n"] == 1]
    ref = next((f for f in txts if f["txt"].strip() == f"N{mark}"), None)
    if ref is None:
        return None
    a = math.radians(ref["a"])
    u, v = math.cos(a), math.sin(a)                 # direção do texto; a linha é a dos textos com a mesma normal

    def normal(f):
        return -v * f["x"] + u * f["y"]
    linha = [f for f in txts if abs(f["a"] - ref["a"]) < 0.1 and abs(normal(f) - normal(ref)) < 0.05]
    ini = min(linha, key=lambda f: u * f["x"] + v * f["y"])
    return ini["x"], ini["y"], ini["h"], ini["a"]


def replicar(despejo):
    d = json.load(open(despejo, encoding="utf-8"))
    ents, niveis = d["ents"], d["niveis"]
    dwg = arquivo.novo_desenho(d["info"]["escala"])
    definir_blocos(dwg, ents, niveis)
    n_cotas = n_ferros = 0
    i = 0
    while i < len(ents):
        e = ents[i]
        if e["t"] == "Bloco":
            _, fim = filhos(ents, i)
            dwg.draw.level = e["n"]
            dwg.draw.BlockInsert(nome_bloco(e["b"]), e["x"], e["y"], e["sx"], e["sy"], e["ang"])
            i = fim + 1
            continue
        if e["t"] == "Objeto":
            fs, fim = filhos(ents, i)
            if e["obj"] == "IPOFER" and e.get("ferro"):
                ferro(dwg, e["ferro"], fs)
                n_ferros += 1
            elif e["obj"] == "IPOCOT" and cota(dwg, e, fs, niveis):
                n_cotas += 1
            i = fim + 1
            continue
        if e["t"] not in ("Fim de bloco", "Fim de objeto"):
            desenhar(dwg, e, niveis)
        i += 1
    arquivo.configurar_cotas(dwg)
    nome = "REPLICA_" + os.path.splitext(os.path.basename(despejo))[0].replace("-", "_")
    arqs = arquivo.salvar(dwg, os.path.join(RAIZ, "saidas", "e0"), nome)
    return d, arqs, n_cotas, n_ferros


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    despejos = sys.argv[1:] or sorted(glob.glob(os.path.join(RAIZ, "saidas", "modelos", "PUN_P02*.json")))
    if not despejos:
        print("Sem despejos dos modelos: rode ferramentas/ler_modelo.py DesenhosReferencia/*.DWG")
        return
    for desp in despejos:
        modelo, arqs, nc, nf = replicar(desp)
        rep = ler_modelo.ler(arqs["dwg"])
        saida = os.path.splitext(arqs["dwg"])[0] + ".json"
        json.dump(rep, open(saida, "w", encoding="utf-8"), ensure_ascii=False, default=str)
        r = comparar.comparar(modelo, rep)
        print(f"== {os.path.basename(desp)} -> {os.path.basename(arqs['dwg'])}: {nf} ferros, {nc} cotas; "
              f"arquivos {sorted(arqs)}")
        print(f"   iguais {r['iguais']}, só no modelo {sum(r['so_a'].values())}, só na réplica "
              f"{sum(r['so_b'].values())}")
        for (pos, bit, q, comp), k in sorted((r["ferros_so_a"] + r["ferros_so_b"]).items()):
            print(f"   ferro diferente: N{pos} {q} ø{bit} C={comp}")
        tab = [(e["ferro"]["mark"], e["ferro"]["tabela"][0][2], e["ferro"]["tabela"][0][1],
                e["ferro"]["tabela"][0][8]) for e in rep["ents"] if e.get("ferro")]
        print("   ferros na réplica (TQS):", sorted(tab))


if __name__ == "__main__":
    main()
