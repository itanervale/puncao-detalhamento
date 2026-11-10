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

Cada pilar também tem uma **visualização 3D** (`PUN_<pilar>-3D.html`), que abre no navegador sem o TQS e sem internet.

> **Situação:** etapas E0 a E8 feitas (base, cobrinha, conectores, janela, relatório do lote, fechamento do repositório e importação do TQS) e a E9 (cobrinha e conectores): **pilares internos, de borda e de canto**, retangulares. O plano, com as decisões e as próximas etapas, está em [PLANO_Detalhamento_Puncao.md](PLANO_Detalhamento_Puncao.md); o padrão gráfico, em [PADRAO_desenho.md](PADRAO_desenho.md).

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

### Pilar de borda e de canto

Na aba Pilar, o grupo **Borda livre** diz de que lado do pilar a laje termina: **Em x** (esquerda ou direita) e **Em y** (baixo ou cima), cada um com a distância da face do pilar à borda (0 = pilar faceando a borda). Uma borda faz o pilar de borda; uma em x e outra em y, de canto. Vale para as duas soluções.

As regras são as do pilar interno, cortadas pela borda:
- nada passa da borda: as cobrinhas, a montagem e as barras de colapso param no cobrimento da laje (o maior entre c sup. e c inf.);
- **pilar recuado da borda:** sem opção, a armadura de punção não passa da linha da face voltada para a borda (como se o pilar faceasse a borda). Duas opções, desligadas por padrão, no grupo Borda livre das abas Cobrinha e Conectores, por região:
  - **Pinos na face recuada:** a armadura diante dessa face, até a borda;
  - **Linhas construtivas:** além dos cantos, junto da borda;
- **cobrinha:** diante da face voltada para a borda, as peças vão até o cobrimento, com uma perna a s0 (se couber) e uma junto da borda (5 cm antes da ponta) se ela ficar a mais de 3 cm da última perna regular; com as linhas construtivas, as peças inteiras ao lado do pilar seguem até a borda. Com a borda ao longo das linhas, a linha além da face voltada para a borda vira a peça inteira (as duas opções), as duas peças das faces para fora (só as construtivas) ou uma peça entre os prolongamentos das faces, com as pernas de 5 cm a L − 5 cm (só a face recuada);
- ao lado do pilar, a peça inteira começa na ponta do lado livre, pelo trecho de baixo. Cada forma de peça é uma posição;
- a montagem de cada fileira vai só nas linhas que têm perna nela, `mont_ext` além da última;
- **borda curta:** a montagem entre a face do pilar e a borda não é desenhada quando ficaria com menos de `mont_min_borda` (30 cm); os vértices de baixo dessas linhas ficam na armadura positiva da laje, e as mensagens dizem isso;
- **colapso:** as barras paralelas à borda como no interno; as perpendiculares terminam no cobrimento da borda. No As só contam as faces voltadas para a laje: 3 no pilar de borda e 2 no de canto, faceando ou recuado (a face voltada para a borda não conta). **Gancho na borda** (aba Colapso, desligado por padrão) põe um gancho de 90° com ponta de 8ø (NBR 6118, 9.4.2.3) na ponta da borda; o app confere se ele cabe entre os cobrimentos;
- as verificações de 2d e de C'' e a ancoragem do colapso valem só nos lados livres; com a borda a 2d ou mais da face, o app avisa que o pilar pode ser tratado como interno;
- uma viga a menos de 2d da face é tratada como borda: a armadura para no cobrimento da face da viga.

Na prancha: a linha da borda com o texto "BORDA LIVRE" na planta e no colapso, as seções com a laje terminando reta na borda, a distância da face à borda numa fila de cotas própria e os detalhes de cada forma de peça. O pente mestre e as cotas de s0 ficam num lado livre, nunca na borda curta, e o gabarito dos pentes mestres mostra o pilar de borda ou de canto desprezando a borda curta (do lado da borda, sem pente mestre e com a borda na face). Quando a montagem da borda curta é omitida, a NOTA 5 manda usar a armadura positiva da laje como montagem.

