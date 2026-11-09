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


P2X = dict(P2, bx=50, by=150, col_n_face_bx=3, col_n_face_by=8)     # o P2 girado: cobrinhas em x


class TesteFolhaX(unittest.TestCase):
    """Cobrinhas em x: os cortes e os detalhes embaixo da planta, alinhados com ela, face superior para cima."""

    @classmethod
    def setUpClass(cls):
        cls.res = detalhar(P2X)
        cls.f = prancha_cobrinha.montar(cls.res)

    def test_mesmos_ferros_do_p2(self):
        self.assertEqual(self.res["cobrinha"]["direcao"], "x")
        y = {f["pos"]: (f["quant"], f["comp"]) for f in detalhar(P2)["ferros"]}
        x = {f["pos"]: (f["quant"], f["comp"]) for f in self.res["ferros"]}
        self.assertEqual({k: x[k] for k in (1, 2, 3, 4)}, {k: y[k] for k in (1, 2, 3, 4)})
        self.assertEqual({x[5], x[6]}, {y[5], y[6]})                     # colapso com as faces trocadas

    def test_cobrinhas_horizontais(self):
        ins = [p for p in self.f.prims if p["t"] == "Bloco" and p["b"].startswith("COBRINHA")]
        self.assertEqual(len(ins), 26)
        self.assertEqual({p["ang"] for p in ins}, {-90.0})
        self.assertEqual({p["sy"] for p in ins}, {1.0, -1.0})

    def test_cortes_embaixo_da_planta_e_alinhados(self):
        reg = self.f.regioes
        self.assertLess(reg["corte"][3], reg["planta"][1])
        txt = {p["txt"]: p for p in self.f.prims if p["t"] == "Texto"}
        self.assertLess(txt["SEÇÃO A-A"]["y"], txt["SEÇÃO B-B"]["y"])      # A-A é a mais afastada
        self.assertEqual(txt["TOPO LAJE"]["a"], 0.0)
        gen = [p for p in self.f.prims if p["t"] == "Ferro" and p["tipo"] == "gen"]
        self.assertEqual(len(gen), 2)
        for p in gen:                                                   # trechos de cima acima dos de baixo
            self.assertEqual({round(y, 6) for _, y in p["pontos"]}, {0.0, self.res["cobrinha"]["altura_eixo"]})

    def test_so_niveis_dos_modelos(self):
        usados = {p["n"] for p in self.f.prims if "n" in p}
        usados |= {p["n"] for prims in self.f.blocos.values() if prims for p in prims}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)


class TesteGabarito(unittest.TestCase):
    """O DET. PLANTA (gabarito a 1:25, com a altura do pilar) não desce sobre os títulos das vistas. Antes, com
    by >= 150, ele invadia o título "VISTA EM PLANTA (COLAPSO PROGRESSIVO)" (relato do usuário de 09/11/2026)."""

    def _caixa(self, par):
        pr = prancha_cobrinha.Prancha(detalhar(par))
        f = pr.montar()
        return pr, f

    def test_nao_invade_os_titulos(self):
        from nucleo.folha import H_VISTA
        for direcao in ("x", "y"):
            for bx in (20, 40, 80, 150, 200):
                for by in (20, 50, 100, 150, 200, 300):
                    with self.subTest(direcao=direcao, bx=bx, by=by):
                        pr, f = self._caixa(dict(P2, bx=bx, by=by, cob_direcao=direcao, col_n_face_bx=2,
                                                 col_n_face_by=2))
                        x0, y0, x1, y1 = pr.caixa_gabarito
                        topo_titulos = pr.y_tit + H_VISTA * pr.E
                        self.assertGreaterEqual(y0, topo_titulos + 0.5 * pr.E)
                        moldura = f.prims[-1]                                    # a moldura cobre o gabarito
                        ys = [y for _, y in moldura["xy"]] if "xy" in moldura else [moldura["y1"], moldura["y2"]]
                        self.assertGreaterEqual(max(ys), y1)

    def test_faixa_do_modelo_nao_muda(self):
        pr, _ = self._caixa(P2)                                             # by = 50: gabarito baixo
        self.assertAlmostEqual(pr.caixa_gabarito[3], pr.y_tit + 1.2 * pr.E + 9.0 * pr.E)


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

    def test_p2_em_x_pelo_tqs(self):
        from dwg_tqs import prancha
        pasta = tempfile.mkdtemp(prefix="pun_e2x_")
        try:
            g = prancha.gerar(detalhar(P2X), pasta)
            self.assertTrue(g["confere"], (g["tabela_tqs"], g["esperado"]))
            self.assertEqual(g["tabela_tqs"], [(1, 18, 10.0, 167), (2, 8, 10.0, 472), (3, 8, 12.5, 335),
                                               (4, 8, 12.5, 95), (5, 8, 10.0, 220), (6, 3, 10.0, 320)])
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
