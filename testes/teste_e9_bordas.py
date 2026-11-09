# -*- coding: utf-8 -*-
"""
E9: pilares de borda e de canto (cobrinha e conectores). Sem o TQS, confere os parâmetros, a geometria das peças e
dos pentes junto da borda livre, o colapso (pontas, faces e gancho), as verificações e as folhas; com o TQS, grava
pilares de borda e de canto numa pasta temporária e confere os comprimentos que o TQS calcula (inclusive o gancho de
90°).

Uso:  python -m unittest testes.teste_e9_bordas -v
"""
import math
import os
import shutil
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import cobrinha, colapso, conectores, prancha_cobrinha    # noqa: E402
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
        self.assertEqual(normalizar(dict(BE0, solucao="conectores"))[1], [])        # E9: conectores de borda


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
        c = detalhar(dict(BD20, cob_face_recuada=True, cob_construtivas=True))["cobrinha"]
        borda = [pc for pc in c["pecas"] if pc["tipo"] == "extremidade_borda"]
        self.assertTrue(borda)
        self.assertEqual((borda[0]["pernas"], borda[0]["fim"]), ([61.0], 67.5))   # perna a s0, ponta no cobrimento
        self.assertEqual(c["contorno"]["u+"], 11.0)                       # a borda deixa a perna de s0

    def test_borda_ao_longo_das_linhas(self):
        c = detalhar(dict(BC15, cob_face_recuada=True, cob_construtivas=True))["cobrinha"]
        self.assertEqual(c["linhas"][-1], 161.0)                          # Lt + s0 <= Lt + 15 - 2,5
        self.assertEqual(c["t_mont"][1], 163.0)                           # montagem até o cobrimento
        self.assertIsNone(c["alcance"]["t+"])

    def test_toda_perna_tem_trechos_dos_dois_lados(self):
        for par in (BE0, BD20, BC15, CEB0):
            for pc in detalhar(par)["cobrinha"]["pecas"]:
                self.assertEqual(len(pc["trechos"]), len(pc["pernas"]) + 1, (par["titulo"], pc["tipo"]))


class TesteOpcoesCobrinha(unittest.TestCase):
    """Borda recuada, por região (pedido do usuário em 09/11/2026): sem opção, nada passa da linha da face voltada
    para a borda; pinos na face recuada = diante dela; linhas construtivas = além dos cantos."""

    def _c(self, par, **op):
        r = detalhar(dict(par, **op))
        self.assertEqual(r["erros"], [])
        return r["cobrinha"]

    def test_padrao_nada_alem_da_face(self):
        c = self._c(BD20)                                                  # borda em u+, a 20 cm
        self.assertLessEqual(max(u for pc in c["pecas"] for u, _ in pc["pontos"]), 50.0)
        self.assertNotIn("extremidade_borda", {pc["tipo"] for pc in c["pecas"]})
        c = self._c(BC15)                                                  # borda em t+, a 15 cm
        self.assertLess(max(c["linhas"]), 150.0)

    def test_so_a_face_recuada(self):
        c = self._c(BD20, cob_face_recuada=True)
        self.assertIn("extremidade_borda", {pc["tipo"] for pc in c["pecas"]})
        inteiras = [pc for pc in c["pecas"] if pc["tipo"].startswith("continua")]
        self.assertLessEqual(max(u for pc in inteiras for u, _ in pc["pontos"]), 50.0)
        c = self._c(BC15, cob_face_recuada=True)
        alem = [pc for pc in c["pecas"] if pc["linha"] > 150]
        self.assertTrue(alem)
        self.assertEqual({pc["tipo"] for pc in alem}, {"recuada"})
        self.assertEqual((alem[0]["pernas"][0], alem[0]["pernas"][-1]), (5.0, 45.0))   # como os pentes a 5 do canto

    def test_so_as_construtivas(self):
        c = self._c(BD20, cob_construtivas=True)
        self.assertNotIn("extremidade_borda", {pc["tipo"] for pc in c["pecas"]})
        inteiras = [pc for pc in c["pecas"] if pc["tipo"].startswith("continua")]
        self.assertEqual(max(u for pc in inteiras for u, _ in pc["pontos"]), 67.5)    # até o cobrimento da borda
        c = self._c(BC15, cob_construtivas=True)
        alem = [pc for pc in c["pecas"] if pc["linha"] > 150]
        self.assertEqual({pc["tipo"] for pc in alem}, {"extremidade"})               # das faces para fora
        self.assertEqual({pc["ini"] for pc in alem}, {0.0, 50.0})

    def test_montagem_so_onde_ha_pernas(self):
        c = self._c(BC15, cob_construtivas=True)
        for b in c["montagem"]:
            if b["tipo"] == "lateral" and b["ini"] >= 150:                 # do lado da borda, sem pernas no meio
                self.fail(b)

    def test_texto_da_verificacao(self):
        txt = " ".join(t for _, t, _ in detalhar(BD20)["verificacoes"])
        self.assertIn("só até a linha da face voltada para a borda", txt)
        txt = " ".join(t for _, t, _ in detalhar(dict(BD20, cob_construtivas=True))["verificacoes"])
        self.assertIn("além dos cantos (linhas construtivas)", txt)

    def test_prancha_com_as_pecas_entre_as_faces(self):
        f = prancha_cobrinha.montar(detalhar(dict(BC15, cob_face_recuada=True)))
        fe = next(x for x in detalhar(dict(BC15, cob_face_recuada=True))["ferros"] if x.get("subtipo") == "recuada")
        self.assertIn(f"COBRINHA N{fe['pos']} 10", f.blocos)
        usados = {q["n"] for q in f.prims if "n" in q}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)