**Conectores** (como no LPUNC; plano, respostas Q10 a Q12):
- **face voltada para a borda:** pentes só com **Pinos na face recuada** e só com os pinos que cabem: o último pino, mais a ponta do pente (meia cabeça e o gancho do trilho), até o cobrimento da borda. Pode sair um pente mais curto ("PUN 1P 17 cm", "PUN 2P 17 cm"), que vira outro tipo no quadro; sem pino que caiba, a face fica sem pentes;
- **faces perpendiculares à borda:** os pentes da face, com o pente da ponta a `con_dist_canto` do canto ou afastado o bastante para o trilho ficar no cobrimento da borda;
- **inclinados:** só nos cantos internos (as duas faces voltadas para a laje);
- **linhas construtivas** (`con_construtivas`, aba Conectores > Borda livre, desligada por padrão): no pilar recuado, um pente a mais em cada face perpendicular, além do canto, junto da borda (como o PuncV1);
- os pinos de fora vizinhos através de um canto do lado da borda não entram na verificação de 2d, porque ali o contorno termina na borda;
- na prancha: os contornos das linhas de pinos recortados na borda, a NOTA 1 do lado que tem pentes, o "TOPO LAJE" do lado livre (ou fora da laje, além da borda) e as cotas só dos lados com pentes.

### Importar do TQS

**Lote > Importar do TQS** (ou o menu Pilar) traz os pilares de uma planta de um edifício do TQS. Antes de abrir a importação, o app avisa: "Programa em fase de testes, recomenda-se a duplicação do edifício".

1. Escolha a pasta do edifício (a que tem o `EDIFICIO.BDE`) e a planta, e clique em **Ler a planta**.
2. A leitura é feita numa cópia temporária (a raiz do edifício e a pasta da planta), num processo à parte. O edifício não é alterado, e o TQS pode estar aberto.
3. A tabela mostra todos os pilares da planta, com seção, posição, h da laje e os esforços. Marque os que vão para o projeto:
   - **marcados de saída:** os internos, os de borda e os de canto retangulares, sem abertura a menos de 8d nem capitel. Nos de borda e de canto, as bordas da laje (ou as vigas) a menos de 2d da face vão para o grupo Borda livre do pilar;
   - **bordas ou vigas em lados opostos** e **pilares girados com borda:** podem ser marcados, com confirmação, porque o app os detalharia como internos (ele detalha uma borda por direção, nos eixos da planta);
   - **seção não retangular** (circular, L, U): não podem ser marcados.
4. **OK** acrescenta os pilares ao projeto. Os que já estão no projeto com o mesmo nome têm atualizadas as dimensões, o h, os cobrimentos e as repetições; o detalhamento escolhido fica. Os demais parâmetros vêm do pilar atual da janela.
5. **Sugerir o colapso progressivo** (opção ligada por padrão): a mesma sugestão do botão da aba Colapso (abaixo), depois do ajuste de s0 e dos espaçamentos.
6. **Ajustar s0 e os espaçamentos aos limites da NBR 6118** (opção ligada por padrão): com o d de cada pilar importado, s0 e os espaçamentos da cobrinha e dos conectores que passam de 0,5d e 0,75d descem até o limite, arredondados para baixo ao centímetro (laje de 20, d = 15,5: s0 = 7 e sr = 11). O número de linhas não muda. Vale também para os pilares do projeto que forem atualizados; as mensagens dizem o que mudou.

**O que vem do TQS:**
- **pilar:** nome e seção. Girado de 0° ou 90°, bx e by saem da poligonal; em outro ângulo, ficam nos eixos do pilar, com aviso;
- **laje:** espessura, cobrimentos (os de laje do edifício, ou os de laje protendida) e fck (o concreto da planta ou, sem ele, o de vigas e lajes do edifício). Com lajes de espessuras diferentes na planta, vale a mais comum, com aviso, porque a interface do TQS não dá o contorno de cada laje;
- **repetições:** as da planta (um pavimento tipo repetido 5 vezes dá "5X");
- **posição:** interno quando nenhuma borda da laje (contornos) nem viga fica a menos de 2d da face do pilar, ou seja, o contorno C' não é cortado; borda com um lado, canto com dois vizinhos, com o lado e a distância passados ao pilar. Uma viga conta como borda. Na reimportação, um pilar que deixou de ser de borda volta a interno;
- **esforços, só para conferência:** as reações da grelha por pilar em cada combinação de ELU (título começando por "ELU"), em tf e tf·m, característicos. Ficam no pilar (árvore e propriedades) e na tabela do lote. O app não dimensiona.

### Colapso progressivo (NBR 6118:2026, 19.5.4)

O app confere a armadura contra colapso progressivo de cada pilar:
- **Ancoragem além de C'':** com armadura de punção, as barras de colapso devem estar ancoradas além do contorno C'', que fica 2d além da última linha da armadura de punção. A parte da barra além de C'' (comprimento além da face menos a distância a C'') deve ter pelo menos lb (9.4.2.4: barra reta, boa aderência na face inferior, fck da laje). Nos modelos do escritório, as barras de 85 cm além da face terminam antes de C'' (P2 da cobrinha: C'' a 108 cm; P02 dos conectores: a 90 cm), e a verificação avisa.
- **Capacidade, com as cargas do TQS:** As·fyd ≥ 1,5·FSd, com FSd = 1,2 × a maior força Z das combinações de ELU (característica, 1 tf = 10 kN) e As a soma das barras que cruzam cada face do pilar (uma barra que atravessa o pilar cruza duas faces).

