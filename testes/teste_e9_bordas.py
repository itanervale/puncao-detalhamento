# -*- coding: utf-8 -*-
"""
E9: pilares de borda e de canto (cobrinha). Sem o TQS, confere os parâmetros, a geometria das peças junto da borda
livre, o colapso (pontas, faces e gancho), as verificações e a folha; com o TQS, grava dois pilares de canto numa
pasta temporária e confere os comprimentos que o TQS calcula (inclusive o gancho de 90°).

Uso:  python -m unittest testes.teste_e9_bordas -v
"""
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import cobrinha, colapso, prancha_cobrinha                # noqa: E402
from nucleo.detalhe import detalhar                                    # noqa: E402
from nucleo.parametros import normalizar, posicao                      # noqa: E402

try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False

BASE = dict(bx=50, by=150, h_laje=27, c_sup=2.0, c_inf=2.0, cob_direcao="x")   # cobrinhas em x (o lado menor)
BE0 = dict(BASE, titulo="BE0", borda_x="esquerda")                       # borda faceando a face u = 0
BD20 = dict(BASE, titulo="BD20", borda_x="direita", dist_borda_x=20)    # borda a 20 cm da face u = L
BC15 = dict(BASE, titulo="BC15", borda_y="cima", dist_borda_y=15)       # borda ao longo das linhas
CEB0 = dict(BASE, titulo="CEB0", borda_x="esquerda", borda_y="baixo")   # canto
NIVEIS_MODELOS = {0, 1, 79, 200, 202, 203, 204, 205, 210, 220, 221, 222, 224, 225, 226, 227, 233, 240, 241, 242,
                  243, 244, 245, 246, 253, 254}


class TesteParametros(unittest.TestCase):
    def test_posicao_e_normalizacao(self):
        p, erros = normalizar(dict(BASE, borda_x="Esquerda", borda_y="nenhuma"))
        self.assertEqual(erros, [])
        self.assertEqual((p["borda_x"], p["borda_y"], posicao(p)), ("esquerda", "", "borda"))
        self.assertEqual(posicao(normalizar(CEB0)[0]), "canto")
        self.assertEqual(posicao(normalizar(BASE)[0]), "interno")

    def test_erros(self):
        self.assertTrue(normalizar(dict(BASE, borda_x="frente"))[1])
        self.assertTrue(normalizar(dict(BASE, borda_x="direita", dist_borda_x=-1))[1])
        erros = normalizar(dict(BE0, solucao="conectores"))[1]
        self.assertTrue(any("ainda não implementado" in e for e in erros))


class TesteCobrinha(unittest.TestCase):
    def test_borda_faceando(self):
        c = detalhar(BE0)["cobrinha"]
        tipos = {pc["tipo"] for pc in c["pecas"]}
        self.assertEqual(tipos, {"continua_borda", "extremidade"})       # nada diante da face da borda
        cont = next(pc for pc in c["pecas"] if pc["tipo"] == "continua_borda")
        self.assertEqual(cont["fim"], 2.5)                                # cobrimento 2 + ø/2
        self.assertEqual(cont["pernas"][-1], 2.5 + cobrinha.PONTA_BORDA)  # a perna junto da borda e a ponta
        self.assertEqual(c["alcance"]["u-"], None)
        self.assertEqual(c["contorno"]["u-"], -7.5)
        self.assertTrue(all(pc["ini"] == 50.0 for pc in c["pecas"] if pc["tipo"] == "extremidade"))

    def test_borda_recuada(self):
        c = detalhar(BD20)["cobrinha"]
        borda = [pc for pc in c["pecas"] if pc["tipo"] == "extremidade_borda"]
        self.assertTrue(borda)
        self.assertEqual((borda[0]["pernas"], borda[0]["fim"]), ([61.0], 67.5))   # perna a s0, ponta no cobrimento
        self.assertEqual(c["contorno"]["u+"], 11.0)                       # a borda deixa a perna de s0

    def test_borda_ao_longo_das_linhas(self):
        c = detalhar(BC15)["cobrinha"]
        self.assertEqual(c["linhas"][-1], 161.0)                          # Lt + s0 <= Lt + 15 - 2,5
        self.assertEqual(c["t_mont"][1], 163.0)                           # montagem até o cobrimento
        self.assertIsNone(c["alcance"]["t+"])

    def test_toda_perna_tem_trechos_dos_dois_lados(self):
        for par in (BE0, BD20, BC15, CEB0):
            for pc in detalhar(par)["cobrinha"]["pecas"]:
                self.assertEqual(len(pc["trechos"]), len(pc["pernas"]) + 1, (par["titulo"], pc["tipo"]))


