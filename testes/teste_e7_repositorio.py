# -*- coding: utf-8 -*-
"""
E7: o repositório funciona sozinho, como o usuário o recebe do GitHub.
- independência: os módulos só importam a biblioteca padrão, o próprio repositório, o TQS, o Pillow e o matplotlib;
- os exemplos do README existem e detalham sem erro;
- sem o TQS (ou sem o matplotlib no --png), o detalhar.py para com uma mensagem clara, antes de gravar;
- o atalho da janela fica com fim de linha do Windows e o .gitignore deixa de fora as saídas e os modelos.

Uso:  python -m unittest testes.teste_e7_repositorio -v
"""
import ast
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nucleo.detalhe import detalhar                                    # noqa: E402
from nucleo.parametros import ler_projeto                              # noqa: E402

PROPRIOS = {"nucleo", "dwg_tqs", "janela", "ferramentas", "testes"}
TERCEIROS = {"TQS", "PIL", "matplotlib"}           # TQS: vem com o TQS; os outros: requirements*.txt
FORA = ("saidas", "DesenhosReferencia", ".git", "__pycache__")

try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False


def _codigo():
    for pasta, subpastas, arqs in os.walk(RAIZ):
        subpastas[:] = [s for s in subpastas if s not in FORA]
        for a in arqs:
            if a.endswith((".py", ".pyw")):
                yield os.path.join(pasta, a)


def _rodar(codigo, *args):
    """Roda o detalhar.py num processo à parte, com `codigo` antes (para esconder módulos)."""
    script = (f"import runpy, sys\n{codigo}\nsys.argv = ['detalhar.py'] + {list(args)!r}\n"
              f"runpy.run_path({os.path.join(RAIZ, 'detalhar.py')!r}, run_name='__main__')\n")
    return subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, encoding="utf-8",
                          cwd=RAIZ, env=dict(os.environ, PYTHONIOENCODING="utf-8"))


class TesteIndependencia(unittest.TestCase):
    def test_imports(self):
        permitidos = set(sys.stdlib_module_names) | PROPRIOS | TERCEIROS
        fora = []
        for arq in _codigo():
            with open(arq, encoding="utf-8") as f:
                arvore = ast.parse(f.read(), arq)
            for no in ast.walk(arvore):
                if isinstance(no, ast.Import):
                    nomes = [a.name for a in no.names]
                elif isinstance(no, ast.ImportFrom) and no.level == 0:
                    nomes = [no.module]
                else:
                    continue
                fora += [f"{os.path.relpath(arq, RAIZ)}:{no.lineno} {n}" for n in nomes
                         if n.split(".")[0] not in permitidos]
        self.assertEqual(fora, [], "importa de fora do repositório")

    def test_sys_path_so_na_raiz(self):
        """Nenhum módulo acrescenta ao sys.path uma pasta acima da raiz (o "..\\" dos outros apps)."""
        for arq in _codigo():
            with open(arq, encoding="utf-8") as f:
                for i, linha in enumerate(f, 1):
                    if re.search(r"sys\.path\.(insert|append)\(", linha) and re.search(r"pardir|['\"]\.\.", linha):
                        self.fail(f"{os.path.relpath(arq, RAIZ)}:{i}: {linha.strip()}")


class TesteExemplos(unittest.TestCase):
    def test_exemplos_do_readme_existem(self):
        with open(os.path.join(RAIZ, "README.md"), encoding="utf-8") as f:
            citados = set(re.findall(r"exemplos[/\\]([\w.-]+\.json)", f.read()))
        self.assertTrue(citados)
        for nome in citados:
            self.assertTrue(os.path.exists(os.path.join(RAIZ, "exemplos", nome)), nome)

    def test_exemplos_detalham_sem_erro(self):
        arqs = glob.glob(os.path.join(RAIZ, "exemplos", "*.json"))
        self.assertGreaterEqual(len(arqs), 5)
        for arq in arqs:
            for par in ler_projeto(arq)["pilares"]:
                with self.subTest(arquivo=os.path.basename(arq), pilar=par.get("titulo")):
                    self.assertEqual(detalhar(par)["erros"], [])


class TesteFaltas(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="pun_e7_")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_sem_tqs(self):
        saida = os.path.join(self.pasta, "x")
        r = _rodar("sys.modules['TQS'] = None", "exemplos/P2_cobrinha.json", "--saida", saida)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("precisa do TQS", r.stderr)
        self.assertIn("--so-relatorio", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertFalse(os.path.exists(saida))

    @unittest.skipUnless(TEM_TQS, "sem o TQS (a falta do TQS é avisada antes)")
    def test_png_sem_matplotlib(self):
        saida = os.path.join(self.pasta, "x")
        r = _rodar("import importlib.util as u; _f = u.find_spec\n"
                   "u.find_spec = lambda n, *a: None if n == 'matplotlib' else _f(n, *a)",
                   "exemplos/P2_cobrinha.json", "--png", "--saida", saida)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("precisa do matplotlib", r.stderr)
        self.assertFalse(os.path.exists(saida))                    # para antes de gravar o 1º DWG


class TesteArquivos(unittest.TestCase):
    def test_atalho_com_fim_de_linha_do_windows(self):
        bat, = glob.glob(os.path.join(RAIZ, "Detalhar*.bat"))
        with open(bat, "rb") as f:
            b = f.read()
        self.assertIn(b"\r\n", b)
        self.assertEqual(b.count(b"\n"), b.count(b"\r\n"))
        self.assertIn(b"janela_puncao.pyw", b)

    def test_gitignore(self):
        with open(os.path.join(RAIZ, ".gitignore"), encoding="utf-8") as f:
            linhas = {lin.strip() for lin in f}
        self.assertIn("saidas/", linhas)
        self.assertIn("DesenhosReferencia/", linhas)


if __name__ == "__main__":
    unittest.main()
