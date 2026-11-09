# -*- coding: utf-8 -*-
"""
E8: importação do TQS.
- sem o TQS: combinações de ELU do .GRE, reações da listagem do FGREANA, posição do pilar na laje (interno, borda,
  canto), seção, espessura, aberturas e capitéis, montagem dos pilares do projeto e a mescla com o projeto, a partir
  de uma leitura real gravada em testes/dados (planta "Primeiro" do edifício de desenvolvimento, sem dados do
  licenciado);
- com a tela: o diálogo (marcar, desmarcar, confirmar borda e canto) e a janela (importar num projeto);
- com o TQS e o edifício de desenvolvimento (variável PUN_EDIFICIO_TESTE, fora do repositório): o leitor numa
  cópia, que deve dar o mesmo da leitura gravada.

Uso:  python -m unittest testes.teste_e8_importacao -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import importacao as imp                                   # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402

DADOS = os.path.join(RAIZ, "testes", "dados")
EDIFICIO = os.environ.get("PUN_EDIFICIO_TESTE", "")              # pasta de um edifício com a planta "Primeiro"


def _ler(nome):
    with open(os.path.join(DADOS, nome), encoding="utf-8") as f:
        return json.load(f) if nome.endswith(".json") else f.read()


try:
    import tkinter as tk
    _r = tk.Tk()
    _r.destroy()
    TEM_TELA = True
except Exception:
    TEM_TELA = False
try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False


def _ret(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


class TesteGrelha(unittest.TestCase):
    def test_combinacoes(self):
        gre = _ler("grelha_combinacoes.gre")
        self.assertEqual([n for n, _ in imp.combinacoes(gre)], [9, 10, 11, 12, 13, 14])
        self.assertEqual(imp.combinacoes_elu(gre), [(9, "ELU1/PERM/PP+PERM"), (10, "ELU1/PERMACID/PP+PERM+ACID"),
                                                    (12, "ELU1/PERM/PP_V+PERM_V"), (13, "ELU1/PERMACID/PP_V+PERM_V+ACID_V")])

    def test_reacoes(self):
        r = imp.reacoes(_ler("greana_comb10.lst"))
        self.assertEqual(len(r), 12)
        self.assertEqual(r["P7"][2], 48.68)                  # a listagem gerada à mão no TQS dá o mesmo
        self.assertEqual(r["P6"], (0.5, -5.13, 53.12))
        self.assertNotIn("Total", r)

    def test_governante(self):
        es = [dict(n=9, titulo="a", mx=0, my=0, fz=10.0), dict(n=10, titulo="b", mx=1, my=2, fz=12.5)]
        self.assertEqual(imp.governante(es)["n"], 10)
        self.assertIsNone(imp.governante([]))
        self.assertIn("Fz 12,50 tf", imp.resumo_esforcos(es))


class TestePosicao(unittest.TestCase):
    LAJE = [(0, 0, 1000, 0, 0.0, "borda"), (1000, 0, 1000, 800, 0.0, "borda"),
            (1000, 800, 0, 800, 0.0, "borda"), (0, 800, 0, 0, 0.0, "borda")]

    def test_interno_borda_canto(self):
        d = 15.5                                             # 2d = 31
        self.assertEqual(imp.posicao(_ret(400, 300, 440, 340), self.LAJE, d)[0], "interno")
        self.assertEqual(imp.posicao(_ret(400, 0, 440, 40), self.LAJE, d)[0], "borda")
        c, lados = imp.posicao(_ret(0, 0, 40, 40), self.LAJE, d)
        self.assertEqual((c, sorted(lados)), ("canto", ["baixo", "esquerda"]))
        self.assertEqual(imp.posicao(_ret(400, 32, 440, 72), self.LAJE, d)[0], "interno")     # 32 > 2d
        self.assertEqual(imp.posicao(_ret(400, 30, 440, 70), self.LAJE, d)[0], "borda")       # 30 < 2d

    def test_viga_desconta_meia_largura(self):
        viga = [(0, 100, 1000, 100, 7.5, "viga V1")]         # eixo a 40 cm da face, face a 32,5
        self.assertEqual(imp.posicao(_ret(400, 140, 440, 180), viga, 15.5)[0], "interno")
        c, lados = imp.posicao(_ret(400, 135, 440, 175), viga, 15.5)
        self.assertEqual((c, lados["baixo"][1]), ("borda", "viga V1"))

    def test_lados_opostos_pedem_conferencia(self):
        estreita = [(0, 0, 1000, 0, 0.0, "b"), (1000, 40, 0, 40, 0.0, "b")]
        self.assertEqual(imp.posicao(_ret(400, 0, 440, 40), estreita, 15.5)[0], "verificar")

    def test_distancias(self):
        self.assertEqual(imp.dist_poligono_seg(_ret(0, 0, 10, 10), (5, 5), (50, 5)), 0.0)
        self.assertAlmostEqual(imp.dist_poligono_seg(_ret(0, 0, 10, 10), (13, 14), (20, 14)), 5.0)
        self.assertAlmostEqual(imp.dist_poligonos(_ret(0, 0, 10, 10), _ret(20, 0, 30, 10)), 10.0)


class TesteSecaoELaje(unittest.TestCase):
    def test_dimensoes(self):
        self.assertEqual(imp.dimensoes(dict(ang=0, b1=20, h1=100, polig=_ret(660, 0, 680, 100))), (20, 100, ""))
        self.assertEqual(imp.dimensoes(dict(ang=90, b1=20, h1=100, polig=_ret(0, 0, 100, 20)))[:2], (100, 20))
        bx, by, av = imp.dimensoes(dict(ang=30, b1=20, h1=100, polig=_ret(0, 0, 1, 1)))
        self.assertEqual((bx, by), (20, 100))
        self.assertIn("girado de 30°", av)

    def test_espessura(self):
        self.assertEqual(imp.espessura([dict(h=20.0)]), (20.0, ""))
        h, av = imp.espessura([dict(h=20.0), dict(h=20.0), dict(h=18.0)])
        self.assertEqual(h, 20.0)
        self.assertIn("18, 20", av)
        self.assertEqual(imp.espessura([])[0], None)


class TesteAnalise(unittest.TestCase):
    def setUp(self):
        self.dados = _ler("leitura_planta.json")
        self.linhas = {ln["titulo"]: ln for ln in imp.analisar(self.dados)}

    def test_internos_da_planta(self):
        internos = sorted(t for t, ln in self.linhas.items() if imp.selecao_padrao(ln))
        self.assertEqual(internos, ["P11", "P5", "P7"])
        self.assertEqual(self.linhas["P1"]["posicao"], "canto")
        self.assertEqual(self.linhas["P2"]["posicao"], "borda")
        self.assertFalse(self.linhas["P6"]["suportado"])      # circular
        self.assertIn("circular", self.linhas["P6"]["motivo"])

    def test_pilar_do_projeto(self):
        par = self.linhas["P7"]["par"]
        self.assertEqual({k: par[k] for k in ("titulo", "bx", "by", "h_laje", "c_sup", "c_inf", "repeticoes")},
                         dict(titulo="P7", bx=40.0, by=40.0, h_laje=20.0, c_sup=2.5, c_inf=2.5, repeticoes=1))
        self.assertEqual([e["n"] for e in par["tqs"]["esforcos"]], [9, 10, 12, 13])
        self.assertEqual(par["tqs"]["posicao"], "interno")
        self.assertAlmostEqual(self.linhas["P7"]["d"], 15.5)
        self.assertEqual(detalhar(par)["erros"], [])

    def test_base_e_repeticao(self):
        base = dict(titulo="PX", bx=99, solucao="conectores", repeticoes=3, con_pinos=4, tqs=dict(planta="velha"))
        dados = dict(self.dados, repeticao=5)
        par = {ln["titulo"]: ln for ln in imp.analisar(dados, base)}["P7"]["par"]
        self.assertEqual((par["solucao"], par["con_pinos"], par["repeticoes"], par["bx"]), ("conectores", 4, 5, 40.0))
        self.assertEqual(par["tqs"]["planta"], "Primeiro")

    def test_abertura_e_capitel(self):
        dados = dict(self.dados, furos=[dict(polig=_ret(1360, 650, 1400, 690))],          # 20 cm à direita do P7
                     capiteis=[dict(polig=_ret(1250, 1210, 1390, 1410), h=10.0)])         # em volta do P11
        linhas = {ln["titulo"]: ln for ln in imp.analisar(dados)}
        self.assertTrue(any(a.startswith("abertura a 20 cm") for a in linhas["P7"]["avisos"]))
        self.assertTrue(any(a.startswith("capitel de 10 cm") for a in linhas["P11"]["avisos"]))
        self.assertFalse(imp.selecao_padrao(linhas["P7"]))
        self.assertTrue(imp.selecao_padrao(linhas["P5"]))

    def test_ajustar_limites(self):
        par = self.linhas["P7"]["par"]                                   # laje de 20: d = 15,5
        avisos = lambda q: [v[1] for v in detalhar(q)["verificacoes"] if v[0] == "aviso"]    # noqa: E731
        self.assertTrue(any("passa de" in a for a in avisos(par)))
        novo, mud = imp.ajustar_limites(par)
        self.assertEqual((novo["cob_s0"], novo["cob_s"], novo["con_s0"], novo["con_sr"]), (7.0, 11.0, 7.0, 11.0))
        self.assertEqual(len(mud), 4)
        self.assertIn("s0 da cobrinha 11 -> 7 (0,5d = 7,75)", mud)
        self.assertNotIn("cob_s_x", novo)                                # vazio segue o cob_s
        self.assertFalse(any("passa de" in a for a in avisos(novo)))
        self.assertFalse(any("passa de" in a for a in avisos(dict(novo, solucao="conectores"))))
        self.assertEqual(imp.ajustar_limites(novo)[1], [])                # já dentro: nada muda

    def test_ajustar_respeita_o_modelo_e_valores_menores(self):
        p2 = dict(titulo="P2", bx=150, by=50, h_laje=27, c_sup=2.0, c_inf=2.0)     # d = 23: 11 e 17 já no limite
        self.assertEqual(imp.ajustar_limites(p2)[1], [])
        q, mud = imp.ajustar_limites(dict(p2, cob_s0=8, cob_s_x=20))
        self.assertEqual((q["cob_s0"], q["cob_s_x"]), (8, 17.0))
        self.assertEqual(mud, ["espaçamento em x 20 -> 17 (0,75d = 17,25)"])

    def test_fck_do_tqs(self):
        self.assertEqual(self.linhas["P7"]["par"]["fck"], 25.0)
        sem = {k: v for k, v in self.dados.items() if k != "fck"}
        self.assertNotIn("fck", {ln["titulo"]: ln for ln in imp.analisar(sem)}["P7"]["par"])   # fica o padrão

    def test_mesclar(self):
        atuais = [dict(titulo="P7", bx=30, by=30, cob_s=12.0), dict(titulo="P2")]
        novos = [self.linhas["P7"]["par"], self.linhas["P5"]["par"]]
        pil, n_novos, n_atual, pulados = imp.mesclar(atuais, novos)
        self.assertEqual((n_novos, n_atual, pulados), (1, 1, []))
        p7 = pil[0]
        self.assertEqual((p7["bx"], p7["h_laje"], p7["cob_s"]), (40.0, 20.0, 12.0))   # detalhamento mantido
        self.assertIn("tqs", p7)
        self.assertEqual(atuais[0]["bx"], 30)                                           # sem efeito colateral
        pil, n_novos, n_atual, pulados = imp.mesclar(atuais, novos, atualizar=False)
        self.assertEqual((n_novos, n_atual, pulados, pil[0]["bx"]), (1, 0, ["P7"], 30))


class TestePastaDaPlanta(unittest.TestCase):
    """A pasta da planta vem dos dados do edifício: a cópia não pode sair da pasta temporária."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pun_e8p_")
        self.edif = os.path.join(self.tmp, "Edificio")
        os.makedirs(os.path.join(self.edif, "Primeiro"))
        self.copia = os.path.join(self.tmp, "copia", "Edificio")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_subpasta_do_edificio(self):
        from dwg_tqs import leitor_tqs as lt
        orig, dest = lt.pasta_na_copia(self.edif, os.path.join(self.edif, "Primeiro"), self.copia)
        self.assertEqual(os.path.basename(orig), "Primeiro")
        self.assertEqual(dest, os.path.join(os.path.realpath(self.copia), "Primeiro"))

    def test_recusa_fora_do_edificio(self):
        from dwg_tqs import leitor_tqs as lt
        for pasta in (os.path.join(self.edif, "..", "Outro"), os.path.join(self.edif, "Primeiro", "..", ".."),
                      self.edif, self.tmp + "x"):
            with self.subTest(pasta=pasta), self.assertRaises(lt.ErroLeitura):
                lt.pasta_na_copia(self.edif, pasta, self.copia)


