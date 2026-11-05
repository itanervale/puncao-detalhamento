# -*- coding: utf-8 -*-
"""
E4: prancha dos conectores. Sem o TQS, confere a folha em primitivas contra o desenho de referência PUN_P02
(contagens de blocos e cotas, só níveis dos modelos, textos, quadro, blocos com as correções do pino ø10, da cabeça
de 32 mm e dos trilhos ø8); com o TQS, grava o DWG do P02 e o de um pilar com a montagem opcional e confere os
comprimentos que o TQS calcula.

Uso:  python -m unittest testes.teste_e4_prancha_conectores -v
"""
import math
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import prancha_conectores                                  # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402

try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False

P02 = dict(titulo="P02", bx=50, by=150, h_laje=27, c_sup=2.5, c_inf=2.5, solucao="conectores",
           col_n_face_bx=3, col_n_face_by=8, con_n_face_bx=3, con_n_face_by=5)
P9 = dict(titulo="P9", bx=60, by=60, h_laje=25, solucao="conectores", con_montagem=True, mont_bitola=8,
          col_n_face_bx=4, col_n_face_by=4, con_n_face_bx=4, con_n_face_by=4)
# Níveis usados nos dois desenhos de referência (PADRAO_desenho.md, seção 3): a prancha não pode usar outros.
NIVEIS_MODELOS = {0, 1, 79, 200, 202, 203, 204, 205, 210, 220, 221, 222, 224, 225, 226, 227, 233, 240, 241, 242,
                  243, 244, 245, 246, 253, 254}


class TesteFolhaP02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = prancha_conectores.montar(detalhar(P02))

    def _tipo(self, t):
        return [p for p in self.f.prims if p["t"] == t]

    def test_contagens_do_modelo(self):
        blocos = self._tipo("Bloco")
        nomes = sorted({b["b"] for b in blocos})
        self.assertEqual(nomes, ["C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA", "PUN 3P 17 cm", "Pino 22 cm em corte"])
        self.assertEqual(sum(b["b"] == "PUN 3P 17 cm" for b in blocos), 20)
        self.assertEqual(sum(b["b"] == "Pino 22 cm em corte" for b in blocos), 12)   # 6 no corte e 6 no pente
        self.assertEqual(len(self._tipo("Cota")), 44)                                # as 44 cotas do modelo

    def test_pentes_nas_posicoes_do_modelo(self):
        ins = {(round(b["x"], 3), round(b["y"], 3), round(b["ang"] % 360, 3))
               for b in self._tipo("Bloco") if b["b"] == "PUN 3P 17 cm"}
        self.assertIn((-11.0, 75.0, 180.0), ins)
        self.assertIn((round(50 + 11 / math.sqrt(2), 3), round(-11 / math.sqrt(2), 3), 315.0), ins)

    def test_bloco_do_pente_corrigido(self):
        bl = self.f.blocos["PUN 3P 17 cm"]
        circ = sorted({(p["n"], p["r"]) for p in bl if p["t"] == "Circulo"})
        self.assertEqual(circ, [(241, 1.6), (245, 0.5)])                  # cabeça de 32 mm e fuste ø10
        ys = sorted({round(abs(p["xy"][0][1]), 3) for p in bl if p["t"] == "Linha" and
                     abs(p["xy"][0][1] - p["xy"][1][1]) < 1e-9})
        self.assertEqual(ys, [1.6, 2.4])                                  # trilho ø8 encostado na cabeça
        pino = self.f.blocos["Pino 22 cm em corte"][0]["xy"]
        self.assertEqual(max(x for x, _ in pino), 3.2)
        self.assertEqual(max(y for _, y in pino), 22.0)
        self.assertAlmostEqual(pino[3][0] - pino[-3][0], 1.0)             # fuste de 10 mm no corte

    def test_so_niveis_dos_modelos(self):
        usados = {p["n"] for p in self.f.prims if "n" in p}
        usados |= {p["n"] for prims in self.f.blocos.values() if prims for p in prims}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)
        self.assertFalse({n for n in usados if 1 <= n <= 199})

    def test_textos_e_quadro(self):
        txt = {p["txt"] for p in self._tipo("Texto")}
        for t in ("P02", "1X", "(50x150)", "VISTA EM PLANTA (PINOS)", "VISTA EM PLANTA (COLAPSO PROGRESSIVO)",
                  "CORTE A-A", "TOPO LAJE", "NOTA 1", "NOTA 2", "NOTA 3", "NOTAS IMPORTANTES", "N2",
                  "ARMADURA DE COMBATE À PUNÇÃO", "QUANTIDADE: 1 x 20 PENTES", "DESCRIÇÃO: 3 { 10 mm (CA-50)",
                  "com 220 mm + 2 { 8 mm (CA-50)"):
            self.assertIn(t, txt)

    def test_leiaute_do_modelo(self):
        x1, y1, x2, y2 = (round(v, 3) for v in self.f.extensao())
        self.assertEqual((x1, y1, x2, y2), (-106.0, -225.5, 434.0, 320.0))   # a moldura do modelo
        quadro = [p for p in self._tipo("Polyline") if p["n"] == 240 and p["xy"][0] == [279.0, 281.0]]
        self.assertEqual(len(quadro), 1)

    def test_cotas_39_legiveis(self):
        cantos = [p for p in self._tipo("Cota") if p["modo"] == "a"]
        self.assertEqual([c["txt"] for c in cantos], ["39"] * 8)
        for c in cantos:                                                  # da esquerda para a direita
            self.assertLess((c["p1"][0], c["p1"][1]), (c["p2"][0], c["p2"][1]))

    def test_ferros_do_colapso(self):
        ferros = sorted((p["mark"], p["quant"], p["comp"], p["ins"][0]["x"], p["ins"][0]["y"], p["ins"][0]["ang"])
                        for p in self._tipo("Ferro"))
        self.assertEqual(ferros, [(1, 8, 220, -85, 250, 0.0), (2, 3, 320, 149, -85, 90.0)])   # como no modelo