Na aba Colapso, **Sugerir no pilar** e **Sugerir em todos** propõem, com a bitola escolhida:
- o nº de barras por face pelas cargas do TQS, na proporção dos lados, com no mínimo 2 por face;
- o comprimento além da face: a distância a C'' mais o lb, para cima a 5 cm. Sem cargas, só esse comprimento.

Os esforços precisam da grelha processada no TQS (`FOR<nº>M.GRE` e `.RSX` na pasta da planta). As listagens `GREANA*.LST` não são necessárias: o app roda o `FGREANA.EXE` do TQS para cada combinação.

Pela linha de comando:

```bash
python -m dwg_tqs.leitor_tqs plantas "C:\TQS\<edifício>"
```

```bash
python -m dwg_tqs.leitor_tqs planta "C:\TQS\<edifício>" <planta> --saida leitura.json --projeto projeto.json
```

O segundo grava a leitura e um projeto com os pilares internos, de borda e de canto (ou os de `--pilares P5,P7`; `--todos` inclui os de bordas em lados opostos, os girados com borda e os com abertura ou capitel; `--ajustar` traz s0 e os espaçamentos para os limites da norma).

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

### Visualização 3D

```bash
python visualizar_3d.py exemplos/P2_cobrinha.json --abrir
```

Grava uma página por pilar (`PUN_<pilar>-3D.html`, na mesma pasta dos DWG) e, com `--abrir`, abre cada uma numa janela própria (o Edge ou o Chrome em modo aplicativo, ou o navegador padrão). Não precisa do TQS nem de internet: o three.js (licença MIT) vai embutido na página, a partir de `vendor\three-0.169.0`. Aceita também `--saida` e `--pilar`. Na janela, Exibir > 3D > **Ver em 3D** (Ctrl+3) faz o mesmo para o pilar atual, e **3D do lote** grava as páginas de todos os pilares.

A página tem as mesmas funções da visualização do app de vigas protendidas:
- a laje translúcida (até a borda livre, quando há) e o pilar, com a opacidade ajustável;
- cada ferro com a bitola real e as dobras em canto vivo, na cor da posição (N1, N2...): cobrinhas, montagem e colapso progressivo; nos conectores, cada pente com os pinos, as cabeças e os trilhos;
- os contornos das linhas de pinos, o contorno C'' da ancoragem do colapso (2d além da última linha) e os cortes do desenho (A-A, B-B);
- escala vertical de 0,1× a 50× (a planta fica em escala real);
- vistas prontas: 3D, planta, inferior, frontal, lateral e os cortes do desenho, em perspectiva ou ortogonal;
- a lista das posições, para ligar, desligar e destacar;
- os dados do ferro ou do pino sob o mouse;
- uma seção móvel em x ou em y, com o desenho 2D em escala real (roda: aproximar; arrastar: deslocar). O modelo pode ser cortado nela, e o duplo clique numa cobrinha leva a seção ao plano dela;
- tema claro ou escuro, avisos das verificações e o estado lembrado por pilar no computador.

As alturas são as dos cortes da prancha: cobrinha de cobrimento a cobrimento, montagem sobre as dobras de baixo, colapso na face inferior, pinos a partir do cobrimento inferior.

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
| `PUN_<pilar>-3D.html` | Visualização 3D do pilar (`visualizar_3d.py` ou Exibir > 3D na janela), com o three.js embutido |

Além do leiaute dos modelos, as seções da cobrinha (na ponta de baixo, ou à esquerda com as cobrinhas em x) e o corte A-A dos conectores (à direita) têm as cotas da espessura da laje e dos cobrimentos: numa fila os cobrimentos inferior e superior e, por fora, a espessura.

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
| `fck` | 25 | Concreto da laje (MPa), para o lb da ancoragem do colapso além de C'' |
| `borda_x`, `borda_y` | "" | Borda livre: `esquerda` ou `direita` em x, `baixo` ou `cima` em y; vazio (ou `nenhuma`) = sem borda desse lado |
| `dist_borda_x`, `dist_borda_y` | 0 | Distância da face do pilar à borda livre (0 = faceando) |
| `solucao` | cobrinha | `cobrinha` ou `conectores` |
| `escala` | 15 | Escala da prancha |
| `neg_bitola_ext`, `neg_bitola_int` | 10, 10 | Bitolas das duas camadas da negativa existente (para a altura útil e o aviso dos vértices) |
| `d` | calculada | Altura útil: d = h − c_sup − e − (3·ø1 + ø2)/4, com a negativa abaixo da cabeça do pino ou do trecho de cima da cobrinha (e) |

