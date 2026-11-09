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
        with mock.patch("janela.app.DlgImportar") as dlg:
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
        for k in ("pilares", "lajes", "bordas", "cobrimentos", "grelha", "repeticao", "projeto"):
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