class TesteColapso(unittest.TestCase):
    """Colapso progressivo (NBR 6118:2026, 19.5.4): ancoragem além de C'' e As·fyd >= 1,5·FSd com as cargas do TQS."""

    def test_lb(self):
        from nucleo import colapso as col
        self.assertAlmostEqual(col.lb_basico(10, 25), 37.67, places=2)      # fbd = 2,25 x 0,7 x 2,565 / 1,4
        self.assertAlmostEqual(col.lb_basico(10, 30), 33.36, places=2)
        self.assertAlmostEqual(col.lb_basico(16, 25), 60.27, places=2)
        self.assertEqual(col.lb_basico(10, 90), 25.0)                       # o mínimo de 25ø

    def test_ultima_linha_e_c2(self):
        from nucleo import colapso as col
        con = detalhar(dict(titulo="P02", bx=50, by=150, h_laje=27, solucao="conectores", col_n_face_bx=3,
                            col_n_face_by=8, con_n_face_bx=3, con_n_face_by=5))
        anc = col.ancoragem(con)
        self.assertEqual((anc["x"]["ult"], anc["x"]["a"]), (45, 90))            # 11 + 2 x 17; + 2d = 45
        self.assertFalse(anc["x"]["ok"])
        cob = detalhar(dict(titulo="P", bx=40, by=40, h_laje=27, c_sup=2.0, c_inf=2.0, cob_s_y=15, cob_linhas_y=5))
        u = col.ultima_linha(cob)
        self.assertEqual(sorted(u.values()), [62, 71])                       # 11 + 3 x 17 e 11 + 4 x 15

    def test_capacidade_e_sugestao(self):
        from nucleo import colapso as col
        par = {ln["titulo"]: ln for ln in imp.analisar(_ler("leitura_planta.json"))}["P7"]["par"]
        par, _ = imp.ajustar_limites(par)
        cap = col.capacidade({**detalhar(par)["p"]})
        self.assertAlmostEqual(cap["as_nec"], 1.5 * 1.2 * 486.8 / (50 / 1.15), places=6)      # 20,15 cm2
        self.assertFalse(cap["ok"])                                          # 8 + 3 ø10 = 17,28
        mud, txt = col.sugerir(detalhar(par))
        self.assertEqual(mud, dict(col_n_face_bx=7, col_n_face_by=6, col_ext=110.0))      # 71 + 37,67 -> 110
        r = detalhar({**par, **mud})
        self.assertFalse([v for v in r["verificacoes"] if v[0] == "aviso"])
        self.assertTrue(any(v[1].startswith("colapso: As = 20,42") for v in r["verificacoes"]))


