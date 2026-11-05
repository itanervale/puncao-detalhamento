# -*- coding: utf-8 -*-
"""
Compara dois despejos JSON (ferramentas/ler_modelo.py) entidade a entidade: tipo, nível, estilo, coordenadas
(com tolerância), texto e blocos; e os ferros inteligentes pela tabela (posição, bitola, quantidade, comprimento).
Serve para conferir a prancha gerada contra o desenho de referência e para achar as edições feitas no TQS.

Uso:  python ferramentas/comparar.py <a.json> <b.json> [--tol 0.05] [--deslocar dx,dy] [--alinhar-titulo]
      [--detalhes N]
--deslocar soma (dx, dy) às coordenadas de b; --alinhar-titulo calcula esse deslocamento pelo texto do nível 222.
Sai com código 0 quando não há diferença.
"""
import argparse
import json
import pathlib
import sys
from collections import Counter

TIPOS = ("Linha", "Polyline", "Curva", "Circulo", "Arco", "Texto", "Bloco", "Objeto")


def _r(v, tol):
    return round(v / tol) * tol if tol else v


def assinatura(e, tol, dx=0.0, dy=0.0):
    """Tipo, nível, estilo, geometria e texto, e no fim a cor (índice e RGB próprio): uma cor diferente aparece como
    diferença (os ferros com o objeto em outro nível saíam com outra cor no editor do TQS)."""
    s = _assinatura(e, tol, dx, dy)
    if not s:
        return None
    if str(e.get("dentro", "")).startswith("<IPOCOT"):
        # Dentro das cotas, a cor lida é a que o objeto guardou ao ser criado, não a da tabela de níveis: o módulo
        # de cotas da interface usa sempre as cores padrão (3 e 7), mesmo com a tabela dos modelos gravada
        # (03/11/2026). Por isso não entra na comparação.
        return s + (("cor", None, None),)
    return s + (("cor", e.get("c"), e.get("rgb", 0)),)


def _assinatura(e, tol, dx, dy):
    t, n, s = e["t"], e["n"], e.get("s", 0)
    if t == "Objeto":
        return (t, n, e.get("obj"))                   # o nível do objeto decide a cor do ferro no editor
    if str(e.get("dentro", "")).startswith("<"):
        s = None                                        # dentro de cota ou ferro: o estilo é o do objeto
    if t in ("Linha", "Polyline", "Curva"):
        pts = [(round(_r(x + dx, tol), 4), round(_r(y + dy, tol), 4)) for x, y in e.get("xy") or []]
        if len(pts) == 2 and pts[0] == pts[1] and str(e.get("dentro", "")).startswith("<"):
            return None                                 # pontos de definição das cotas (linhas de comprimento zero)
        if t == "Linha" and len(pts) == 2:
            pts.sort()                                  # a mesma linha nos dois sentidos
        return (t, n, s, tuple(pts), bool(e.get("fill")))
    if t == "Circulo":
        return (t, n, s, round(_r(e["x"] + dx, tol), 4), round(_r(e["y"] + dy, tol), 4), round(_r(e["r"], tol), 4))
    if t == "Arco":
        return (t, n, s, round(_r(e["x"] + dx, tol), 4), round(_r(e["y"] + dy, tol), 4), round(_r(e["r"], tol), 4),
                round(e["a1"] % 360, 1), round(e["a2"] % 360, 1))
    if t == "Texto":
        return (t, n, round(_r(e["x"] + dx, tol), 4), round(_r(e["y"] + dy, tol), 4), round(e["h"], 3),
                round(e["a"] % 360, 1), e["txt"].strip())
    if t == "Bloco":
        return (t, n, e["b"], round(_r(e["x"] + dx, tol), 4), round(_r(e["y"] + dy, tol), 4),
                round(e["ang"] % 360, 1), round(e["sx"], 3), round(e["sy"], 3))
    return None


def ferros(d):
    out = Counter()
    for e in d["ents"]:
        f = e.get("ferro")
        if f:
            for linha in f["tabela"]:
                out[(linha[0], round(linha[1], 1), linha[2], round(linha[8], 1))] += 1
    return out


def titulo(d):
    for e in d["ents"]:
        if e["t"] == "Texto" and e["n"] == 222:
            return e["x"], e["y"]
    return None


def _achatar(s):
    """Separa a assinatura em parte fixa (tipo, nível, textos) e números (coordenadas, raios, ângulos)."""
    fixa, nums = [], []

    def vai(v):
        if isinstance(v, tuple):
            fixa.append(len(v))
            for x in v:
                vai(x)
        elif isinstance(v, float) and not isinstance(v, bool):
            nums.append(v)
        else:
            fixa.append(v)
    vai(s)
    return tuple(fixa), nums