class TesteColapso(unittest.TestCase):
    def test_faces_que_contam(self):
        # borda = 3 faces, canto = 2, com o pilar faceando ou recuado (regra do usuário em 09/11/2026)
        casos = ((BE0, (1, 2)), (BD20, (1, 2)), (BC15, (2, 1)), (CEB0, (1, 1)),
                 (dict(BASE, borda_x="direita", dist_borda_x=30, borda_y="cima", dist_borda_y=12), (1, 1)))
        for par, esperado in casos:
            self.assertEqual(tuple(b["faces"] for b in detalhar(par)["colapso"]), esperado, par)

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


CON = dict(bx=50, by=150, h_laje=27, c_sup=2.0, c_inf=2.0, solucao="conectores")
C_BE0 = dict(CON, titulo="CBE0", borda_x="esquerda")
C_BE20 = dict(CON, titulo="CBE20", borda_x="esquerda", dist_borda_x=20, con_face_recuada=True)
C_CANTO = dict(CON, titulo="CCDC40", borda_x="direita", dist_borda_x=40, borda_y="cima", dist_borda_y=10,
               con_face_recuada=True,
               con_construtivas=True, con_montagem=True)
C_BD0 = dict(CON, titulo="CBD0", bx=150, by=50, borda_x="direita", con_n_face_bx=5, con_n_face_by=3)