class TesteOutrasGeometrias(unittest.TestCase):
    def test_lote_sem_erro_e_dentro_da_moldura(self):
        casos = [P9, {**P02, "con_pinos": 5, "titulo": "P5"}, {**P02, "con_inclinados": "cruz"},
                 dict(titulo="P3", bx=30, by=80, h_laje=30, solucao="conectores", con_pinos=5,
                      con_n_face_bx=2, con_n_face_by=4, col_n_face_bx=2, col_n_face_by=4)]
        for par in casos:
            f = prancha_conectores.montar(detalhar(par))
            moldura = [p for p in f.prims if p["t"] == "Polyline" and p["n"] == 0][-1]["xy"]
            xs, ys = [q[0] for q in moldura], [q[1] for q in moldura]
            x1, y1, x2, y2 = f.extensao()
            self.assertGreaterEqual(x1, min(xs) - 1e-6, par["titulo"])
            self.assertGreaterEqual(y1, min(ys) - 1e-6, par["titulo"])
            self.assertLessEqual(y2, max(ys) + 1e-6, par["titulo"])

    def test_montagem_desenhada_e_identificada(self):
        f = prancha_conectores.montar(detalhar(P9))
        self.assertEqual(sum(1 for p in f.prims if p["t"] == "Linha" and p["n"] == 243), 12)
        ferros = sorted((p["mark"], p["quant"], p["comp"]) for p in f.prims if p["t"] == "Ferro")
        self.assertEqual(ferros, [(1, 4, 230), (2, 4, 230), (3, 6, 110), (4, 6, 110)])


@unittest.skipUnless(TEM_TQS, "sem o TQS")
class TesteDWG(unittest.TestCase):
    def test_pelo_tqs(self):
        from dwg_tqs import prancha
        pasta = tempfile.mkdtemp(prefix="pun_e4_")
        try:
            g = prancha.gerar(detalhar(P02), pasta)
            self.assertTrue(g["confere"], (g["tabela_tqs"], g["esperado"]))
            self.assertEqual(g["tabela_tqs"], [(1, 8, 10.0, 220), (2, 3, 10.0, 320)])
            for k in ("dwg", "pdf", "dxf"):
                self.assertTrue(os.path.exists(g["arquivos"][k]), k)
            g = prancha.gerar(detalhar(P9), pasta)
            self.assertEqual(g["tabela_tqs"], [(1, 4, 10.0, 230), (2, 4, 10.0, 230), (3, 6, 8.0, 110),
                                               (4, 6, 8.0, 110)])
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
