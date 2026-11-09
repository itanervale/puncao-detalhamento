# Detalhamento de armadura de punção (TQS)

Gera o **detalhamento da armadura de punção** de pilares em DWG-TQS (com ferros inteligentes), PDF e DXF. O app não dimensiona: ele detalha a armadura definida pelo projetista e confere as regras de detalhamento da NBR 6118:2026.

Duas soluções:
- **barras dobradas em "cobrinha"**, em malha ortogonal;
- **conectores tipo pino (studs)** da [Trejor](https://www.trejor.com/conector-de-combate-a-puncao), em pentes num arranjo radial.

Cada pilar vira uma prancha (`PUN_<pilar>.DWG`) no padrão dos desenhos do escritório:
- planta da armadura de punção;
- cortes ou o pente em corte;
- barras desenvolvidas;
- colapso progressivo;
- quadro dos conectores;
- notas.

Os comprimentos dos ferros são os que o próprio TQS calcula. O app os confere com os do núcleo.

> **Situação:** etapas E0 a E8 feitas (base, cobrinha, conectores, janela, relatório do lote, fechamento do repositório e importação do TQS). Por enquanto, só **pilares internos e retangulares**. O plano, com as decisões e as próximas etapas, está em [PLANO_Detalhamento_Puncao.md](PLANO_Detalhamento_Puncao.md); o padrão gráfico, em [PADRAO_desenho.md](PADRAO_desenho.md).

## Requisitos

- **Windows.**
- **Python 3.13.** É a versão em que o TQS instala a interface Python.
- **TQS V25** com a `TQSPythonInterface` 2.1.7 ou mais nova. Ela vem com a instalação do TQS e não faz parte deste repositório.
  - Só é necessária para gravar DWG, PDF e DXF.
  - A prévia da janela, as verificações e o relatório funcionam sem ela.
- **Opcional:**
  - `pip install -r requirements.txt` (Pillow), para os ícones da janela. Sem ele, a janela abre com ícones vazios.
  - `pip install -r requirements-dev.txt` (matplotlib), para as imagens de conferência (`--png` e as ferramentas).

## Do clone ao DWG

1. Baixe o repositório:

   ```bash
   git clone https://github.com/itanervale/puncao-detalhamento.git
   ```

   ```bash
   cd puncao-detalhamento
   ```

2. Instale os ícones da janela (opcional):

   ```bash
   py -3.13 -m pip install -r requirements.txt
   ```

3. Abra a janela com um duplo clique em `Detalhar Punção.bat`.
   - O atalho procura o Python 3.13 na instalação do usuário, na de todos os usuários e pelo lançador `pyw -3.13`.
   - Pela linha de comando: `pythonw janela_puncao.pyw [projeto.json]`.
4. Em **Arquivo > Abrir projeto** (Ctrl+O), escolha `exemplos\P2_cobrinha.json` (cobrinha) ou `exemplos\P02_conectores.json` (conectores). Confira a prévia nas abas Planta, Corte, Colapso, Prancha e Tabela.
5. **Gerar o pilar** (Ctrl+G) grava o DWG, o PDF e o DXF em `saidas\<projeto>\` e mostra nas mensagens a conferência dos comprimentos com o TQS.

Pela linha de comando, o mesmo resultado:

```bash
python detalhar.py exemplos/P2_cobrinha.json
```

## Janela

Segue o estilo dos editores do TQS:
- ribbon com as abas Pilar, Cobrinha, Conectores, Colapso, Lote, Exibir e Saídas, com todos os parâmetros e dicas;
- árvore do projeto e propriedades à esquerda;
- área CAD com a prévia da prancha, nas cores de tela do TQS ou nas de plotagem;
- mensagens com as verificações da NBR 6118:2026 e barra de status.

A prévia é refeita a cada mudança e não precisa do TQS.

Um projeto tem vários pilares. Na aba Lote:
- **+ Pilar**, **Duplicar** e **Apagar**;
- **Colar do Excel**, com as colunas Título; bx; by; h; repetições; solução, separadas por tabulação ou ponto e vírgula. A linha de cabeçalho é ignorada, e os pilares colados herdam o resto do pilar atual.

**Gerar o lote** (Ctrl+Shift+G) grava um DWG por pilar e o relatório do lote. **Relatório do lote** grava só o relatório, sem o TQS.

### Importar do TQS

**Lote > Importar do TQS** (ou o menu Pilar) traz os pilares de uma planta de um edifício do TQS.

1. Escolha a pasta do edifício (a que tem o `EDIFICIO.BDE`) e a planta, e clique em **Ler a planta**.
2. A leitura é feita numa cópia temporária (a raiz do edifício e a pasta da planta), num processo à parte. O edifício não é alterado, e o TQS pode estar aberto.
3. A tabela mostra todos os pilares da planta, com seção, posição, h da laje e os esforços. Marque os que vão para o projeto:
   - **marcados de saída:** os internos retangulares sem abertura a menos de 8d nem capitel;
   - **borda e canto:** podem ser marcados, com confirmação, porque o app os detalharia como internos;
   - **seção não retangular** (circular, L, U): não podem ser marcados.
4. **OK** acrescenta os pilares ao projeto. Os que já estão no projeto com o mesmo nome têm atualizadas as dimensões, o h, os cobrimentos e as repetições; o detalhamento escolhido fica. Os demais parâmetros vêm do pilar atual da janela.
5. **Ajustar s0 e os espaçamentos aos limites da NBR 6118** (opção ligada por padrão): com o d de cada pilar importado, s0 e os espaçamentos da cobrinha e dos conectores que passam de 0,5d e 0,75d descem até o limite, arredondados para baixo ao centímetro (laje de 20, d = 15,5: s0 = 7 e sr = 11). O número de linhas não muda. Vale também para os pilares do projeto que forem atualizados; as mensagens dizem o que mudou.

**O que vem do TQS:**
- **pilar:** nome e seção. Girado de 0° ou 90°, bx e by saem da poligonal; em outro ângulo, ficam nos eixos do pilar, com aviso;
- **laje:** espessura e cobrimentos (os de laje do edifício, ou os de laje protendida). Com lajes de espessuras diferentes na planta, vale a mais comum, com aviso, porque a interface do TQS não dá o contorno de cada laje;
- **repetições:** as da planta (um pavimento tipo repetido 5 vezes dá "5X");
- **posição:** interno quando nenhuma borda da laje (contornos) nem viga fica a menos de 2d da face do pilar, ou seja, o contorno C' não é cortado; borda com um lado, canto com dois;
- **esforços, só para conferência:** as reações da grelha por pilar em cada combinação de ELU (título começando por "ELU"), em tf e tf·m, característicos. Ficam no pilar (árvore e propriedades) e na tabela do lote. O app não dimensiona.

Os esforços precisam da grelha processada no TQS (`FOR<nº>M.GRE` e `.RSX` na pasta da planta). As listagens `GREANA*.LST` não são necessárias: o app roda o `FGREANA.EXE` do TQS para cada combinação.

Pela linha de comando:

```bash
python -m dwg_tqs.leitor_tqs plantas "C:\TQS\<edifício>"
```

```bash
python -m dwg_tqs.leitor_tqs planta "C:\TQS\<edifício>" <planta> --saida leitura.json --projeto projeto.json
```

O segundo grava a leitura e um projeto com os pilares internos (ou os de `--pilares P5,P7`; `--todos` inclui os de borda e canto; `--ajustar` traz s0 e os espaçamentos para os limites da norma).

## Linha de comando

```bash
python detalhar.py exemplos/lote_conectores.json
```

Grava um DWG-TQS por pilar do projeto, com o PDF e o DXF, e confere os comprimentos dos ferros que o TQS calcula com os do núcleo. No fim, grava o relatório do lote.

Opções:
- `--saida PASTA`: outra pasta. Sem ela, vale a `pasta_saida` gravada pela janela no projeto, se houver, ou `saidas\<projeto>`;
- `--pilar P2`: um pilar só;
- `--png`: imagem de conferência de cada prancha (precisa do matplotlib);
- `--so-relatorio`: só o relatório, com os comprimentos do núcleo. Não grava DWG e não precisa do TQS.

Sem o TQS (ou sem o matplotlib no `--png`), o comando para antes de gravar, com uma mensagem dizendo o que falta.

Para só ver os ferros e as verificações, sem o TQS:

```bash
python -m nucleo.detalhe exemplos/P02_conectores.json
```

## Saídas

Em `saidas\<projeto>\` (a pasta `saidas\` não vai para o repositório):

| Arquivo | Conteúdo |
|---|---|
| `PUN_<pilar>.DWG` | Prancha do pilar em DWG-TQS (sistema 9, subsistema 13, escala 1:15), com ferros inteligentes e o "1X" das repetições |
| `PUN_<PILAR>-R00.PDF` | PDF gravado pelo TQS, com a tabela de plotagem (`TABPLTA`) |
| `PUN_<pilar>.DXF` | DXF com as cores da plotagem |
| `RELATORIO_<projeto>.txt` | Pilares, ferros, aço por bitola com as repetições (NBR 7480), pentes somados, avisos e erros |
| `RELATORIO_<projeto>_pilares.csv` e `_ferros.csv` | O mesmo, para o Excel (ponto e vírgula, vírgula decimal) |

Antes de regravar um DWG, o app copia o anterior para `anteriores\<nome>_<data>_<hora>.DWG`, para não perder edições feitas no TQS. Se o DWG estiver aberto no TQS e não puder ser regravado, grava `<nome>_HHMMSS.DWG` e avisa.

## Projeto (`.json`)

O projeto é uma lista de pilares. Cada pilar guarda só o que difere dos padrões (`nucleo\parametros.py`, `PADROES`), que são os dos desenhos de referência:

```json
{
  "formato": "puncao-detalhamento",
  "versao": 1,
  "pilares": [
    {"titulo": "P2", "bx": 150, "by": 50, "h_laje": 27, "c_sup": 2.0, "c_inf": 2.0, "solucao": "cobrinha"},
    {"titulo": "P5", "repeticoes": 2, "bx": 40, "by": 40, "h_laje": 25, "solucao": "conectores"}
  ]
}
```

**Unidades:** comprimentos em cm, bitolas em mm. `bx` é a dimensão do pilar na horizontal da prancha e `by` na vertical.

**Pilar e laje**

| Parâmetro | Padrão | O que é |
|---|---|---|
| `titulo` | P1 | Nome do pilar (vai para o DWG: `PUN_<titulo>`) |
| `repeticoes` | 1 | Pilares iguais; vira o "1X", "2X" do desenho, que o TQS multiplica no resumo |
| `bx`, `by` | 50, 150 | Dimensões do pilar |
| `h_laje` | 27 | Espessura da laje |
| `c_sup`, `c_inf` | 2,5 | Cobrimentos. O pino e a cobrinha vão de cobrimento a cobrimento |
| `solucao` | cobrinha | `cobrinha` ou `conectores` |
| `escala` | 15 | Escala da prancha |
| `neg_bitola_ext`, `neg_bitola_int` | 10, 10 | Bitolas das duas camadas da negativa existente (para a altura útil e o aviso dos vértices) |
| `d` | calculada | Altura útil: d = h − c_sup − e − (3·ø1 + ø2)/4, com a negativa abaixo da cabeça do pino ou do trecho de cima da cobrinha (e) |

**Colapso progressivo** (face inferior, passando dentro do pilar)

| Parâmetro | Padrão | O que é |
|---|---|---|
| `col_bitola` | 10 | Bitola |
| `col_ext` | 85 | Comprimento além da face |
| `col_n_face_bx`, `col_n_face_by` | 8, 3 | Barras em cada face de comprimento bx e by |

**Cobrinha** (malha ortogonal)

| Parâmetro | Padrão | O que é |
|---|---|---|
| `cob_s` (`cob_s_x`, `cob_s_y`) | 17 | Espaçamento da malha (por direção, se diferente) |
| `cob_s0` | 11 | Distância da face à 1ª linha de pernas |
| `cob_linhas` (`cob_linhas_x`, `cob_linhas_y`) | 4 | Linhas de pernas além de cada face, contando a de s0 |
| `cob_bitola` | 10 | Bitola da cobrinha |
| `cob_direcao` | menor | Cobrinhas paralelas ao lado `menor` do pilar, ao `maior`, em `x` ou em `y` |
| `mont_bitola` | 12,5 | Montagem positiva, uma por fileira de pernas, na dobra de baixo |
| `mont_ext` | 30 | Montagem além da última linha |
| `mont_arred` | 5 | Arredondamento da montagem (para cima) |

**Conectores** (pentes Trejor)

| Parâmetro | Padrão | O que é |
|---|---|---|
| `con_s0`, `con_sr` | 11, 17 | Distância da face à 1ª linha de pinos e entre linhas |
| `con_pinos` | 3 | Pinos por pente |
| `con_n_face_bx`, `con_n_face_by` | 3, 5 | Pentes em cada face de comprimento bx e by |
| `con_dist_canto` | 5 | Distância do pente ao canto do pilar, ao longo da face |
| `con_inclinados` | auto | Pentes inclinados por canto: `auto` (o menor número que deixa os pinos de fora vizinhos a até 2d), `cruz` (nenhum) ou um número |
| `con_bitola` | 10 | Bitola do pino (CA-50); a cabeça vem do catálogo (`nucleo\catalogo_trejor.json`) |
| `con_cabeca_esp` | 1,0 | Espessura da cabeça (entra na altura útil) |
| `con_arred_mm` | 5 | Comprimento do pino arredondado para baixo (mm) |
| `con_trilhos`, `con_trilho_bitola` | 2, 8 | Vergalhões que ligam os pinos |
| `con_montagem` | false | Montagem positiva nos conectores (opcional; o padrão do escritório usa as barras da laje) |

As verificações (s0 ≤ 0,5d, espaçamentos ≤ 0,75d, pinos ou pernas vizinhos a até 2d, bitolas, catálogo da Trejor) aparecem nas mensagens da janela, no terminal e no relatório. Um aviso não impede a gravação; um erro de parâmetro impede.

## Exemplos

| Arquivo | O que tem |
|---|---|
| `exemplos/P2_cobrinha.json` | O P2 do desenho de referência da cobrinha (150 × 50, laje de 27) |
| `exemplos/P2x_cobrinha.json` | O mesmo pilar girado, com as cobrinhas em x e os cortes embaixo da planta |
| `exemplos/lote_cobrinha.json` | Cinco pilares: o P2, um quadrado com 2X, outra direção, cobrimento de 2,5 e um em x |
| `exemplos/P02_conectores.json` | O P02 do desenho de referência dos conectores (50 × 150, 20 pentes de 3 pinos) |
| `exemplos/lote_conectores.json` | Cinco pilares: o P02, um quadrado, 5 pinos por pente, montagem ligada e arranjo em cruz |

## Limitações desta versão

- Só pilares internos e retangulares. Faltam os de borda e de canto, os circulares e as aberturas na laje.
- Conectores só no arranjo "antes da armadura" (pentes com trilhos); falta o "posterior à armadura".
- A importação do TQS ajusta só s0 e os espaçamentos (opção). O número de linhas, as bitolas e o colapso progressivo continuam com o projetista; as verificações mostram o que passa dos limites.

## Testes

```bash
python -m unittest discover -s testes -t . -p "teste_*.py" -v
```

Os testes do núcleo, da janela, do relatório e da importação não precisam do TQS. A importação usa uma leitura real gravada em `testes\dados\`. Os testes que gravam DWG são pulados sem o TQS, e a réplica dos modelos é pulada sem a pasta `DesenhosReferencia\`, que fica fora do repositório. O teste do leitor numa cópia de um edifício real usa a pasta da variável `PUN_EDIFICIO_TESTE` e é pulado sem ela ou sem o TQS.

## Ferramentas de conferência (desenvolvimento)

```bash
python ferramentas/esquema.py exemplos/lote_cobrinha.json
```

Imagem da geometria calculada pelo núcleo (não é a prancha), em `saidas\e1\`. Precisa do matplotlib.

```bash
python ferramentas/ler_modelo.py "<desenho>.DWG"
```

Lê um DWG-TQS a partir de uma cópia temporária, sem alterar o original, e grava o despejo em `saidas\modelos\<desenho>.json`. Precisa do TQS.

```bash
python ferramentas/imagem.py "saidas/modelos/<desenho>.json"
```

Imagem de conferência do despejo. As fontes do TQS são mais largas que as da imagem, então textos colados podem aparecer sobrepostos nela e não no PDF.

```bash
python ferramentas/comparar.py <a>.json <b>.json
```

Compara dois despejos por nível, tipo, posição e texto.

```bash
python ferramentas/capturar_janela.py exemplos/P2_cobrinha.json
```

Abre a janela, passa pelas vistas e abas e grava cada estado em PNG (`saidas\janela\`).

```bash
python dwg_tqs/teste_gravacao.py
```

Refaz os desenhos de referência pela interface do TQS e os compara com os originais. Precisa da pasta `DesenhosReferencia\`.

```bash
python ferramentas/extrair_penas.py
```

Regrava `nucleo\niveis.json` a partir da tabela de plotagem do TQS instalado.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `nucleo\` | Python puro (sem TQS): parâmetros, cobrinha, conectores, colapso, verificações, relatório, folha e pranchas em primitivas; níveis e catálogo da Trejor |
| `dwg_tqs\` | Gravação pelo TQS (DWG-TQS com ferros inteligentes, PDF e DXF) e leitura de uma planta do TQS para a importação (`leitor_tqs.py`) |
| `janela\` | Janela (Tk) no estilo do TQS |
| `ferramentas\` | Leitura e comparação de DWG-TQS, imagens de conferência, captura da janela, extração das penas |
| `exemplos\` | Projetos de exemplo |
| `testes\` | Testes |
| `saidas\` | Resultados (fora do repositório) |

## Problemas comuns

- **"A gravação do DWG precisa do TQS"**: o Python em uso não enxerga a `TQSPythonInterface`. Use o Python 3.13 em que o TQS a instalou, ou use `--so-relatorio` e a prévia da janela.
- **DWG com sufixo de hora (`PUN_P2_103512.DWG`)**: o DWG anterior estava aberto no TQS. Feche-o e grave de novo.
- **O atalho não abre a janela**: rode `py -3.13 janela_puncao.pyw` num terminal para ver a mensagem de erro.
