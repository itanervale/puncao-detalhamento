# -*- coding: utf-8 -*-
"""
E6: relatório do lote (nucleo/relatorio.py), sem o TQS: aço por pilar e por bitola (NBR 7480), pentes somados,
comprimentos do TQS quando o pilar foi gravado, pilares com erro, formato dos CSV (Excel), o detalhar.py com
--so-relatorio e o botão da janela (este, só com tela).

Uso:  python -m unittest testes.teste_e6_relatorio -v
"""
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import relatorio as R                                      # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402
from nucleo.parametros import ler_projeto                              # noqa: E402

LOTE = os.path.join(RAIZ, "exemplos", "lote_conectores.json")
P02 = dict(titulo="P02", bx=50, by=150, h_laje=27, c_sup=2.5, c_inf=2.5, solucao="conectores",
           col_n_face_bx=3, col_n_face_by=8, con_n_face_bx=3, con_n_face_by=5)
DATA = datetime(2026, 11, 9, 10, 30)

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


def _rel(pilares, tqs=None):
    return R.montar([R.item(detalhar(p), (tqs or {}).get(p.get("titulo"))) for p in pilares], projeto="teste",
                    data=DATA)


class TesteNumeros(unittest.TestCase):
    def test_massa_linear_nbr7480(self):
        self.assertEqual(R.massa_linear(10), 0.617)
        self.assertEqual(R.massa_linear(12.5), 0.963)
        self.assertEqual(R.massa_linear(6.3), 0.245)
        self.assertAlmostEqual(R.massa_linear(14), 1.208, places=3)       # fora da tabela: ø² · π/4 · 7850

    def test_aco_do_p02(self):
        rel = _rel([P02])
        q, = rel["pilares"]
        self.assertAlmostEqual(q["aco"], 8 * 2.20 * 0.617 + 3 * 3.20 * 0.617, places=6)    # 16,78 kg
        self.assertEqual(q["fonte"], "núcleo")
        self.assertEqual(q["dwg"], "não gravado")
        self.assertIn("20 pentes PUN 3P 17 cm", q["armadura"])

    def test_repeticoes_e_resumo_por_bitola(self):
        pil = ler_projeto(LOTE)["pilares"]
        rel = _rel(pil)
        p5 = next(q for q in rel["pilares"] if q["pilar"] == "P5")
        self.assertEqual(p5["rep"], 2)
        self.assertAlmostEqual(p5["aco_rep"], 2 * p5["aco"])
        tot_ferros = sum(f["kg_rep"] for f in rel["ferros"])
        self.assertAlmostEqual(sum(r["kg"] for r in rel["resumo"]), tot_ferros)
        self.assertEqual([r["bitola"] for r in rel["resumo"]], [8.0, 10.0])   # a montagem do P9 é ø8
        self.assertEqual(rel["n_com_rep"], 6)

    def test_pentes_somados(self):
        rel = _rel(ler_projeto(LOTE)["pilares"])
        por = {(c["bloco"], c["comprimento_mm"]): (c["pentes"], c["pinos"]) for c in rel["conectores"]}
        self.assertEqual(por, {("PUN 3P 17 cm", 220): (20, 60),
                               ("PUN 3P 17 cm", 200): (16 * 2 + 20 + 14, (16 * 2 + 20 + 14) * 3),
                               ("PUN 5P 17 cm", 250): (20, 100)})

    def test_comprimentos_do_tqs(self):
        tqs = {"P02": dict(tabela_tqs=[(1, 8, 10.0, 221), (2, 3, 10.0, 320)], confere=False,
                           arquivos=dict(dwg=r"C:\x\PUN_P02.DWG"))}
        rel = _rel([P02], tqs)
        q, = rel["pilares"]
        self.assertEqual((q["fonte"], q["conferencia"], q["dwg"]), ("TQS", "difere", "PUN_P02.DWG"))
        self.assertEqual(rel["ferros"][0]["comp"], 221)
        self.assertEqual(rel["n_difere"], 1)
        self.assertIn("pelo TQS em 1 de 1 pilar(es) (1 difere do núcleo).", rel["texto"])

    def test_pilar_com_erro(self):
        rel = _rel([P02, dict(P02, titulo="PX", con_dist_canto=40)])
        self.assertEqual([q["pilar"] for q in rel["pilares"]], ["P02", "PX"])
        self.assertEqual(rel["pilares"][1]["erros"], 1)
        self.assertFalse([f for f in rel["ferros"] if f["pilar"] == "PX"])
        self.assertIn("ERROS (1)", rel["texto"])

    def test_texto(self):
        t = _rel(ler_projeto(LOTE)["pilares"])["texto"]
        for trecho in ("RELATÓRIO DO LOTE", "Data: 09/11/2026 10:30", "PILARES", "FERROS", "RESUMO DE AÇO",
                       "CONECTORES", "AVISOS (", "pelo núcleo"):
            self.assertIn(trecho, t)


