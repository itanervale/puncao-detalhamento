# -*- coding: utf-8 -*-
"""
E1: núcleo da cobrinha (sem o TQS). Malha do desenho de referência PUN_P02-R01, com as regras do usuário de
03/11/2026: nada por cima do pilar, as peças diante das faces começam na face pelo trecho de baixo, as linhas ao
lado do pilar são inteiras com número ímpar de espaços ao lado da face (Q6), montagem interrompida nas faces e
30 cm além da última linha.

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

    def test_pernas_ao_lado_numero_impar_de_espacos(self):
        self.assertEqual(cobrinha.pernas_ao_lado(50, 11, 17), [3.5, 18.0, 32.0, 46.5])     # 5 x ~14,4
        for L in (20, 33, 40, 47, 80, 90, 151):
            meio = cobrinha.pernas_ao_lado(L, 11, 17)
            todas = [-11] + meio + [L + 11]
            esp = [b - a for a, b in zip(todas, todas[1:])]
            self.assertEqual(len(esp) % 2, 1, L)                        # ímpar
            self.assertTrue(all(e <= 17.5 for e in esp), (L, esp))    # <= s (+ arredondamento de 0,5)
            self.assertEqual([round(a + b, 4) for a, b in zip(todas, reversed(todas))], [L] * len(todas))


class TesteP2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = detalhar(P2)
        cls.c = cls.r["cobrinha"]

    def test_sem_erros_nem_avisos(self):
        self.assertEqual(self.r["erros"], [])
        self.assertEqual([v for v in self.r["verificacoes"] if v[0] == "aviso"], [])
        self.assertAlmostEqual(self.r["d"], 23.0)

    def test_ferros(self):
        self.assertEqual([(f["pos"], f["quant"], f["bitola"], f["comp"]) for f in self.r["ferros"]],
                         [(1, 18, 10.0, 167), (2, 8, 10.0, 472),          # 79 + 4 x 22 e 208 + 12 x 22
                          (3, 8, 12.5, 335), (4, 8, 12.5, 95),            # 274 + 2 x 30 e 62 + 30
                          (5, 3, 10.0, 320), (6, 8, 10.0, 220)])

    def test_malha_do_modelo(self):
        self.assertEqual(self.c["direcao"], "y")                      # paralelas ao lado menor
        self.assertEqual(self.c["n_linhas"], 17)
        self.assertEqual(self.c["altura_eixo"], 22)

    def test_peca_da_face_para_fora(self):
        pc = next(p for p in self.c["pecas"] if p["tipo"] == "extremidade" and p["ini"] == 0)
        self.assertEqual(pc["pontos"], [(0, "inf"), (-11, "inf"), (-11, "sup"), (-28, "sup"), (-28, "inf"),
                                        (-45, "inf"), (-45, "sup"), (-62, "sup"), (-62, "inf"), (-79, "inf")])

    def test_pecas_comecam_pelo_trecho_de_baixo(self):
        for pc in self.c["pecas"]:
            self.assertEqual(pc["pontos"][0][1], "inf")
            if pc["tipo"] == "extremidade":                          # diante das faces: começa na face
                self.assertIn(pc["pontos"][0][0], (0, 50))
            else:                                                     # ao lado: inteira, da ponta de fora
                self.assertEqual((pc["pontos"][0][0], pc["pontos"][-1][0]), (-79, 129))

    def test_nada_por_cima_do_pilar(self):
        for pc in self.c["pecas"]:
            if 0 < pc["linha"] < 150:
                self.assertTrue(all(u <= 0 or u >= 50 for u, _ in pc["pontos"]), pc["linha"])
        for b in self.c["montagem"]:
            if 0 < b["pos"] < 50:
                self.assertTrue(b["fim"] <= 0 or b["ini"] >= 150)

    def test_linhas_ao_lado_do_pilar_inteiras(self):
        lado = [p for p in self.c["pecas"] if p["tipo"] == "continua"]
        self.assertEqual(sorted(p["linha"] for p in lado), [-62, -45, -28, -11, 161, 178, 195, 212])
        self.assertEqual(lado[0]["pernas"], [-62, -45, -28, -11, 3.5, 18, 32, 46.5, 61, 78, 95, 112])
        frente = [p for p in self.c["pecas"] if p["tipo"] == "extremidade"]
        self.assertEqual(len(frente), 18)                              # 9 linhas diante das faces x 2

    def test_montagem_dentro_da_dobra_de_baixo_de_todas_as_cobrinhas(self):
        """A barra é reta: em cada fileira, todas as cobrinhas que ela cruza têm o trecho de baixo do lado dela."""
        for b in self.c["montagem"]:
            lado = 1 if b["pos"] > b["fileira"] else -1
            for pc in self.c["pecas"]:
                if not (b["ini"] <= pc["linha"] <= b["fim"]) or b["fileira"] not in pc["pernas"]:
                    continue
                vizinho = b["fileira"] + lado * 0.5
                trecho = next(n for a, z, n in pc["trechos"] if min(a, z) <= vizinho <= max(a, z))
                self.assertEqual(trecho, "inf", (b, pc["linha"]))
        self.assertAlmostEqual(self.c["mont_afast"], 1.125)       # (ø10 + ø12,5)/2, encostada na perna

    def test_montagem(self):
        cont = [b for b in self.c["montagem"] if b["tipo"] == "continua"]
        lat = [b for b in self.c["montagem"] if b["tipo"] == "lateral"]
        self.assertEqual({(b["ini"], b["fim"]) for b in cont}, {(-92, 242)})
        self.assertEqual({(b["ini"], b["fim"]) for b in lat}, {(-92, 0), (150, 242)})

    def test_colapso(self):
        em_x, em_y = self.r["colapso"]
        self.assertEqual([round(v, 2) for v in em_x["pos"]], [8.33, 25.0, 41.67])
        self.assertEqual(em_y["pos"], [9.375 + 18.75 * i for i in range(8)])
        self.assertEqual((em_x["ini"], em_x["fim"], em_y["ini"], em_y["fim"]), (-85, 235, -85, 135))

    def test_gabarito(self):
        self.assertEqual(self.c["gabarito"], (-11, -11, 161, 61))


class TesteVariacoes(unittest.TestCase):
    def test_cobrimento_25_encurta_as_cobrinhas_e_avisa(self):
        r = detalhar(dict(P2, c_sup=2.5, c_inf=2.5))
        self.assertEqual([f["comp"] for f in r["ferros"][:2]], [163, 460])      # pernas de 21 pelo eixo
        self.assertAlmostEqual(r["d"], 22.5)
        self.assertEqual(sum(1 for v in r["verificacoes"] if v[0] == "aviso"), 2)   # 17 > 0,75d em x e y

    def test_outra_direcao(self):
        c = detalhar(dict(P2, cob_direcao="maior"))["cobrinha"]
        self.assertEqual((c["direcao"], c["n_linhas"]), ("x", 11))
        for pc in c["pecas"]:
            if pc["tipo"] == "extremidade":
                self.assertIn(pc["pontos"][0][0], (0, 150))

    def test_montagem_padrao_de_30(self):
        p, _ = parametros.normalizar(P2)
        self.assertEqual(p["mont_ext"], 30)

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
