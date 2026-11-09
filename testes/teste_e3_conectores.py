# -*- coding: utf-8 -*-
"""
E3: núcleo dos conectores (pentes Trejor, arranjo radial), sem o TQS. O gabarito é o desenho de referência
PUN_P02 (50 x 150, laje de 27, c = 2,5): 20 pentes "PUN 3P 17 cm" nas posições e ângulos dos blocos do modelo,
contornos a 11, 28 e 45, cotas 35 e 20 entre pentes e 39 (39,1) entre pinos de fora nos cantos, pinos de 220 mm,
quadro do modelo e colapso N1 8 ø10 C=220 e N2 3 ø10 C=320.

Uso:  python -m unittest testes.teste_e3_conectores -v
"""
import math
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import conectores                                          # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402
from nucleo.parametros import normalizar                               # noqa: E402

P02 = dict(titulo="P02", bx=50, by=150, h_laje=27, c_sup=2.5, c_inf=2.5, solucao="conectores",
           col_n_face_bx=3, col_n_face_by=8, con_n_face_bx=3, con_n_face_by=5)

# Inserções do bloco "PUN 3P 17 cm" no PUN_P02 (x, y, ângulo mod 360), lidas do desenho.
_D = 11 / math.sqrt(2)
MODELO = {
    (-11, 5, 180), (-11, 40, 180), (-11, 75, 180), (-11, 110, 180), (-11, 145, 180),
    (61, 5, 0), (61, 40, 0), (61, 75, 0), (61, 110, 0), (61, 145, 0),
    (5, -11, 270), (25, -11, 270), (45, -11, 270),
    (5, 161, 90), (25, 161, 90), (45, 161, 90),
    (-_D, -_D, 225), (50 + _D, -_D, 315), (50 + _D, 150 + _D, 45), (-_D, 150 + _D, 135),
}


def _chave(x, y, a):
    return (round(x, 3), round(y, 3), round(a % 360, 3))


def _con(**extra):
    p, erros = normalizar({**P02, **extra})
    assert not erros, erros
    return p, conectores.detalhar(p)