class TesteColapso(unittest.TestCase):
    def test_gancho_como_o_tqs(self):
        # medido no TQS em 09/11/2026 (ICP090 numa ponta, reto de 100)
        self.assertEqual([colapso.gancho_90(f) for f in (8, 10, 12.5, 16, 20)], [8, 10, 12, 16, 21])
        self.assertEqual(colapso.altura_gancho(10), 11.5)

    def test_pontas_e_faces(self):
        x, y = detalhar(BE0)["colapso"]
        self.assertEqual((x["ini"], x["fim"], x["faces"], x["comp"]), (2.0, 135.0, 1, 133))
        self.assertEqual((y["ini"], y["faces"]), (-85.0, 2))
        g = detalhar(dict(BE0, col_gancho_borda=True))["colapso"][0]
        self.assertEqual((g["ganchos"], g["reto"], g["comp"]), ((True, False), 133, 143))

    def test_capacidade_conta_as_faces(self):
        p = normalizar(dict(BE0, tqs=dict(esforcos=[dict(n=1, titulo="ELU", fz=30.0, mx=0, my=0)])))[0]
        cap = colapso.capacidade(p)
        self.assertAlmostEqual(cap["as_ef"], (8 * 1 + 3 * 2) * colapso.area(10))

    def test_ultima_linha_so_dos_lados_livres(self):
        self.assertEqual(colapso.ultima_linha(detalhar(BE0)), {"x": 62.0, "y": 62.0})

    def test_gancho_que_nao_cabe(self):
        r = detalhar(dict(BE0, h_laje=14, col_gancho_borda=True))
        self.assertTrue(any(t == "aviso" and "gancho" in txt for t, txt, _ in r["verificacoes"]))


class TesteVerificacoes(unittest.TestCase):
    def test_linha_da_borda(self):
        v = detalhar(CEB0)["verificacoes"]
        self.assertTrue(any(t == "ok" and txt.startswith("pilar de canto") for t, txt, _ in v))

    def test_borda_a_2d_ou_mais(self):
        v = detalhar(dict(BASE, borda_x="direita", dist_borda_x=50))["verificacoes"]
        self.assertTrue(any(t == "aviso" and "tratado como interno" in txt for t, txt, _ in v))


class TesteFolha(unittest.TestCase):
    def _folha(self, par):
        return prancha_cobrinha.montar(detalhar(par))

    def test_bordas_desenhadas(self):
        f = self._folha(CEB0)
        rotulos = [p for p in f.prims if p["t"] == "Texto" and p["txt"] == "BORDA LIVRE"]
        self.assertEqual(len(rotulos), 4)                                 # duas na planta e duas no colapso
        usados = {p["n"] for p in f.prims if "n" in p}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)

    def test_cota_da_face_a_borda(self):
        f = self._folha(BD20)
        cotas = [p for p in f.prims if p["t"] == "Cota" and p["modo"] == "h"]
        self.assertTrue(any(abs(abs(p["p2"][0] - p["p1"][0]) - 20) < 1e-6 for p in cotas))

    def test_gabarito_aberto_na_borda_faceando(self):
        f = self._folha(CEB0)
        linhas_pm = [p for p in f.prims if p["t"] == "Polyline" and p["n"] == 233 and len(p["xy"]) == 3]
        self.assertEqual(len(linhas_pm), 1)                               # só os lados livres: um "L"

    def test_ganchos_so_quando_ha(self):
        com = [p for p in self._folha(dict(CEB0, col_gancho_borda=True)).prims if p["t"] == "Ferro" and "ganchos" in p]
        self.assertEqual(len(com), 2)
        self.assertTrue(all(p["reto"] < p["comp"] for p in com))
        sem = [p for p in self._folha(CEB0).prims if p["t"] == "Ferro" and "ganchos" in p]
        self.assertEqual(sem, [])

    def test_cobrinhas_em_y(self):
        f = self._folha(dict(titulo="Y", bx=150, by=50, h_laje=27, c_sup=2.0, c_inf=2.0, borda_x="direita",
                             dist_borda_x=10, borda_y="cima", cob_direcao="y"))
        self.assertIn("COBRINHA N2 10", f.blocos)
        self.assertEqual(len([p for p in f.prims if p["t"] == "Texto" and p["txt"] == "BORDA LIVRE"]), 4)


@unittest.skipUnless(TEM_TQS, "sem o TQS")
class TesteDWG(unittest.TestCase):
    def test_cantos_pelo_tqs(self):
        from dwg_tqs import prancha
        pasta = tempfile.mkdtemp(prefix="pun_e9_")
        try:
            for par in (dict(CEB0, col_gancho_borda=True),
                        dict(titulo="YCDC10G", bx=150, by=50, h_laje=27, c_sup=2.0, c_inf=2.0, borda_x="direita",
                             dist_borda_x=10, borda_y="cima", col_gancho_borda=True, cob_direcao="y")):
                g = prancha.gerar(detalhar(par), pasta, pdf=False, dxf=False)
                self.assertTrue(g["confere"], (par["titulo"], g["tabela_tqs"], g["esperado"]))
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