class TesteConectores(unittest.TestCase):
    def _c(self, par):
        r = detalhar(par)
        self.assertEqual(r["erros"], [])
        return r["conectores"]

    def test_face_recuada_desligada(self):
        par = dict(C_BE20, con_face_recuada=False)
        r = detalhar(par)
        self.assertNotIn("esquerda", {pt["face"] for pt in r["conectores"]["pentes"]})
        self.assertTrue(any("pinos na face recuada\" está desligada" in t for _, t, _ in r["verificacoes"]))

    def test_borda_faceando(self):
        c = self._c(C_BE0)
        faces = {pt["face"] for pt in c["pentes"]}
        self.assertNotIn("esquerda", faces)
        cantos = [pt for pt in c["pentes"] if pt["tipo"] == "canto"]
        self.assertEqual(sorted(pt["face"] for pt in cantos), ["canto inferior direito", "canto superior direito"])
        self.assertEqual(c["n_pentes"], 13)
        self.assertEqual([(t["n_pinos"], t["quant"]) for t in c["tipos"]], [(3, 13)])
        self.assertTrue(any(v["borda"] for v in c["vizinhos"]))           # o par que atravessa a borda

    def test_trilho_no_cobrimento_da_borda(self):
        lat, _ = conectores.extensoes(normalizar(C_BE0)[0])
        for par, a in ((C_BE0, 0.0), (C_BE20, 20.0)):
            for pt in self._c(par)["pentes"]:
                if pt["face"] in ("baixo", "cima"):
                    self.assertGreaterEqual(pt["x"] - lat, -a + 2.0 - 1e-6, (par["titulo"], pt))

    def test_pentes_curtos_na_face_recuada(self):
        c = self._c(C_BE20)
        self.assertEqual([(t["n_pinos"], t["quant"]) for t in c["tipos"]], [(3, 13), (1, 5)])
        self.assertEqual(c["texto_pentes"], "13 pentes PUN 3P 17 cm + 5 pentes PUN 1P 17 cm")
        self.assertEqual(len(c["quadro"]), 7)
        _, ponta = conectores.extensoes(normalizar(C_BE20)[0])
        for pt in c["pentes"]:
            if pt["face"] == "esquerda":
                self.assertGreaterEqual(min(x for x, _ in pt["pinos"]) - ponta, -20 + 2.0 - 1e-6)

    def test_linhas_construtivas(self):
        c = self._c(dict(C_BE20, con_construtivas=True))
        cons = [pt for pt in c["pentes"] if pt["tipo"] == "construtiva"]
        self.assertEqual(sorted((pt["face"], pt["x"]) for pt in cons), [("baixo", -15.5), ("cima", -15.5)])
        self.assertEqual(self._c(dict(C_BE0, con_construtivas=True))["n_pentes"], 13)   # faceando: nada a mais

    def test_canto_recuado(self):
        r = detalhar(C_CANTO)
        c = r["conectores"]
        self.assertNotIn("cima", {pt["face"] for pt in c["pentes"]})        # a 10 cm não cabe pino
        self.assertEqual({pt["n_pinos"] for pt in c["pentes"] if pt["face"] == "direita"}, {2})
        self.assertEqual([pt["face"] for pt in c["pentes"] if pt["tipo"] == "canto"], ["canto inferior esquerdo"])
        for b in c["montagem"]:                                             # montagem até o cobrimento das bordas
            self.assertLessEqual(max(b["p1"][0], b["p2"][0]), 50 + 40 - 2 + 1e-6)
            self.assertLessEqual(max(b["p1"][1], b["p2"][1]), 150 + 10 - 2 + 1e-6)
        txt = " ".join(t for _, t, _ in r["verificacoes"])
        self.assertIn("pilar de canto", txt)
        self.assertIn("face cima: a borda a 10 cm não deixa espaço", txt)
        self.assertIn("face direita: pentes de 2 pinos", txt)

    def test_relatorio_por_tipo(self):
        from nucleo import relatorio
        rel = relatorio.montar([dict(res=detalhar(C_BE20), tqs=None)])
        self.assertEqual(sorted((g["bloco"], g["pentes"], g["pinos"]) for g in rel["conectores"]),
                         [("PUN 1P 17 cm", 5, 5), ("PUN 3P 17 cm", 13, 39)])


class TesteFolhaConectores(unittest.TestCase):
    def test_bordas_desenhadas(self):
        from nucleo import prancha_conectores
        f = prancha_conectores.montar(detalhar(dict(C_CANTO, col_gancho_borda=True)))
        self.assertEqual(sum(1 for p in f.prims if p["t"] == "Texto" and p["txt"] == "BORDA LIVRE"), 4)
        self.assertIn("PUN 2P 17 cm", f.blocos)
        usados = {p["n"] for p in f.prims if "n" in p} | {p["n"] for b in f.blocos.values() if b for p in b}
        self.assertTrue(usados <= NIVEIS_MODELOS, usados - NIVEIS_MODELOS)
        self.assertTrue(any(p["t"] == "Ferro" and "ganchos" in p for p in f.prims))

    def test_linha_da_borda_visivel(self):
        # no 240 (hachura de 25 %), a linha não sai na plotagem: a borda vai no 0, nas duas soluções
        from nucleo import prancha_conectores
        for mod, par in ((prancha_conectores, C_BE20), (prancha_cobrinha, BD20)):
            f = mod.montar(detalhar(par))
            x = -20.0 if par is C_BE20 else 70.0
            linhas = [p for p in f.prims if p["t"] == "Linha" and abs(p["xy"][0][0] - x) < 1e-6
                      and abs(p["xy"][1][0] - x) < 1e-6 and abs(p["xy"][1][1] - p["xy"][0][1]) > 100]
            self.assertTrue(linhas, mod.__name__)
            self.assertEqual({p["n"] for p in linhas}, {0})

    def test_nota_1_do_lado_dos_pentes(self):
        from nucleo import prancha_conectores
        f = prancha_conectores.montar(detalhar(C_BD0))                       # borda direita faceando
        nota = next(p for p in f.prims if p["t"] == "Texto" and p["txt"] == "NOTA 1")
        self.assertLess(nota["x"], 0)
        topo = next(p for p in f.prims if p["t"] == "Texto" and p["txt"] == "TOPO LAJE")
        self.assertGreater(topo["x"], 150)                                  # fora da laje, além da borda

    def test_quadro_nao_desce_sobre_o_titulo(self):
        from nucleo import prancha_conectores
        f = prancha_conectores.montar(detalhar(C_BE20))
        linhas = [p for p in f.prims if p["t"] == "Texto" and p["txt"].startswith(("QUANTIDADE", "DESCRIÇÃO", "com "))]
        self.assertEqual(len(linhas), 6)                                    # dois tipos de pente
        tit = next(p for p in f.prims if p["t"] == "Texto" and p["txt"] == "VISTA EM PLANTA (COLAPSO PROGRESSIVO)")
        self.assertGreater(min(p["y"] for p in linhas), tit["y"] + tit["h"])


