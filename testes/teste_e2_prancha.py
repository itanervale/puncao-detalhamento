# -*- coding: utf-8 -*-
"""
E2: prancha da cobrinha. Sem o TQS, confere a folha em primitivas (blocos, ferros e só os níveis dos desenhos de
referência); com o TQS, grava o DWG do P2 numa pasta temporária e confere os comprimentos que o TQS calcula.

Uso:  python -m unittest testes.teste_e2_prancha -v
"""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import prancha_cobrinha                                    # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402

try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False

P2 = dict(titulo="P2", bx=150, by=50, h_laje=27, c_sup=2.0, c_inf=2.0, solucao="cobrinha",
          col_n_face_bx=8, col_n_face_by=3)
# Níveis usados nos dois desenhos de referência (PADRAO_desenho.md, seção 3): a prancha não pode usar outros.
NIVEIS_MODELOS = {0, 1, 79, 200, 202, 203, 204, 205, 210, 220, 221, 222, 224, 225, 226, 227, 233, 240, 241, 242,
                  243, 244, 245, 246, 253, 254}


class TesteFolha(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = detalhar(P2)
        cls.f = prancha_cobrinha.montar(cls.res)

    def test_ferros(self):
        ferros = [p for p in self.f.prims if p["t"] == "Ferro"]
        self.assertEqual(sorted((p["mark"], p["quant"], p["tipo"]) for p in ferros),
                         [(1, 18, "gen"), (2, 8, "gen"), (3, 8, "reto"), (4, 8, "reto"), (5, 3, "reto"),
                          (6, 8, "reto")])
        niveis = {i["nivel"] for p in ferros for i in p["ins"]}
        self.assertEqual(niveis, {242, 244, 246})          # cobrinha, montagem e colapso, como no modelo

    def test_blocos_das_cobrinhas_com_a_bitola_real(self):
        self.assertIn("COBRINHA N1 10", self.f.blocos)
        self.assertIn("COBRINHA N2 10", self.f.blocos)
        larg = {round(abs(p["xy"][0][0]), 3) for p in self.f.blocos["COBRINHA N1 10"] if p["t"] == "Linha"}
        self.assertEqual(larg, {0.5})                       # ø10: linhas a ±0,5 do eixo
        insercoes = [p for p in self.f.prims if p["t"] == "Bloco" and p["b"].startswith("COBRINHA")]
        self.assertEqual(len(insercoes), 26)                # 18 peças da face + 8 inteiras

    def test_so_niveis_dos_modelos(self):
        usados = {p["n"] for p in self.f.prims if "n" in p}
        usados |= {p["n"] for prims in self.f.blocos.values() if prims for p in prims}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)
        self.assertFalse({n for n in usados if 1 <= n <= 199})

    def test_textos_principais(self):
        txt = {p["txt"] for p in self.f.prims if p["t"] == "Texto"}
        for t in ("P2", "1X", "(150x50)", "SEÇÃO A-A", "SEÇÃO B-B", "VISTA EM PLANTA (ARM. PUNÇÃO)",
                  "VISTA EM PLANTA (COLAPSO PROGRESSIVO)", "DET. PLANTA", "NOTAS IMPORTANTES", "PENTE MESTRE"):
            self.assertIn(t, txt)


@unittest.skipUnless(TEM_TQS, "sem o TQS")
class TesteDWG(unittest.TestCase):
    def test_p2_pelo_tqs(self):
        from dwg_tqs import prancha
        pasta = tempfile.mkdtemp(prefix="pun_e2_")
        try:
            g = prancha.gerar(detalhar(P2), pasta)
            self.assertTrue(g["confere"], (g["tabela_tqs"], g["esperado"]))
            self.assertEqual(g["tabela_tqs"], [(1, 18, 10.0, 167), (2, 8, 10.0, 472), (3, 8, 12.5, 335),
                                               (4, 8, 12.5, 95), (5, 3, 10.0, 320), (6, 8, 10.0, 220)])
            for k in ("dwg", "pdf", "dxf"):
                self.assertTrue(os.path.exists(g["arquivos"][k]), k)
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
