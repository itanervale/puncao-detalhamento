# Detalhamento de armadura de punção (TQS)

Gera o **detalhamento da armadura de punção** de pilares em DWG-TQS (com ferros inteligentes), PDF e DXF. O app não dimensiona: ele detalha a armadura definida pelo projetista.

Duas soluções:
- **barras dobradas em "cobrinha"**, em malha ortogonal;
- **conectores tipo pino (studs)** da [Trejor](https://www.trejor.com/conector-de-combate-a-puncao), em arranjo radial.

> **Situação:** em desenvolvimento. Feitas:
> - a E0 (base e padrão do desenho);
> - a E1 (núcleo da cobrinha);
> - a E2 (prancha da cobrinha em DWG-TQS);
> - a E3 (núcleo dos conectores);
> - a E4 (prancha dos conectores em DWG-TQS);
> - a E5 (janela);
> - a E6 (relatório do lote).
>
> A próxima é a E7 (fechamento do repositório). O plano está em [PLANO_Detalhamento_Puncao.md](PLANO_Detalhamento_Puncao.md) e o padrão gráfico em [PADRAO_desenho.md](PADRAO_desenho.md).

## Uso

### Janela

Abra pelo `Detalhar Punção.bat` (ou `pythonw janela_puncao.pyw [projeto.json]`). A janela segue o estilo dos editores do TQS:
- ribbon com as abas Pilar, Cobrinha, Conectores, Colapso, Lote, Exibir e Saídas;
- árvore do projeto e propriedades à esquerda;
- área CAD com a prévia da prancha, nas cores de tela do TQS ou nas de plotagem, e as abas Planta, Corte, Colapso, Prancha e Tabela;
- mensagens com as verificações.

Um projeto tem vários pilares (aba Lote: + Pilar, Duplicar, Apagar, Colar do Excel). A prévia não precisa do TQS. "Gerar o pilar" (Ctrl+G) e "Gerar o lote" (Ctrl+Shift+G) gravam pelo TQS.

### Linha de comando

```bash
python detalhar.py exemplos/P2_cobrinha.json
```

Grava um DWG-TQS por pilar do projeto (`saidas\<projeto>\PUN_<pilar>.DWG`), com o PDF e o DXF, e confere os comprimentos dos ferros que o TQS calcula com os do núcleo. No fim, grava o relatório do lote:
- `RELATORIO_<projeto>.txt`: pilares, ferros, aço por bitola com as repetições, pentes, avisos e erros;
- `RELATORIO_<projeto>_pilares.csv` e `RELATORIO_<projeto>_ferros.csv`, para o Excel.

Precisa do TQS. Serve às duas soluções; exemplos de conectores: `exemplos/P02_conectores.json` e `exemplos/lote_conectores.json`.

Opções:
- `--png`: imagem de conferência;
- `--saida PASTA`: outra pasta (sem ela, a `pasta_saida` do projeto, se houver, ou `saidas\<projeto>`);
- `--pilar P2`: um pilar só;
- `--so-relatorio`: só o relatório, sem gravar DWG e sem o TQS, com os comprimentos do núcleo.

## Requisitos

- Windows.
- Python 3.13.
- TQS V25 com a `TQSPythonInterface` (2.1.7 ou mais nova). Ela vem com a instalação do TQS e não faz parte deste repositório. Só é necessária para gravar DWG, PDF e DXF.
- Para os ícones da janela: `pip install -r requirements.txt` (Pillow). Sem ele, a janela abre com ícones vazios.
- Para as ferramentas de conferência: `pip install -r requirements-dev.txt`.

## Instalação

```bash
git clone https://github.com/itanervale/puncao-detalhamento.git
cd puncao-detalhamento
```

Não há outra instalação: o app usa a biblioteca padrão do Python e a interface do TQS.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `nucleo\` | Cálculo do desenho em Python puro (sem TQS): parâmetros, geometria, prancha em primitivas, verificações; dados dos níveis e do catálogo dos conectores |
| `dwg_tqs\` | Gravação pelo TQS: DWG-TQS com ferros inteligentes, PDF e DXF |
| `janela\` | Janela (Tk) no estilo do TQS: ribbon, vista CAD, prévia da prancha, lote |
| `ferramentas\` | Leitura e comparação de DWG-TQS, imagens de conferência, extração das penas |
| `exemplos\` | Projetos de exemplo (`.json`) |
| `testes\` | Testes que reproduzem os desenhos de referência |
| `saidas\` | Resultados (não vão para o repositório) |

## Projeto e núcleo (E1)

O projeto é um arquivo `.json` com uma lista de pilares; cada pilar guarda só o que difere dos padrões (`nucleo\parametros.py`, `PADROES`). Exemplos:
- `exemplos\P2_cobrinha.json`, `exemplos\P2x_cobrinha.json` (o mesmo pilar girado, com as cobrinhas em x) e `exemplos\lote_cobrinha.json` (cobrinha);
- `exemplos\P02_conectores.json` (conectores).

Os dois `P2`/`P02` são os pilares dos desenhos de referência.

```bash
python -m nucleo.detalhe exemplos/P2_cobrinha.json
```

Imprime, para cada pilar, os ferros (posição, quantidade, bitola, comprimento) e as verificações da NBR 6118:2026. Com conectores, imprime também os pentes e o quadro "ARMADURA DE COMBATE À PUNÇÃO"; o aço dos pentes não vira ferro do TQS e fica só no quadro. Não precisa do TQS.

```bash
python ferramentas/esquema.py exemplos/lote_cobrinha.json
```

Grava a imagem de conferência da geometria em `saidas\e1\` (outra pasta com `--saida`).
- Cobrinha: planta da punção, colapso e cortes ao longo da cobrinha.
- Conectores: planta dos pinos, colapso e um pente em corte.

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
