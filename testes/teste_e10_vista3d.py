# -*- coding: utf-8 -*-
"""
Visualização 3D (pedido do usuário em 10/11/2026: "as mesmas propriedades do app de Vigas Protendidas"): a geometria
de nucleo/vista3d.py confere com o núcleo e com os cortes da prancha, a página leva o three.js embutido, a linha de
comando grava sem o TQS e a janela grava a página do pilar e a do lote. Nada aqui usa o TQS nem abre o navegador
(a conferência no navegador fica fora dos testes: a página exige WebGL).

Uso:  python -m unittest testes.teste_e10_vista3d -v
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo import vista3d                                              # noqa: E402
from nucleo.detalhe import detalhar                                     # noqa: E402
from nucleo.parametros import ler_projeto                               # noqa: E402

try:
    import tkinter as tk
    _r = tk.Tk()
    _r.destroy()
    TEM_TELA = True
except Exception:
    TEM_TELA = False


def _pilares():
    for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "*.json"))):
        for par in ler_projeto(arq)["pilares"]:
            yield os.path.basename(arq), par


def _dados(arq, titulo):
    par = next(q for q in ler_projeto(os.path.join(RAIZ, "exemplos", arq))["pilares"] if q["titulo"] == titulo)
    res = detalhar(par)
    return res, vista3d.dados_3d(res, "teste")


def _tipo(d, k):
    return [e for e in d["elems"] if e["k"] == k]


class TesteGeometria(unittest.TestCase):
    def test_todos_os_exemplos(self):
        """Cada ferro vira uma posição da legenda, e tudo fica dentro da laje (planta) e da espessura (z)."""
        for arq, par in _pilares():
            with self.subTest(arq=arq, pilar=par["titulo"]):
                res = detalhar(par)
                d = vista3d.dados_3d(res)
                ids = [g["id"] for g in d["grupos"]]
                self.assertEqual([i for i in ids if i.startswith("N")], [f"N{f['pos']}" for f in res["ferros"]])
                x0, x1, y0, y1 = d["laje"]
                for e in d["elems"]:
                    self.assertGreater(e["r"], 0)
                    self.assertGreaterEqual(len(e["p"]), 2)
                    self.assertTrue(0 <= e["g"] < len(d["grupos"]))
                    for x, y, z in e["p"]:
                        self.assertTrue(x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6, (e["t"], x, y))
                        self.assertTrue(e["r"] - 1e-6 <= z <= d["h"] - e["r"] + 1e-6, (e["t"], z))

    def test_cobrinha_de_cobrimento_a_cobrimento(self):
        res, d = _dados("P2_cobrinha.json", "P2")
        p, c = res["p"], res["cobrinha"]
        cob = [e for e in d["elems"] if d["grupos"][e["g"]]["tipo"] == "cobrinha"]
        self.assertEqual(len(cob), c["n_pecas"])
        fc = p["cob_bitola"] / 10
        zs = {round(q[2], 2) for e in cob for q in e["p"]}
        self.assertEqual(zs, {round(p["c_inf"] + fc / 2, 2), round(p["h_laje"] - p["c_sup"] - fc / 2, 2)})
        # cobrinhas em y: cada peça fica no plano x = linha, que o duplo clique usa para a seção
        for e in cob:
            self.assertEqual(e["pl"][0], "x")
            self.assertEqual({q[0] for q in e["p"]}, {e["pl"][1]})
        mont = [e for e in d["elems"] if d["grupos"][e["g"]]["tipo"] == "montagem"]
        self.assertEqual(len(mont), len(c["montagem"]))
        col = [e for e in d["elems"] if d["grupos"][e["g"]]["tipo"] == "colapso"]
        self.assertEqual(len(col), sum(g["quant"] for g in res["colapso"]))

    def test_cortes_do_desenho(self):
        """Os planos A-A e B-B são os da prancha: na linha diante da face e na linha ao lado do pilar."""
        from nucleo.prancha_cobrinha import Prancha
        res, d = _dados("P2_cobrinha.json", "P2")
        pr = Prancha(res)
        self.assertEqual([(c["letra"], c["eixo"], c["v"]) for c in d["cortes"]],
                         [("A", "x", pr.t_frente), ("B", "x", pr.t_lado)])
        _res, d = _dados("P2x_cobrinha.json", "P2")
        self.assertEqual({c["eixo"] for c in d["cortes"]}, {"y"})
        from nucleo.prancha_conectores import Prancha as PC
        res, d = _dados("P02_conectores.json", "P02")
        self.assertEqual(d["cortes"], [dict(letra="A", eixo="y", v=PC(res).y_corte)])

    def test_pentes(self):
        res, d = _dados("P02_conectores.json", "P02")
        p, c = res["p"], res["conectores"]
        n_pinos = sum(pt["n_pinos"] for pt in c["pentes"])
        self.assertEqual(len(_tipo(d, "pino")), n_pinos)
        self.assertEqual(len(_tipo(d, "cabeca")), 2 * n_pinos)
        self.assertEqual(len(_tipo(d, "trilho")), 2 * c["n_pentes"])
        L = c["pino"]["comprimento_mm"] / 10
        for e in _tipo(d, "pino"):
            self.assertEqual([q[2] for q in e["p"]], [p["c_inf"], p["c_inf"] + L])
            self.assertLessEqual(e["p"][1][2], p["h_laje"] - p["c_sup"] + 1e-6)
        self.assertEqual({e["r"] for e in _tipo(d, "cabeca")}, {c["pino"]["cabeca_mm"] / 20})
        self.assertEqual(d["grupos"][0]["id"], "PUN 3P 17 cm")
        self.assertEqual(len(d["contornos"]), len(c["contornos"]))       # sem borda: um contorno inteiro por linha

    def test_borda_livre(self):
        """A laje termina na borda (faceando o pilar, x = 0) e os pentes curtos da face recuada formam outra posição."""
        res, d = _dados("lote_bordas_conectores.json", "P31")
        self.assertEqual(d["laje"][0], 0.0)
        self.assertEqual(d["bordas"], [dict(lado="esquerda", a=0.0)])
        self.assertEqual(d["posicao"], "borda")
        _res, d = _dados("lote_bordas_conectores.json", "P32")
        self.assertIn("PUN 1P 17 cm", [g["id"] for g in d["grupos"]])
        self.assertEqual(d["laje"][0], -20.0)

    def test_gancho_do_colapso_na_borda(self):
        par = dict(titulo="PG", bx=50, by=150, borda_x="esquerda", dist_borda_x=0, col_gancho_borda=True)
        res = detalhar(par)
        d = vista3d.dados_3d(res)
        col = [e for e in d["elems"] if d["grupos"][e["g"]]["tipo"] == "colapso" and len(e["p"]) == 3]
        self.assertEqual(len(col), res["colapso"][0]["quant"])          # as barras em x: gancho na ponta da borda
        (x, _y, z0), (x1, _y1, z1) = col[0]["p"][:2]
        self.assertEqual(x, x1)
        self.assertGreater(z0, z1)

    def test_erro_no_pilar(self):
        res = detalhar(dict(titulo="PX", bx=0))
        with self.assertRaises(ValueError):
            vista3d.dados_3d(res)


class TestePagina(unittest.TestCase):
    def setUp(self):
        self.res, self.d = _dados("P2_cobrinha.json", "P2")

    def _dados_da_pagina(self, txt):
        m = re.search(r"window\.DADOS = (.*?);</script>", txt, re.S)
        return json.loads(m.group(1).replace("<\\/", "</"))

    def test_three_embutido_e_dados(self):
        txt = vista3d.html_3d(self.d)
        for ident in ("three-src", "three-orbit", "three-css2d"):
            self.assertIn(f'id="{ident}"', txt)
        self.assertNotIn("/*__DADOS__*/", txt)
        self.assertIn("<title>P2 - punção 3D</title>", txt)
        self.assertEqual(self._dados_da_pagina(txt), self.d)

    def test_sem_vendor_usa_o_cdn(self):
        with mock.patch.object(vista3d, "VENDOR", os.path.join(RAIZ, "nao_existe")):
            txt = vista3d.html_3d(self.d)
        self.assertNotIn('id="three-src"', txt)
        self.assertIn("cdn.jsdelivr.net/npm/three@0.169.0", txt)

    def test_texto_com_fim_de_script_nao_quebra_a_pagina(self):
        d = dict(self.d, projeto="</script><!-- x")
        txt = vista3d.html_3d(d)
        self.assertEqual(self._dados_da_pagina(txt)["projeto"], "</script><!-- x")

    def test_licenca_do_three(self):
        with open(os.path.join(vista3d.VENDOR, "LICENSE"), encoding="utf-8") as f:
            self.assertIn("The MIT License", f.read())


class TesteLinhaDeComando(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="pun_3d_")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _rodar(self, *args):
        return subprocess.run([sys.executable, os.path.join(RAIZ, "visualizar_3d.py"), *args], capture_output=True,
                              text=True, encoding="utf-8", cwd=RAIZ, env=dict(os.environ, PYTHONIOENCODING="utf-8"))

    def test_lote(self):
        r = self._rodar(os.path.join(RAIZ, "exemplos", "lote_bordas.json"), "--saida", self.pasta)
        self.assertEqual(r.returncode, 0, r.stderr)
        n = len(ler_projeto(os.path.join(RAIZ, "exemplos", "lote_bordas.json"))["pilares"])
        self.assertEqual(len(glob.glob(os.path.join(self.pasta, "PUN_*-3D.html"))), n)

    def test_um_pilar_e_pilar_com_erro(self):
        proj = os.path.join(self.pasta, "proj.json")
        with open(proj, "w", encoding="utf-8") as f:
            json.dump({"pilares": [dict(titulo="P1"), dict(titulo="P2", bx=0)]}, f)
        r = self._rodar(proj, "--saida", self.pasta)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("P2: não gravado", r.stdout)
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "PUN_P1-3D.html")))
        r = self._rodar(proj, "--saida", self.pasta, "--pilar", "P9")
        self.assertIn("Nenhum pilar gravado", r.stdout)


@unittest.skipUnless(TEM_TELA, "sem tela para o Tk")
class TesteJanela(unittest.TestCase):
    def setUp(self):
        from janela.app import App
        self.pasta = tempfile.mkdtemp(prefix="pun_3d_janela_")
        self.app = App()
        self.app.withdraw()
        self.app.abrir(os.path.join(RAIZ, "exemplos", "lote_conectores.json"))
        self.app.pasta.set(self.pasta)
        self.app.update()

    def tearDown(self):
        self.app.modificado = False
        self.app.destroy()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_ver_em_3d_e_lote(self):
        with mock.patch.object(vista3d, "abrir") as abrir:
            caminho = self.app.ver_3d()
        abrir.assert_called_once_with(caminho)
        self.assertTrue(os.path.exists(caminho))
        self.assertEqual(os.path.dirname(caminho), self.pasta)
        feitos = self.app.ver_3d_lote()
        self.assertEqual(len(feitos), len(self.app.projeto["pilares"]))