def _mesma_chave(a, b):
    """Partes fixas iguais; estilo None (entidade dentro de objeto) vale como qualquer estilo."""
    return len(a) == len(b) and all(x == y or x is None or y is None for x, y in zip(a, b))


def _parear(so_a, so_b, folga):
    """2ª passada: pares que só diferem por arredondamento na borda da grade (diferença <= folga) ou pelo estilo de
    uma entidade de dentro de objeto (ex.: chamada que no modelo é objeto e na réplica é polilinha comum)."""
    resto_b = Counter(so_b)
    por_tipo = {}
    for s in resto_b.elements():
        por_tipo.setdefault((s[0], s[1]), []).append(s)
    resto_a = Counter()
    for s in so_a.elements():
        chave, nums = _achatar(s)
        cands = por_tipo.get((s[0], s[1]), [])
        par = next((c for c in cands if _mesma_chave(chave, _achatar(c)[0]) and len(nums) == len(_achatar(c)[1])
                    and max((abs(u - v) for u, v in zip(nums, _achatar(c)[1])), default=0) <= folga), None)
        if par is None:
            resto_a[s] += 1
        else:
            cands.remove(par)
            resto_b[par] -= 1
    return resto_a, +resto_b


def comparar(a, b, tol=0.05, dx=0.0, dy=0.0):
    ca = Counter(s for s in (assinatura(e, tol) for e in a["ents"] if e["t"] in TIPOS) if s)
    cb = Counter(s for s in (assinatura(e, tol, dx, dy) for e in b["ents"] if e["t"] in TIPOS) if s)
    so_a, so_b = _parear(ca - cb, cb - ca, 2.01 * tol)
    fa, fb = ferros(a), ferros(b)
    # nível como texto: do JSON vem "221", da leitura direta vem 221
    na = {str(k): v for k, v in a.get("niveis", {}).items()}
    nb = {str(k): v for k, v in b.get("niveis", {}).items()}
    niveis = {n: (na.get(n), nb.get(n)) for n in set(na) | set(nb)
              if (na.get(n) or {}).get("cor") != (nb.get(n) or {}).get("cor")
              or (na.get(n) or {}).get("estilo") != (nb.get(n) or {}).get("estilo")}
    return dict(iguais=sum((ca & cb).values()), so_a=so_a, so_b=so_b, ferros_so_a=fa - fb, ferros_so_b=fb - fa,
                niveis=niveis)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--tol", type=float, default=0.05)
    ap.add_argument("--deslocar")
    ap.add_argument("--alinhar-titulo", action="store_true")
    ap.add_argument("--detalhes", type=int, default=8)
    o = ap.parse_args()
    a = json.loads(pathlib.Path(o.a).read_text(encoding="utf-8"))
    b = json.loads(pathlib.Path(o.b).read_text(encoding="utf-8"))
    dx = dy = 0.0
    if o.deslocar:
        dx, dy = (float(v) for v in o.deslocar.split(","))
    elif o.alinhar_titulo and titulo(a) and titulo(b):
        (xa, ya), (xb, yb) = titulo(a), titulo(b)
        dx, dy = xa - xb, ya - yb
    r = comparar(a, b, o.tol, dx, dy)
    print(f"iguais: {r['iguais']} | só em A: {sum(r['so_a'].values())} | só em B: {sum(r['so_b'].values())}"
          f" | deslocamento de B: ({dx:.2f}, {dy:.2f})")
    for nome, c in (("A", r["so_a"]), ("B", r["so_b"])):
        por = Counter()
        for s, k in c.items():
            por[(s[1], s[0])] += k
        for (n, t), k in sorted(por.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
            print(f"  só em {nome}: nível {n} {t}: {k}")
            for s in [s for s in c if s[1] == n and s[0] == t][:o.detalhes]:
                print("      ", s)
    for nome, c in (("A", r["ferros_so_a"]), ("B", r["ferros_so_b"])):
        for (pos, bit, q, comp), k in sorted(c.items()):
            print(f"  ferro só em {nome}: N{pos} {q} ø{bit} C={comp}")
    for n, (x, y) in sorted(r["niveis"].items(), key=lambda kv: int(kv[0])):
        print(f"  tabela de níveis, nível {n}: A {x} | B {y}")
    iguais = not (r["so_a"] or r["so_b"] or r["ferros_so_a"] or r["ferros_so_b"] or r["niveis"])
    sys.exit(0 if iguais else 1)


if __name__ == "__main__":
    main()