**Colapso progressivo** (face inferior, passando dentro do pilar)

| Parâmetro | Padrão | O que é |
|---|---|---|
| `col_bitola` | 10 | Bitola |
| `col_ext` | 85 | Comprimento além da face |
| `col_n_face_bx`, `col_n_face_by` | 3, 8 | Barras em cada face de comprimento bx e by (no pilar padrão de 50 × 150: 3 na face de 50 e 8 na de 150, como no P02) |
| `col_gancho_borda` | false | Gancho de 90° (ponta de 8ø) nas barras que terminam na borda livre |
| `cob_face_recuada`, `con_face_recuada` | false | Pilar recuado da borda: armadura de punção diante da face voltada para a borda (cobrinha ou conectores) |
| `cob_construtivas`, `con_construtivas` | false | Pilar recuado da borda: além dos cantos, as cobrinhas ao lado do pilar seguem até a borda; nos conectores, um pente a mais junto da borda |

**Cobrinha** (malha ortogonal)

| Parâmetro | Padrão | O que é |
|---|---|---|
| `cob_s` (`cob_s_x`, `cob_s_y`) | 17 | Espaçamento da malha (por direção, se diferente) |
| `cob_s0` | 11 | Distância da face à 1ª linha de pernas |
| `cob_linhas` (`cob_linhas_x`, `cob_linhas_y`) | 4 | Linhas de pernas além de cada face, contando a de s0 |
| `cob_bitola` | 10 | Bitola da cobrinha |
| `cob_direcao` | maior | Cobrinhas paralelas ao lado `maior` do pilar (padrão desde 09/11/2026), ao `menor` (como no modelo do P2), em `x` ou em `y` |
| `mont_bitola` | 12,5 | Montagem positiva, uma por fileira de pernas, na dobra de baixo |
| `mont_ext` | 30 | Montagem além da última linha |
| `mont_arred` | 5 | Arredondamento da montagem (para cima) |
| `mont_min_borda` | 30 | Pilar de borda: a montagem ao lado do pilar, da face até a borda livre, com menos que isso não é desenhada |

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
| `exemplos/lote_bordas.json` | Seis pilares de borda e de canto com a cobrinha: borda faceando, a 20 cm com as duas opções, a 15 cm ao longo das linhas sem elas, canto com gancho e dois com o pilar deitado (um com as linhas construtivas) |
| `exemplos/lote_bordas_conectores.json` | Cinco pilares de borda e de canto com os conectores: borda faceando, a 20 cm com as duas opções (pentes de 1 pino), canto faceando com gancho, canto recuado com as duas opções e a montagem (pentes de 2 pinos) e o pilar deitado |

## Limitações desta versão

- Só pilares retangulares. Faltam os circulares e as aberturas na laje.
- Uma borda livre por direção: lados opostos (laje mais estreita que o pilar + 4d, ou borda de um lado e viga do outro) não são tratados.
- Conectores só no arranjo "antes da armadura" (pentes com trilhos); falta o "posterior à armadura".
- A importação do TQS ajusta s0 e os espaçamentos e sugere o colapso (opções). O número de linhas e as bitolas continuam com o projetista; as verificações mostram o que passa dos limites.

## Testes

```bash
python -m unittest discover -s testes -t . -p "teste_*.py" -v
```

Os testes do núcleo, da janela, do relatório, da importação e da visualização 3D não precisam do TQS. A página 3D é conferida no navegador à parte (precisa de WebGL). A importação usa uma leitura real gravada em `testes\dados\`. Os testes que gravam DWG são pulados sem o TQS, e a réplica dos modelos é pulada sem a pasta `DesenhosReferencia\`, que fica fora do repositório. O teste do leitor numa cópia de um edifício real usa a pasta da variável `PUN_EDIFICIO_TESTE` e é pulado sem ela ou sem o TQS.

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
python -m ferramentas.sobreposicoes exemplos/lote_bordas.json
```

Procura sobreposições nas pranchas, sem o TQS: textos sobre textos (inclusive os das cotas, onde o TQS os escreve) e textos cruzados pelas linhas de chamada e pelas marcas dos cortes. Um teste passa todos os exemplos por ela.

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
| `nucleo\` | Python puro (sem TQS): parâmetros, cobrinha, conectores, colapso, verificações, relatório, folha e pranchas em primitivas, visualização 3D (`vista3d.py` e o modelo `vista3d.html`); níveis e catálogo da Trejor |
| `vendor\three-0.169.0\` | three.js (licença MIT), embutido nas páginas 3D |
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
