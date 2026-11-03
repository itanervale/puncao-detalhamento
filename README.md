# Detalhamento de armadura de punção (TQS)

Gera o **detalhamento da armadura de punção** de pilares em DWG-TQS (com ferros inteligentes), PDF e DXF. O app não dimensiona: ele detalha a armadura definida pelo projetista.

Duas soluções:
- **barras dobradas em "cobrinha"**, em malha ortogonal;
- **conectores tipo pino (studs)** da [Trejor](https://www.trejor.com/conector-de-combate-a-puncao), em arranjo radial.

> **Situação:** em desenvolvimento, etapa E0 (base e padrão do desenho). O plano está em [PLANO_Detalhamento_Puncao.md](PLANO_Detalhamento_Puncao.md) e o padrão gráfico em [PADRAO_desenho.md](PADRAO_desenho.md).

## Requisitos

- Windows.
- Python 3.13.
- TQS V25 com a `TQSPythonInterface` (2.1.7 ou mais nova). Ela vem com a instalação do TQS e não faz parte deste repositório. Só é necessária para gravar DWG, PDF e DXF.
- Para as ferramentas de conferência: `pip install -r requirements-dev.txt`.

## Instalação

```bash
git clone <endereço do repositório>
cd <pasta do repositório>
```

Não há outra instalação: o app usa a biblioteca padrão do Python e a interface do TQS.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `nucleo\` | Cálculo do desenho em Python puro (sem TQS): parâmetros, geometria, prancha em primitivas, verificações; dados dos níveis e do catálogo dos conectores |
| `dwg_tqs\` | Gravação pelo TQS: DWG-TQS com ferros inteligentes, PDF e DXF |
| `janela\` | Interface (a partir da etapa E5) |
| `ferramentas\` | Leitura e comparação de DWG-TQS, imagens de conferência, extração das penas |
| `exemplos\` | Projetos de exemplo (`.json`) |
| `testes\` | Testes que reproduzem os desenhos de referência |
| `saidas\` | Resultados (não vão para o repositório) |

## Ferramentas (E0)

```bash
python ferramentas/ler_modelo.py "<desenho>.DWG"
```

Lê um DWG-TQS a partir de uma cópia temporária, sem alterar o original, e grava o despejo em `saidas\modelos\<desenho>.json`.

```bash
python ferramentas/imagem.py "saidas/modelos/<desenho>.json"
```

Gera a imagem de conferência do despejo.

```bash
python ferramentas/comparar.py <a>.json <b>.json
```

Compara dois despejos por nível, tipo, posição e texto.

```bash
python dwg_tqs/teste_gravacao.py
```

Refaz os desenhos de referência pela interface do TQS (`saidas\e0\REPLICA_*.DWG`, PDF e DXF) e os compara com os originais. Precisa da pasta `DesenhosReferencia\`, que não vai para o repositório.

```bash
python -m unittest discover -s testes -t . -p "teste_*.py" -v
```

Roda os testes. Os que dependem do TQS ou dos desenhos de referência são pulados quando eles faltam.

```bash
python ferramentas/extrair_penas.py
```

Regrava `nucleo\niveis.json` a partir da tabela de plotagem do TQS instalado.