@unittest.skipUnless(TEM_TELA, "sem tela para o Tk")
class TesteJanela(unittest.TestCase):
    def setUp(self):
        from janela.app import App
        self.app = App()
        self.app.withdraw()
        self.dados = _ler("leitura_planta.json")

    def tearDown(self):
        self.app.modificado = False
        self.app.destroy()

    def _dialogo(self):
        from janela.importar import DlgImportar
        leituras = []

        def leitor(acao, edif, planta=None):
            leituras.append(acao)
            return dict(plantas=[dict(nome="Primeiro", existe=True)]) if acao == "plantas" else self.dados
        dlg = DlgImportar(self.app, self.app.pilar, leitor=leitor)
        dlg.withdraw()
        dlg.carregar(self.dados)
        return dlg

    def test_dialogo_marca_e_devolve(self):
        dlg = self._dialogo()
        try:
            marcados = sorted(dlg.linhas[j]["titulo"] for j in dlg.marcados)
            self.assertEqual(marcados, ["P11", "P5", "P7"])
            j6 = next(j for j, ln in enumerate(dlg.linhas) if ln["titulo"] == "P6")
            dlg._alternar(str(j6))                                          # circular: não marca
            self.assertNotIn(j6, dlg.marcados)
            j5 = next(j for j, ln in enumerate(dlg.linhas) if ln["titulo"] == "P5")
            dlg._alternar(str(j5))
            dlg.v_solucao.set("conectores")
            r = dlg.aplicar()
            self.assertEqual(sorted(p["titulo"] for p in r["pilares"]), ["P11", "P7"])
            self.assertTrue(all(p["solucao"] == "conectores" for p in r["pilares"]))
            self.assertEqual(r["origem"]["planta"], "Primeiro")
        finally:
            dlg.destroy()

    def test_borda_pede_confirmacao(self):
        dlg = self._dialogo()
        try:
            dlg.marcados = {j for j, ln in enumerate(dlg.linhas) if ln["titulo"] in ("P2", "P7")}
            with mock.patch("janela.importar.messagebox.askyesno", return_value=False) as pergunta:
                self.assertIsNone(dlg.aplicar())
            self.assertIn("P2", pergunta.call_args[0][1])
            with mock.patch("janela.importar.messagebox.askyesno", return_value=True):
                self.assertEqual(len(dlg.aplicar()["pilares"]), 2)
        finally:
            dlg.destroy()

    def test_importar_num_projeto_novo(self):
        linhas = imp.analisar(self.dados, self.app.pilar)
        r = dict(pilares=[ln["par"] for ln in linhas if imp.selecao_padrao(ln)], atualizar=True,
                 origem=dict(edificio="X", planta="Primeiro", data=""), avisos={})
        with mock.patch("janela.app.DlgImportar") as dlg, \
                mock.patch("janela.app.messagebox.askokcancel", return_value=True) as aviso:
            dlg.return_value.mostrar.return_value = r
            self.app.importar_tqs()
        titulos = [p["titulo"] for p in self.app.projeto["pilares"]]
        self.assertEqual(titulos, ["P5", "P7", "P11"])                  # o pilar de exemplo saiu
        self.assertEqual(self.app.projeto["origem_tqs"]["planta"], "Primeiro")
        self.assertEqual(self.app.pilar["titulo"], "P5")
        self.assertTrue(self.app.tv.exists("tqs"))                      # esforços para conferência na árvore
        self.assertEqual(len(self.app.tv.get_children("tqs")), 4)
        self.app.mais_pilar()
        self.assertNotIn("tqs", self.app.pilar)                         # o pilar novo não herda a origem
        self.assertIn("Programa em fase de testes, recomenda-se a duplicação do edifício", aviso.call_args[0][1])

    def test_aviso_cancelado_nao_abre_a_importacao(self):
        with mock.patch("janela.app.DlgImportar") as dlg, \
                mock.patch("janela.app.messagebox.askokcancel", return_value=False):
            self.app.importar_tqs()
        dlg.assert_not_called()

    def test_importar_sugerindo_o_colapso(self):
        linhas = imp.analisar(self.dados, self.app.pilar)
        r = dict(pilares=[ln["par"] for ln in linhas if ln["titulo"] == "P7"], atualizar=True, ajustar=True,
                 colapso=True, origem=dict(edificio="X", planta="Primeiro", data=""), avisos={})
        with mock.patch("janela.app.DlgImportar") as dlg, \
                mock.patch("janela.app.messagebox.askokcancel", return_value=True):
            dlg.return_value.mostrar.return_value = r
            self.app.importar_tqs()
        p7 = self.app.pilar
        self.assertEqual((p7["col_n_face_bx"], p7["col_n_face_by"], p7["col_ext"], p7["fck"]), (7, 6, 110.0, 25.0))
        self.assertFalse([v for v in self.app.res["verificacoes"] if v[0] == "aviso" and "colapso" in v[1]])
        self.assertIn("P7: colapso sugerido", self.app.txm.get("1.0", "end"))

    def test_botao_sugerir_no_pilar(self):
        self.app.abrir(os.path.join(RAIZ, "exemplos", "P02_conectores.json"))
        self.app.sugerir_colapso()                                      # sem cargas: só o comprimento
        self.assertEqual(self.app.pilar["col_ext"], 130.0)              # C'' a 90 + lb 37,67 -> 130
        self.assertEqual(self.app.pilar["col_n_face_by"], 8)
        self.assertIn("sem cargas do TQS", self.app.txm.get("1.0", "end"))

    def test_importar_ajustando_aos_limites(self):
        self.app.projeto["pilares"] = [dict(titulo="P7", bx=30, by=30, cob_s=15.0, cob_linhas=5)]
        self.app.modificado = True
        linhas = imp.analisar(self.dados, self.app.pilar)
        r = dict(pilares=[ln["par"] for ln in linhas if ln["titulo"] in ("P5", "P7")], atualizar=True, ajustar=True,
                 origem=dict(edificio="X", planta="Primeiro", data=""), avisos={})
        with mock.patch("janela.app.DlgImportar") as dlg, \
                mock.patch("janela.app.messagebox.askokcancel", return_value=True) as aviso:
            dlg.return_value.mostrar.return_value = r
            self.app.importar_tqs()
        p7, p5 = self.app.projeto["pilares"]
        self.assertEqual((p7["bx"], p7["cob_s"], p7["cob_s0"], p7["cob_linhas"]), (40.0, 11.0, 7.0, 5))
        self.assertEqual(p5["cob_s0"], 7.0)
        texto = self.app.txm.get("1.0", "end")
        self.assertIn("P7: ajustado à NBR 6118", texto)