class TesteArquivos(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="pun_e6_")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_csv_para_o_excel(self):
        arqs = R.gravar(_rel(ler_projeto(LOTE)["pilares"]), self.pasta, "lote")
        self.assertEqual(sorted(os.path.basename(v) for v in arqs.values()),
                         ["RELATORIO_lote.txt", "RELATORIO_lote_ferros.csv", "RELATORIO_lote_pilares.csv"])
        with open(arqs["ferros"], "rb") as f:
            self.assertEqual(f.read(3), b"\xef\xbb\xbf")                      # BOM: o Excel lê o UTF-8
        with open(arqs["ferros"], encoding="utf-8-sig", newline="") as f:
            linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(linhas[0][:4], ["Pilar", "Repetições", "Posição", "Quantidade"])
        self.assertEqual(linhas[1][:9], ["P02", "1", "N1", "8", "10", "220", "17,60", "10,86", "10,86"])
        with open(arqs["pilares"], encoding="utf-8-sig", newline="") as f:
            linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(len(linhas), 6)
        self.assertIn(";", linhas[1][7])                                     # a armadura, entre aspas

    def test_linha_de_comando_so_relatorio(self):
        r = subprocess.run([sys.executable, os.path.join(RAIZ, "detalhar.py"), LOTE, "--so-relatorio",
                            "--saida", self.pasta], capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Relatório do lote", r.stdout)
        self.assertFalse([a for a in os.listdir(self.pasta) if a.upper().endswith(".DWG")])
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "RELATORIO_lote_conectores.txt")))


@unittest.skipUnless(TEM_TELA, "sem tela para o Tk")
class TesteJanela(unittest.TestCase):
    def test_botao_relatorio_do_lote(self):
        from janela.app import App
        pasta = tempfile.mkdtemp(prefix="pun_e6j_")
        a = App()
        try:
            a.withdraw()
            a.abrir(LOTE)
            a.pasta.set(pasta)
            arqs = a.relatorio_lote(abrir=False)
            self.assertTrue(os.path.exists(arqs["txt"]))
            self.assertIn("Relatório do lote", a.txm.get("1.0", "end"))
        finally:
            a.modificado = False
            a.destroy()
            shutil.rmtree(pasta, ignore_errors=True)

    @unittest.skipUnless(TEM_TQS, "sem o TQS")
    def test_gerar_o_lote_grava_o_relatorio(self):
        from janela.app import App
        pasta = tempfile.mkdtemp(prefix="pun_e6t_")
        a = App()
        try:
            a.withdraw()
            a.abrir(os.path.join(RAIZ, "exemplos", "P02_conectores.json"))
            a.pasta.set(pasta)
            a.gerar_lote()
            t0 = time.time()
            while (a.ocupado or not a.arq_relatorio) and time.time() - t0 < 120:
                a.update()
                time.sleep(0.05)
            self.assertTrue(a.arq_relatorio)
            with open(a.arq_relatorio["txt"], encoding="utf-8") as f:
                t = f.read()
            self.assertIn("pelo TQS em 1 de 1 pilar(es) (todos conferem com o núcleo).", t)
            self.assertIn("PUN_P02.DWG (confere)", t)
        finally:
            a.modificado = False
            a.destroy()
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
