# -*- coding: utf-8 -*-
"""
E1: o núcleo da cobrinha reproduz o desenho de referência PUN_P02-R01 (sem o TQS). Os valores esperados foram lidos
do modelo (PADRAO_desenho.md); não dependem da pasta DesenhosReferencia.

Uso:  python -m unittest testes.teste_e1_cobrinha -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import cobrinha, parametros                               # noqa: E402
from nucleo.detalhe import detalhar                                   # noqa: E402

P2 = dict(titulo="P2", bx=150, by=50, h_laje=27, c_sup=2.0, c_inf=2.0, solucao="cobrinha",
          col_n_face_bx=8, col_n_face_by=3)

# Pontos do ferro genérico N1 no modelo (relativos à inserção; x = -22 é o trecho de cima, 0 o de baixo).
MODELO_N1 = [(-22, 50), (-22, 67), (0, 67), (0, 84), (-22, 84), (-22, 101), (0, 101), (0, 118), (-22, 118),
             (-22, 135), (0, 135), (0, 154), (-22, 154), (-22, 173), (0, 173), (0, 190), (-22, 190), (-22, 207),
             (0, 207), (0, 224), (-22, 224), (-22, 241), (0, 241), (0, 258)]
# No modelo, a 1ª perna (y = 67 acima) fica a 62 cm abaixo da face do pilar: u = y - 129.
DESLOC_N1 = 129


class TesteMalha(unittest.TestCase):
    def test_vao_172_dois_espacos_de_18_no_meio(self):
        pos, esp = cobrinha.posicoes_malha(150, 11, 17, 4)
        self.assertEqual(pos, [-62, -45, -28, -11, 6, 23, 40, 57, 75, 93, 110, 127, 144, 161, 178, 195, 212])
        self.assertEqual(esp[3:13], [17, 17, 17, 17, 18, 18, 17, 17, 17, 17])

    def test_vao_72_dois_espacos_de_19_no_meio(self):
        pos, esp = cobrinha.posicoes_malha(50, 11, 17, 4)
        self.assertEqual(pos, [-62, -45, -28, -11, 6, 25, 44, 61, 78, 95, 112])
        self.assertEqual(esp, [17, 17, 17, 17, 19, 19, 17, 17, 17, 17])

    def test_numero_impar_de_espacos_sobra_no_espaco_do_meio(self):
        pos, esp = cobrinha.posicoes_malha(40, 11, 17, 1)     # vão 62: 3 espaços, sobra 11
        self.assertEqual(esp, [17, 28, 17])
        self.assertEqual(pos, [-11, 6, 34, 51])

    def test_simetria(self):
        for L in (20, 33, 47, 90, 151):
            pos, _ = cobrinha.posicoes_malha(L, 11, 17, 4)
            self.assertEqual([round(a + b, 4) for a, b in zip(pos, reversed(pos))], [L] * len(pos))


class TesteP2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = detalhar(P2)
        cls.c = cls.r["cobrinha"]

    def test_sem_erros_nem_avisos(self):
        self.assertEqual(self.r["erros"], [])
        self.assertEqual([v for v in self.r["verificacoes"] if v[0] == "aviso"], [])
        self.assertAlmostEqual(self.r["d"], 23.0)

    def test_ferros_do_modelo(self):
        self.assertEqual([(f["pos"], f["quant"], f["bitola"], f["comp"]) for f in self.r["ferros"]],
                         [(1, 17, 10.0, 450), (2, 11, 12.5, 395), (3, 3, 10.0, 320), (4, 8, 10.0, 220)])

    def test_cobrinhas_paralelas_ao_lado_menor(self):
        self.assertEqual(self.c["direcao"], "y")
        self.assertEqual(self.c["n_cobrinhas"], 17)
        self.assertEqual(self.c["n_pernas"], 11)
        self.assertEqual(self.c["altura_eixo"], 22)

    def test_pontos_iguais_aos_do_modelo(self):
        esperado = [(y - DESLOC_N1, "sup" if x == -22 else "inf") for x, y in MODELO_N1]
        self.assertEqual(self.c["pontos"], esperado)

    def test_montagem_na_dobra_de_baixo_como_no_modelo(self):
        # no modelo, a N2 fica a +1,5 / -1,5 do eixo de cada perna, alternando (dobra de baixo)
        sinais_modelo = [+1, -1] * 5 + [+1]
        sinais = [1 if m > u else -1 for m, u in zip(self.c["mont_pos"], self.c["pernas"])]
        self.assertEqual(sinais, sinais_modelo)
        self.assertAlmostEqual(self.c["mont_afast"], 1.125)       # (ø10 + ø12,5)/2, encostada na perna
        self.assertEqual((self.c["mont_ini"], self.c["mont_fim"]), (-122, 272))

    def test_colapso(self):
        em_x, em_y = self.r["colapso"]
        self.assertEqual([round(v, 2) for v in em_x["pos"]], [8.33, 25.0, 41.67])
        self.assertEqual(em_y["pos"], [9.375 + 18.75 * i for i in range(8)])
        self.assertEqual((em_x["ini"], em_x["fim"], em_y["ini"], em_y["fim"]), (-85, 235, -85, 135))

    def test_gabarito(self):
        self.assertEqual(self.c["gabarito"], (-11, -11, 161, 61))


class TesteVariacoes(unittest.TestCase):
    def test_cobrimento_25_encurta_a_cobrinha_e_avisa(self):
        r = detalhar(dict(P2, c_sup=2.5, c_inf=2.5))
        self.assertEqual(r["ferros"][0]["comp"], 439)              # pernas de 21 pelo eixo
        self.assertAlmostEqual(r["d"], 22.5)
        self.assertEqual(sum(1 for v in r["verificacoes"] if v[0] == "aviso"), 2)   # 17 > 0,75d em x e y

    def test_outra_direcao(self):
        r = detalhar(dict(P2, cob_direcao="maior"))
        c = r["cobrinha"]
        self.assertEqual((c["direcao"], c["n_cobrinhas"], c["n_pernas"]), ("x", 11, 17))

    def test_erros(self):
        self.assertTrue(detalhar(dict(P2, bx=0))["erros"])
        self.assertTrue(detalhar(dict(P2, h_laje=5))["erros"])
        self.assertTrue(detalhar(dict(P2, cob_linhas=0))["erros"])
        self.assertTrue(detalhar(dict(P2, solucao="outra"))["erros"])

    def test_altura_util(self):
        p, _ = parametros.normalizar(dict(P2, neg_bitola_ext=12.5, neg_bitola_int=10))
        self.assertAlmostEqual(parametros.altura_util(p), 27 - 2 - 1 - (3 * 1.25 + 1.0) / 4)
        p, _ = parametros.normalizar(dict(P2, d=21))
        self.assertEqual(parametros.altura_util(p), 21)


if __name__ == "__main__":
    unittest.main()
