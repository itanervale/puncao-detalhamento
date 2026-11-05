# -*- coding: utf-8 -*-
"""
E5: janela (Tk). A colagem do Excel não precisa de tela; a prévia e o uso da janela (abrir o lote, editar um campo,
trocar de pilar, duplicar, colar, salvar e reabrir) precisam do Tk com tela e são pulados sem ela. Nada aqui usa o
TQS.

Uso:  python -m unittest testes.teste_e5_janela -v
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from janela.app import interpretar_colagem, mesclar_colagem            # noqa: E402

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

LOTE = os.path.join(RAIZ, "exemplos", "lote_conectores.json")


class TesteColagem(unittest.TestCase):
    def test_excel_com_cabecalho(self):
        txt = "Pilar\tbx\tby\th\tRep\tSolução\nP10\t40\t80\t25\t2\tconectores\nP11\t50,5\t50\t22\t\tcobrinha\n"
        self.assertEqual(interpretar_colagem(txt), [
            dict(titulo="P10", bx=40, by=80, h_laje=25, repeticoes=2, solucao="conectores"),
            dict(titulo="P11", bx=50.5, by=50, h_laje=22, solucao="cobrinha")])

    def test_colados_herdam_o_pilar_atual(self):
        base = dict(titulo="P02", bx=50, by=150, h_laje=27, solucao="conectores", con_pinos=4, repeticoes=2)
        q, = mesclar_colagem(base, [dict(titulo="P9", bx=40, by=40, h_laje=25)])
        self.assertEqual(q, dict(titulo="P9", bx=40, by=40, h_laje=25, solucao="conectores", con_pinos=4))
        q, = mesclar_colagem(base, [dict(titulo="P9", bx=40, by=40, h_laje=25, solucao="cobrinha")])
        self.assertEqual(q["solucao"], "cobrinha")

    def test_ponto_e_virgula_e_erros(self):
        self.assertEqual(interpretar_colagem("P1;30;60;20;3x"),
                         [dict(titulo="P1", bx=30, by=60, h_laje=20, repeticoes=3)])
        with self.assertRaises(ValueError):
            interpretar_colagem("P1;30;60")                       # faltam colunas
        with self.assertRaises(ValueError):
            interpretar_colagem("P1;30;60;20\nP2;x;60;20")        # número inválido depois da 1ª linha
        with self.assertRaises(ValueError):
            interpretar_colagem("P1;30;60;20;1;estribo")


@unittest.skipUnless(TEM_TELA, "sem tela para o Tk")
class TesteJanela(unittest.TestCase):
    def setUp(self):
        from janela.app import App
        self.pasta = tempfile.mkdtemp(prefix="pun_e5_")
        self.app = App()
        self.app.withdraw()
        self.app.abrir(LOTE)
        self.app.update()

    def tearDown(self):
        self.app.modificado = False
        self.app.destroy()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_abre_o_lote_e_desenha(self):
        a = self.app
        self.assertEqual(len(a.projeto["pilares"]), 5)
        self.assertFalse(a.res["erros"])
        self.assertGreater(len(a.vista.find_all()), 500)
        self.assertIn("f:1", a.info)                          # o ferro N1 tem chave para a dica e a seleção
        self.assertTrue(any(k.startswith("b:") for k in a.info))
        self.assertTrue(a.tv.exists("pilar:4") and a.tv.exists("ferro:2"))

    def test_editar_campo_e_trocar_de_pilar(self):
        a = self.app
        a.v["con_pinos"].set("5")
        a._mudou("con_pinos")
        a.atualizar()
        self.assertEqual(a.pilar["con_pinos"], 5)
        self.assertEqual(a.res["conectores"]["nome_bloco"], "PUN 5P 17 cm")
        self.assertTrue(a.modificado)
        a.v["con_pinos"].set("3")                             # volta ao padrão: sai do dicionário do pilar
        a._mudou("con_pinos")
        self.assertNotIn("con_pinos", a.pilar)
        a.ir(1)
        self.assertEqual(a.res["p"]["titulo"], "P5")
        self.assertEqual(a.v["titulo"].get(), "P5")
        self.assertEqual(a.v["repeticoes"].get(), "2")

    def test_vistas_e_cores(self):
        a = self.app
        for k in ("planta", "corte", "colapso", "prancha"):
            a.ver(k)
            a.update()
            self.assertIn(k, a.folha.regioes)
        a.plot.set(True)
        a._redesenhar()
        self.assertEqual(a.vista.cget("bg"), "#ffffff")
        a.ver_tabela("lote")
        a.update()
        self.assertEqual(len(a.tt.get_children()), 5)
        a.ver_tabela("ferros")
        self.assertEqual(len(a.tt.get_children()), 3)          # N1, N2 e o total

    def test_lote_duplicar_colar_salvar_reabrir(self):
        a = self.app
        a.duplicar()
        self.assertEqual(len(a.projeto["pilares"]), 6)
        self.assertEqual(a.res["p"]["titulo"], "P02-2")
        a.projeto["pilares"] += mesclar_colagem(a.pilar, interpretar_colagem("P20\t45\t90\t26\t3"))
        arq = os.path.join(self.pasta, "lote.json")
        a._gravar(arq)
        with open(arq, encoding="utf-8") as f:
            dados = json.load(f)
        self.assertEqual(dados["formato"], "puncao-detalhamento")
        self.assertEqual([p["titulo"] for p in dados["pilares"]], ["P02", "P02-2", "P5", "P7", "P9", "P11", "P20"])
        a.abrir(arq)
        a.ir(6)
        self.assertEqual((a.res["p"]["bx"], a.res["p"]["by"], a.res["p"]["repeticoes"]), (45, 90, 3))
        self.assertFalse(a.res["erros"])

    @unittest.skipUnless(TEM_TQS, "sem o TQS")
    def test_gerar_pelo_tqs_numa_thread(self):
        a = self.app
        a.pasta.set(self.pasta)
        a.gerar()
        t0 = time.time()
        while (a.ocupado or "P02" not in a.arquivos) and time.time() - t0 < 120:
            a.update()
            time.sleep(0.05)
        self.assertIn("P02", a.arquivos)
        self.assertTrue(os.path.exists(a.arquivos["P02"]["dwg"]))
        self.assertIn("confere com o núcleo", a.txm.get("1.0", "end"))

    def test_erro_de_parametro_nao_derruba(self):
        a = self.app
        a.v["bx"].set("abc")
        a._mudou("bx")                                       # valor inválido: só avisa no status
        self.assertEqual(a.pilar["bx"], 50)
        a.v["con_dist_canto"].set("40")
        a._mudou("con_dist_canto")
        a.atualizar()
        self.assertTrue(a.res["erros"])
        self.assertIsNone(a.folha)
        a.v["con_dist_canto"].set("5")
        a._mudou("con_dist_canto")
        a.atualizar()
        self.assertFalse(a.res["erros"])


if __name__ == "__main__":
    unittest.main()
