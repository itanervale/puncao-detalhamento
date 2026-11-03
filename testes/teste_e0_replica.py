# -*- coding: utf-8 -*-
"""
E0: a gravação pela interface do TQS reproduz os desenhos de referência (ferros, cotas, blocos, níveis e estilos).
Pulado sem o TQS ou sem a pasta DesenhosReferencia (que não vai para o repositório).

Uso:  python -m unittest testes.teste_e0_replica -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
MODELOS = os.path.join(RAIZ, "DesenhosReferencia")

try:
    import TQS  # noqa: F401
    TEM_TQS = True
except ImportError:
    TEM_TQS = False

# Diferenças conhecidas e aceitas (PADRAO_desenho.md, seção 10). O comparador confere também a cor das entidades
# e o nível dos objetos (cotas e ferros):
#   PUN_P02: o rótulo "N2" que o modelo guarda dentro do ferro N2 (marca no corte), não refeito;
#   PUN_P02-R01: dois textos vazios das notas (resíduo de quebra de linha), não refeitos; 5 chamadas com flecha,
#   objetos de cota no modelo, refeitas como polilinha comum; 4 cotas "11" do gabarito com o objeto no 253 e o
#   texto no 224 (editadas à mão), refeitas com o objeto no nível do texto (a interface põe os dois no mesmo nível).
ESPERADO = {"PUN_P02": dict(so_modelo=1, so_replica=0, ferros=[(1, 8, 10.0, 220.0), (2, 3, 10.0, 320.0)]),
            "PUN_P02-R01": dict(so_modelo=11, so_replica=4, ferros=[(1, 17, 10.0, 450.0), (2, 11, 12.5, 395.0),
                                                                    (3, 3, 10.0, 320.0), (4, 8, 10.0, 220.0)])}


@unittest.skipUnless(TEM_TQS and os.path.isdir(MODELOS), "sem o TQS ou sem DesenhosReferencia")
class TesteReplica(unittest.TestCase):
    def test_replicas(self):
        import json
        from ferramentas import ler_modelo, comparar
        from dwg_tqs import teste_gravacao
        pasta = os.path.join(RAIZ, "saidas", "modelos")
        os.makedirs(pasta, exist_ok=True)
        for nome, esp in ESPERADO.items():
            with self.subTest(nome=nome):
                desp = os.path.join(pasta, nome + ".json")
                json.dump(ler_modelo.ler(os.path.join(MODELOS, nome + ".DWG")), open(desp, "w", encoding="utf-8"),
                          ensure_ascii=False, default=str)
                modelo, arqs, _, _ = teste_gravacao.replicar(desp)
                rep = ler_modelo.ler(arqs["dwg"])
                r = comparar.comparar(modelo, rep)
                self.assertEqual(sum(r["so_b"].values()), esp["so_replica"], "entidades a mais na réplica")
                self.assertEqual(sum(r["so_a"].values()), esp["so_modelo"], "entidades faltando na réplica")
                tab = sorted((e["ferro"]["mark"], e["ferro"]["tabela"][0][2], e["ferro"]["tabela"][0][1],
                              e["ferro"]["tabela"][0][8]) for e in rep["ents"] if e.get("ferro"))
                self.assertEqual(tab, esp["ferros"])
                self.assertIn("pdf", arqs)
                self.assertIn("dxf", arqs)


if __name__ == "__main__":
    unittest.main()