BE20 = dict(BASE, titulo="BE20", cob_direcao="y", borda_x="esquerda", dist_borda_x=20, cob_face_recuada=True,
            cob_construtivas=True)                      # a 2ª imagem do usuário (09/11/2026)


class TesteConferenciaDoUsuario(unittest.TestCase):
    """Pedidos de 09/11/2026: pente mestre fora da borda curta, gabarito como pilar de borda ou de canto, NOTA 2 fora
    das cotas, nota da montagem na borda curta e nenhuma sobreposição de textos."""

    def test_pente_mestre_no_lado_livre(self):
        f = prancha_cobrinha.montar(detalhar(BE20))
        tit = next(p for p in f.prims if p["t"] == "Texto" and p["txt"] == "PENTE MESTRE")
        chamada = min((p for p in f.prims if p["t"] == "Polyline" and p["n"] == 253 and len(p["xy"]) == 4),
                      key=lambda p: math.dist(p["xy"][0], (tit["x"], tit["y"])))
        self.assertAlmostEqual(chamada["xy"][-1][0], 50 + 11)              # a linha a s0 da face livre (direita)

    def test_gabarito_despreza_a_borda_curta(self):
        f = prancha_cobrinha.montar(detalhar(BE20))
        no_gabarito = {round(abs((p["p2"][0] - p["p1"][0]) or (p["p2"][1] - p["p1"][1])) * p["fator"], 1)
                       for p in f.prims if p["t"] == "Cota" and p["fator"] != 1.0}
        self.assertEqual(no_gabarito, {11.0, 50.0, 150.0})                 # sem a faixa de 20 da borda

    def test_nota_da_borda_curta(self):
        notas = lambda par: " ".join(p["txt"] for p in prancha_cobrinha.montar(detalhar(par)).prims       # noqa
                                     if p["t"] == "Texto" and p["n"] == 227)
        self.assertIn("NA BORDA CURTA", notas(BE20))                         # montagem omitida (18 cm)
        self.assertNotIn("NA BORDA CURTA", notas(BASE))
        self.assertNotIn("NA BORDA CURTA", notas(dict(BE20, cob_face_recuada=False, cob_construtivas=False)))

    def test_sem_sobreposicoes(self):
        import glob
        from ferramentas import sobreposicoes
        from nucleo.parametros import ler_projeto
        pilares = [par for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "*.json")))
                   for par in ler_projeto(arq)["pilares"]]
        pilares += [BE20, dict(BE20, cob_face_recuada=False), dict(BE20, cob_construtivas=False),
                    dict(BC15, cob_face_recuada=True), dict(BC15, cob_construtivas=True), BD20, CEB0,
                    dict(BASE, titulo="YC", bx=150, by=50, borda_x="direita", dist_borda_x=10, borda_y="cima",
                         cob_construtivas=True),
                    C_BE0, C_BE20, dict(C_BE20, con_construtivas=True), C_CANTO, C_BD0]
        for par in pilares:
            with self.subTest(par["titulo"]):
                self.assertEqual(sobreposicoes.verificar(sobreposicoes.folha_do_pilar(par)), [])


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

    def test_conectores_pelo_tqs(self):
        from dwg_tqs import prancha
        pasta = tempfile.mkdtemp(prefix="pun_e9c_")
        try:
            for par in (dict(C_BE20, con_construtivas=True, col_gancho_borda=True), C_CANTO):
                g = prancha.gerar(detalhar(par), pasta, pdf=False, dxf=False)
                self.assertTrue(g["confere"], (par["titulo"], g["tabela_tqs"], g["esperado"]))
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
