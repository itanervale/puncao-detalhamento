# -*- coding: utf-8 -*-
"""
Leitura de uma planta de um edifício do TQS, só em cópia (nada é aberto nem gravado no edifício original):

- plantas: copia só os arquivos da raiz do edifício e lista as plantas (nome, nº do projeto, repetição);
- planta: copia a raiz e a pasta da planta e lê do modelo (TQSModel) os pilares (título, tipo de seção, b, h, ângulo,
  poligonal), as lajes (h, tipo, protensão), as bordas livres (contornos da laje e eixos das vigas), os furos e os
  capitéis, e do edifício (TQSBuild) os cobrimentos das lajes. Com a grelha processada (<FORnnnnM>.GRE e .RSX na
  pasta da planta), roda o FGREANA do TQS para cada combinação de ELU e traz as reações por pilar, para conferência.

Testado na interface 2.1.7 (09/11/2026): o modelo abre só com a raiz, mas ler os objetos de uma planta sem a pasta
dela derruba o processo (violação de acesso). Por isso a janela chama este módulo num processo à parte.

Uso:  python -m dwg_tqs.leitor_tqs plantas "<pasta do edifício>" [--saida dados.json]
      python -m dwg_tqs.leitor_tqs planta "<pasta do edifício>" <planta> [--saida dados.json] [--sem-esforcos]
             [--projeto projeto.json [--pilares P5,P7 | --todos]]
A saída é JSON (UTF-8). Com --projeto, grava também um projeto com os pilares internos, de borda e de canto (ou os
escolhidos).
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import types
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from nucleo import importacao                                         # noqa: E402

FGREANA = (r"C:\TQSW\EXEC\X64\FGREANA.EXE", r"C:\TQSW\EXEC\FGREANA.EXE")


class ErroLeitura(Exception):
    pass


def _tqs():
    """TQSBuild e TQSModel. Se o TQSJan.py da instalação não importar (erro de indentação visto em 05/11/2026), entra
    um módulo vazio no lugar: a leitura do modelo não usa janelas."""
    try:
        from TQS import TQSBuild, TQSModel
    except (SyntaxError, ImportError):
        import TQS
        vazio = types.ModuleType("TQS.TQSJan")
        sys.modules["TQS.TQSJan"] = vazio
        TQS.TQSJan = vazio
        for k in [k for k in sys.modules if k in ("TQS.TQSModel", "TQS.TQSBuild")]:
            del sys.modules[k]
        from TQS import TQSBuild, TQSModel
    return TQSBuild, TQSModel


def eh_edificio(pasta):
    return os.path.isfile(os.path.join(pasta, "EDIFICIO.BDE")) or os.path.isfile(os.path.join(pasta, "EDIFICIO.DAT"))


def _copiar_raiz(edificio, tmp):
    if not eh_edificio(edificio):
        raise ErroLeitura(f"{edificio} não é a pasta de um edifício do TQS (sem EDIFICIO.BDE)")
    dest = os.path.join(tmp, os.path.basename(os.path.normpath(edificio)))
    os.makedirs(dest, exist_ok=True)
    for a in os.listdir(edificio):
        orig = os.path.join(edificio, a)
        if os.path.isfile(orig):
            shutil.copy2(orig, dest)
    return dest


def _dentro(base, alvo):
    base, alvo = os.path.realpath(base), os.path.realpath(alvo)
    try:
        return os.path.commonpath([base, alvo]) == base
    except ValueError:                                  # discos diferentes
        return False


def pasta_na_copia(edificio, pasta, copia):
    """Onde a pasta da planta vai na cópia. A pasta vem dos dados do edifício (GetFloorPath): só vale uma subpasta
    do próprio edifício, para a cópia não sair da pasta temporária (um caminho com ".." passaria num startswith)."""
    edif, orig = os.path.realpath(edificio), os.path.realpath(pasta)
    if not _dentro(edif, orig) or orig == edif:
        raise ErroLeitura(f"a pasta da planta fica fora do edifício: {pasta}")
    dest = os.path.join(os.path.realpath(copia), os.path.relpath(orig, edif))
    if not _dentro(copia, dest):
        raise ErroLeitura(f"pasta da planta inválida: {pasta}")
    return orig, dest


def _abrir_edificio(copia):
    TQSBuild, _ = _tqs()
    os.chdir(copia)
    b = TQSBuild.Building()
    if b.file.Open(os.path.basename(copia)) != 0:
        raise ErroLeitura("o TQS não abriu o edifício (cópia)")
    return b


def _lista_plantas(b, edificio):
    fp = b.floorsplan
    out = []
    for i in range(fp.GetFloorsNumber()):
        nome = fp.GetName(i)
        if not nome:
            continue
        cam = fp.GetFloorPath(i) or nome
        if not os.path.isabs(cam):
            cam = os.path.join(edificio, cam)
        out.append(dict(nome=nome, projeto=fp.GetProjectNumber(i), repeticao=fp.GetRepetition(i),
                        classe=fp.GetClass(i), pasta=cam, existe=os.path.isdir(cam), indice=i))
    return out


def _concreto(b, indice):
    """Concreto das lajes da planta: o específico dela ou, vazio, o de vigas e lajes do edifício ("C25")."""
    m = b.materials
    classe = (m.GetFloorPlanConcreteStrength(indice) or m.beamConcreteStrength or "").strip()
    achado = re.search(r"(\d+(?:[.,]\d+)?)", classe)
    return classe, (float(achado.group(1).replace(",", ".")) if achado else None)


def plantas(edificio, tmp=None):
    """Plantas do edifício (só a raiz é copiada)."""
    cwd = os.getcwd()
    tmp = tmp or tempfile.mkdtemp(prefix="pun_tqs_")
    try:
        b = _abrir_edificio(_copiar_raiz(edificio, tmp))
        return _lista_plantas(b, edificio)
    finally:
        os.chdir(cwd)


def _pontos(polig):
    return [[round(x, 3), round(y, 3)] for x, y in (polig.GetPt(j) for j in range(polig.NumPts()))] if polig else []


def _cobrimentos(b):
    c = b.covers
    return dict(sup=c.slabUpperCover, inf=c.slabLowerCover, protendida_sup=c.prestressedSlabUpperCover,
                protendida_inf=c.prestressedSlabLowerCover)


def _ler_modelo(planta):
    _, TQSModel = _tqs()
    m = TQSModel.Model()
    if m.file.OpenModel() != 0:
        raise ErroLeitura("o TQS não abriu o modelo do edifício (cópia)")
    f = m.floors.GetFloor(planta)
    if f is None:
        raise ErroLeitura(f"a planta {planta!r} não está no modelo")
    it = f.iterator
    objs = lambda tipo: [o for o in (it.GetObject(tipo, k) for k in range(it.GetNumObjects(tipo))) if o is not None]  # noqa: E731
    pilares = []
    for s in objs(TQSModel.TYPE_SECPIL):
        g = s.columnGeometry
        pilares.append(dict(titulo=s.formattedTitle, numero=s.column.columnIdent.objectNumber, tipo=g.sectionType,
                            b1=g.sectionB1, h1=g.sectionH1, ang=g.sectionAngle, polig=_pontos(s.sectionPolig)))
    lajes = []
    for s in objs(TQSModel.TYPE_LAJES):
        g, d = s.slabGeometry, s.slabDetailing
        lajes.append(dict(titulo=s.formattedTitle, h=g.thickness, tipo=g.type, rebaixo=g.recess, cobrimento=d.cover,
                          protendida=bool(d.prestressed)))
    bordas = [[c.startX, c.startY, c.endX, c.endY, 0.0, "borda da laje"] for c in objs(TQSModel.TYPE_CTRAUX)]
    for v in objs(TQSModel.TYPE_VIGAS):
        nos = [v.GetBeamNode(i) for i in range(v.NumNodes())]
        pts = [(n.nodeX, n.nodeY) for n in nos]
        meia = v.GetBeamGeometry().width / 2
        nome = v.formattedTitle or f"V{v.number}"
        bordas += [[*pts[i], *pts[i + 1], meia, f"viga {nome}"] for i in range(len(pts) - 1)]
    furos = [dict(polig=_pontos(o.slabOpeningPolygon)) for o in objs(TQSModel.TYPE_FUROS)]
    capiteis = [dict(polig=_pontos(o.dropPanelPolygon), h=o.dropPanelThickness) for o in objs(TQSModel.TYPE_CAPITEIS)]
    return dict(pilares=pilares, lajes=lajes, bordas=[[round(x, 3) if isinstance(x, float) else x for x in b]
                                                      for b in bordas],
                furos=[f for f in furos if f["polig"]], capiteis=[c for c in capiteis if c["polig"]])


def fgreana():
    return next((e for e in FGREANA if os.path.isfile(e)), None)


def esforcos(pasta_planta, projeto):
    """Reações por pilar em cada combinação de ELU da grelha (FOR<projeto>M), rodando o FGREANA na pasta (cópia).
    Sem a grelha processada ou sem o FGREANA, devolve só o aviso."""
    nome = f"FOR{int(projeto):04d}M"
    gre, rsx = (os.path.join(pasta_planta, nome + ext) for ext in (".GRE", ".RSX"))
    out = dict(nome=nome, processada=False, combinacoes=[], esforcos={}, aviso="")
    if not os.path.isfile(gre):
        out["aviso"] = f"sem o modelo da grelha ({nome}.GRE): gere e processe a grelha da planta no TQS"
        return out
    if not os.path.isfile(rsx):
        out["aviso"] = f"grelha não processada (sem {nome}.RSX): processe a grelha da planta no TQS"
        return out
    exe = fgreana()
    if not exe:
        out["aviso"] = "FGREANA.EXE não encontrado em C:\\TQSW\\EXEC"
        return out
    texto = pathlib.Path(gre).read_text(encoding="cp1252", errors="replace")
    combs = importacao.combinacoes_elu(texto)
    out.update(processada=True, combinacoes=[dict(n=n, titulo=t) for n, t in combs])
    if not combs:
        out["aviso"] = "a grelha não tem combinações de ELU"
        return out
    for n, titulo in combs:
        pathlib.Path(pasta_planta, "GREANA.TMP").write_bytes(f"{nome}\r\n{n}\r\n".encode("ascii"))
        r = subprocess.run([exe], cwd=pasta_planta, capture_output=True, timeout=120,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for pil, (mx, my, fz) in importacao.reacoes(r.stdout.decode("cp1252", errors="replace")).items():
            out["esforcos"].setdefault(pil, []).append(dict(n=n, titulo=titulo, mx=mx, my=my, fz=fz))
    if not out["esforcos"]:
        out["aviso"] = "o FGREANA não trouxe reações de pilares"
    return out


def ler_planta(edificio, planta, tmp=None, com_esforcos=True):
    """Tudo o que a importação usa de uma planta (cópia em `tmp`)."""
    cwd = os.getcwd()
    tmp = tmp or tempfile.mkdtemp(prefix="pun_tqs_")
    try:
        copia = _copiar_raiz(edificio, tmp)
        b = _abrir_edificio(copia)
        info = next((p for p in _lista_plantas(b, edificio) if p["nome"] == planta), None)
        if info is None:
            raise ErroLeitura(f"o edifício não tem a planta {planta!r}")
        if not info["existe"]:
            raise ErroLeitura(f"a pasta da planta não existe: {info['pasta']}")
        orig, dest = pasta_na_copia(edificio, info["pasta"], copia)
        shutil.copytree(orig, dest, dirs_exist_ok=True)
        concreto, fck = _concreto(b, info["indice"])
        dados = dict(formato="puncao-leitura-tqs", versao=1, edificio=os.path.normpath(edificio), planta=planta,
                     projeto=info["projeto"], repeticao=info["repeticao"], data=datetime.now().isoformat(timespec="seconds"),
                     cobrimentos=_cobrimentos(b), concreto=concreto, fck=fck)
        os.chdir(copia)
        dados.update(_ler_modelo(planta))
        dados["grelha"] = esforcos(dest, info["projeto"]) if com_esforcos else dict(aviso="esforços não lidos")
        return dados
    finally:
        os.chdir(cwd)


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Leitura de uma planta do TQS (em cópia) para a importação.")
    ap.add_argument("acao", choices=("plantas", "planta"))
    ap.add_argument("edificio")
    ap.add_argument("planta", nargs="?")
    ap.add_argument("--saida", help="arquivo JSON da leitura (sem ele, imprime)")
    ap.add_argument("--tmp", help="pasta temporária da cópia (quem chama apaga)")
    ap.add_argument("--sem-esforcos", action="store_true")
    ap.add_argument("--projeto", help="grava um projeto com os pilares importados")
    ap.add_argument("--pilares", help="títulos separados por vírgula (padrão: os retangulares internos, de borda e de canto)")
    ap.add_argument("--todos", action="store_true", help="todos os retangulares, inclusive os de bordas em lados opostos, os girados com borda e os com "
                    "abertura ou capitel")
    ap.add_argument("--ajustar", action="store_true", help="s0 e espaçamentos nos limites da NBR 6118 (0,5d e 0,75d)")
    a = ap.parse_args(argv)
    tmp = a.tmp or tempfile.mkdtemp(prefix="pun_tqs_")
    try:
        try:
            if a.acao == "plantas":
                dados = dict(plantas=plantas(a.edificio, tmp))
            else:
                if not a.planta:
                    ap.error("informe a planta")
                dados = ler_planta(a.edificio, a.planta, tmp, com_esforcos=not a.sem_esforcos)
        except ErroLeitura as e:
            dados = dict(erro=str(e))
        texto = json.dumps(dados, ensure_ascii=False, indent=1)
        if a.saida:
            pathlib.Path(a.saida).write_text(texto, encoding="utf-8")
        else:
            print(texto)
        if "erro" in dados:
            return 1
        if a.projeto and a.acao == "planta":
            linhas = importacao.analisar(dados)
            nomes = {n.strip() for n in a.pilares.split(",")} if a.pilares else None
            sel = [ln for ln in linhas if ln["suportado"] and
                   (ln["titulo"] in nomes if nomes else (a.todos or importacao.selecao_padrao(ln)))]
            pars = [importacao.ajustar_limites(ln["par"])[0] if a.ajustar else ln["par"] for ln in sel]
            proj = dict(formato="puncao-detalhamento", versao=1, pilares=pars,
                        origem_tqs=dict(edificio=dados["edificio"], planta=dados["planta"], data=dados["data"]))
            pathlib.Path(a.projeto).write_text(json.dumps(proj, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"Projeto: {a.projeto} ({len(sel)} pilar(es): {', '.join(ln['titulo'] for ln in sel)})",
                  file=sys.stderr)
        return 0
    finally:
        if not a.tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