class TesteModeloP02(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p, cls.c = _con()

    def test_pentes_iguais_aos_do_modelo(self):
        self.assertEqual(self.c["n_pentes"], 20)
        self.assertEqual(self.c["inclinados"], 1)
        obtido = {_chave(pt["x"], pt["y"], pt["ang"]) for pt in self.c["pentes"]}
        self.assertEqual(obtido, {_chave(*m) for m in MODELO})

    def test_pinos_do_pente(self):
        pt = next(pt for pt in self.c["pentes"] if pt["face"] == "direita" and pt["y"] == 40)
        self.assertEqual([tuple(round(v, 6) for v in q) for q in pt["pinos"]], [(61, 40), (78, 40), (95, 40)])
        self.assertEqual(self.c["nome_bloco"], "PUN 3P 17 cm")

    def test_contornos_e_cotas(self):
        self.assertEqual(self.c["contornos"], [11, 28, 45])
        self.assertEqual(self.c["espacamento_faces"], {"baixo": 20, "direita": 35, "cima": 20, "esquerda": 35})
        cantos = [v["dist"] for v in self.c["vizinhos"] if v["canto"]]
        self.assertEqual(len(cantos), 8)                      # as oito cotas "39" do modelo
        for v in cantos:
            self.assertAlmostEqual(v, 39.108, places=3)

    def test_altura_util_e_pino(self):
        self.assertAlmostEqual(self.c["d"], 22.5)             # 27 - 2,5 - 1,0 (cabeça) - 1,0 (negativa)
        self.assertEqual(self.c["pino"]["comprimento_mm"], 220)
        self.assertEqual(self.c["pino"]["cabeca_mm"], 32)
        self.assertAlmostEqual(self.c["trilhos"]["afast"], 2.0)   # 1,6 da cabeça + 0,4 do trilho ø8

    def test_quadro_do_modelo(self):
        self.assertEqual(self.c["quadro"], ["ARMADURA DE COMBATE À PUNÇÃO", "QUANTIDADE: 1 x 20 PENTES",
                                            "DESCRIÇÃO: 3 { 10 mm (CA-50)", "com 220 mm + 2 { 8 mm (CA-50)"])

    def test_ferros_so_colapso(self):
        r = detalhar(P02)
        self.assertEqual(r["erros"], [])
        self.assertEqual([(f["pos"], f["quant"], f["bitola"], f["comp"]) for f in r["ferros"]],
                         [(1, 8, 10.0, 220), (2, 3, 10.0, 320)])

    def test_verificacoes(self):
        r = detalhar(P02)
        avisos = [t for tipo, t, _ in r["verificacoes"] if tipo == "aviso"]
        self.assertEqual(len(avisos), 2)
        self.assertIn("sr = 17", avisos[0])                   # passa de 0,75d = 16,875 por 1 mm
        self.assertIn("C'' a 90 cm da face", avisos[1])       # colapso: 45 + 2d, e as barras saem 85 da face


class TesteVariantes(unittest.TestCase):
    def test_cruz(self):
        p, c = _con(con_inclinados="cruz")
        self.assertEqual((c["inclinados"], c["n_pentes"]), (0, 16))
        self.assertAlmostEqual(c["esp_canto_max"], math.hypot(50, 50), places=6)
        avisos = [t for tipo, t, _ in detalhar({**P02, "con_inclinados": "cruz"})["verificacoes"] if tipo == "aviso"]
        self.assertTrue(any("cruz" in t for t in avisos))

    def test_numero_fixo_em_leque(self):
        p, c = _con(con_inclinados=3)
        incl = sorted(round(pt["ang"], 6) for pt in c["pentes"] if pt["face"] == "canto inferior esquerdo")
        self.assertEqual(incl, [202.5, 225.0, 247.5])
        self.assertEqual(c["n_pentes"], 16 + 12)

    def test_auto_aumenta_com_mais_pinos(self):
        p, c = _con(con_pinos=5)                              # pinos de fora a 79: o leque precisa de 3
        self.assertEqual(c["inclinados"], 3)
        self.assertLessEqual(c["esp_canto_max"], 2 * c["d"])
        p, c2 = _con(con_pinos=5, con_inclinados=2)
        self.assertGreater(c2["esp_canto_max"], 2 * c2["d"])  # com 2, não chega: o auto achou o menor

    def test_vizinhos_em_ordem(self):
        p, c = _con()
        pentes = c["pentes"]
        for v in c["vizinhos"]:                               # vizinhos da lista = vizinhos em volta do pilar
            a, b = pentes[v["i"]]["pinos"][0], pentes[v["j"]]["pinos"][0]
            self.assertLess(math.dist(a, b), 40)

    def test_um_pente_na_face_fica_no_meio(self):
        p, c = _con(con_n_face_bx=1)
        baixo = [pt for pt in c["pentes"] if pt["face"] == "baixo"]
        self.assertEqual([(pt["x"], pt["y"]) for pt in baixo], [(25, -11)])
        self.assertIsNone(c["espacamento_faces"]["baixo"])

    def test_espacos_das_faces_em_cm_inteiros(self):
        pf = conectores.posicoes_face
        self.assertEqual(pf(150, 5, 5), [5, 40, 75, 110, 145])           # o modelo: exato
        self.assertEqual(pf(80, 4, 5), [5, 28, 52, 75])                  # 23 / 24 / 23, sobra no meio
        self.assertEqual(pf(60, 4, 5), [5, 21, 39, 55])                  # 16 / 18 / 16
        self.assertEqual(pf(55, 3, 5), [5, 27.5, 50])                    # sobra ímpar: meio cm nos dois do meio
        self.assertEqual(pf(40, 1, 5), [20])

    def test_face_longa_avisa(self):
        r = detalhar({**P02, "con_n_face_by": 2})
        avisos = [t for tipo, t, _ in r["verificacoes"] if tipo == "aviso"]
        self.assertTrue(any("ao longo das faces a 140" in t for t in avisos))

    def test_pino_arredondado_e_minimo(self):
        p, c = _con(h_laje=26.7)                              # 217 mm livres -> 215
        self.assertEqual((c["pino"]["livre_mm"], c["pino"]["comprimento_mm"]), (217.0, 215.0))
        r = detalhar({**P02, "h_laje": 15.5})                 # 105 mm < 110
        self.assertTrue(any("abaixo do mínimo" in t for tipo, t, _ in r["verificacoes"] if tipo == "aviso"))

    def test_bitola_fora_do_catalogo(self):
        r = detalhar({**P02, "con_bitola": 14})
        self.assertTrue(any("fora do catálogo" in t for tipo, t, _ in r["verificacoes"] if tipo == "aviso"))
        self.assertEqual(r["conectores"]["pino"]["cabeca_mm"], 45)

    def test_montagem_opcional(self):
        self.assertEqual(len(detalhar(P02)["ferros"]), 2)     # desligada por padrão (P7, Q7)
        r = detalhar({**P02, "con_montagem": True})
        # uma por linha de pinos em cada face: faces de 150 com 140 + 2 x 30 = 200, de 50 com 40 + 60 = 100
        self.assertEqual([(f["pos"], f["quant"], f["bitola"], f["comp"]) for f in r["ferros"]],
                         [(1, 8, 10.0, 220), (2, 3, 10.0, 320), (3, 6, 12.5, 200), (4, 6, 12.5, 100)])
        esq = [b for b in r["conectores"]["montagem"] if b["face"] == "esquerda"]
        self.assertEqual(sorted(b["p1"][0] for b in esq), [-45, -28, -11])
        self.assertEqual({(b["p1"][1], b["p2"][1]) for b in esq}, {(175, -25)})

    def test_erros(self):
        for extra, trecho in (({"con_sr": 0}, "con_sr"), ({"con_pinos": 0}, "con_pinos"),
                              ({"con_dist_canto": 30}, "distância ao canto"),
                              ({"con_inclinados": "x"}, "con_inclinados")):
            r = detalhar({**P02, **extra})
            self.assertTrue(any(trecho in e for e in r["erros"]), (extra, r["erros"]))


if __name__ == "__main__":
    unittest.main()