@unittest.skipUnless(TEM_TQS and EDIFICIO and os.path.isdir(EDIFICIO), "sem o TQS ou sem PUN_EDIFICIO_TESTE")
class TesteLeitorTQS(unittest.TestCase):
    """Lê o edifício numa cópia (o original não é tocado) e compara com a leitura gravada."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pun_e8_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_le_a_planta_e_gera_o_projeto(self):
        proj = os.path.join(self.tmp, "proj.json")
        saida = os.path.join(self.tmp, "leitura.json")
        r = subprocess.run([sys.executable, "-m", "dwg_tqs.leitor_tqs", "planta", EDIFICIO, "Primeiro", "--saida", saida,
                            "--projeto", proj], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=600)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(saida, encoding="utf-8") as f:
            lido = json.load(f)
        gravado = _ler("leitura_planta.json")
        for k in ("pilares", "lajes", "bordas", "cobrimentos", "concreto", "fck", "grelha", "repeticao", "projeto"):
            self.assertEqual(lido[k], gravado[k], k)
        with open(proj, encoding="utf-8") as f:
            p = json.load(f)
        self.assertEqual([q["titulo"] for q in p["pilares"]], ["P5", "P7", "P11"])

    def test_plantas_e_erros(self):
        r = subprocess.run([sys.executable, "-m", "dwg_tqs.leitor_tqs", "plantas", EDIFICIO], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=300)
        self.assertEqual([p["nome"] for p in json.loads(r.stdout)["plantas"]], ["Fundacao", "Primeiro"])
        r = subprocess.run([sys.executable, "-m", "dwg_tqs.leitor_tqs", "planta", self.tmp, "X"], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=300)
        self.assertEqual(r.returncode, 1)
        self.assertIn("não é a pasta de um edifício", json.loads(r.stdout)["erro"])


if __name__ == "__main__":
    unittest.main()
