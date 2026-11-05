# Detalhamento de armadura de punção: plano em etapas

Versão 2, 03/11/2026, com as respostas do usuário (seção 8).

App só de **detalhamento** (sem dimensionamento) da armadura de punção de pilares, em duas soluções:
- **barras dobradas em "cobrinha"**, em malha ortogonal;
- **conectores tipo pino (studs) da Trejor**, em arranjo radial.

Começa pelos pilares internos (centrais); borda e canto vêm depois. A referência visual do detalhamento final são os dois desenhos de `DesenhosReferencia\`, feitos em parceria. As camadas (níveis) deles não mudam.

**Uso:** o app roda no computador do usuário, que baixa (clona) o repositório do GitHub. O GitHub guarda o código e a evolução; não hospeda nada. O repositório tem tudo o que o processamento precisa, menos o TQS e a interface Python dele, que vêm com a instalação do TQS. Esta pasta não importa nada de fora dela (nem do app de punção, `_apps\Punção`).

---

## 1. O que os dois modelos mostram

Os dois desenhos detalham o mesmo pilar nas duas soluções: P02, 50 × 150, laje de 27 cm. Os dois são DWG-TQS 9/13 ("TQS AGC2 - Desenho de armação", tabela de plotagem `TABPLTA`), na escala 1:15, com coordenadas em cm reais. Foram lidos em cópias, só para leitura. O inventário completo fica no `PADRAO_desenho.md` (E0).

### 1.1 Conectores: `PUN_P02.DWG`

- **Vistas:**
  - VISTA EM PLANTA (PINOS), com os contornos dos pinos;
  - CORTE A-A;
  - VISTA EM PLANTA (COLAPSO PROGRESSIVO);
  - quadro "ARMADURA DE COMBATE À PUNÇÃO";
  - NOTAS IMPORTANTES (3 notas).
- **Título:** "P02" (nível 222), "1X" (202) e "(50x150)" (220).
- **Pente:** bloco `PUN 3P 17 cm`.
  - 3 pinos a 11, 28 e 45 cm da face (s0 = 11, sr = 17).
  - Pino de 220 mm (27 − 2,5 − 2,5), com cabeça de 0,8 cm mais 0,2 cm de concordância.
  - 2 trilhos ø8, um de cada lado dos pinos, cada um com gancho numa ponta.
  - Os trilhos ficam embaixo, como no arranjo "anterior à armadura" do catálogo.
- **Distribuição dos pentes:**
  - face de 150: 5 pentes, a 5 cm dos cantos e a cada 35 cm;
  - face de 50: 3 pentes, a 5 cm dos cantos e a cada 20 cm;
  - cantos: 1 pente a 45° em cada um, com o 1º pino a 11 cm do canto;
  - total: 20 pentes.
- **Cotas "39":** distância entre os pinos externos de pentes vizinhos, a que se compara com 2d.
- **Corte A-A:** as barras de flexão ficam abaixo da cabeça do pino.
  - No topo, a 1ª camada vai de 3,5 a 4,5 cm da face e a 2ª de 4,5 a 5,5 cm.
  - Embaixo, a mesma disposição, espelhada.
- **Colapso progressivo (face inferior):**
  - N1 8 ø10 C=220 (50 + 2 × 85);
  - N2 3 ø10 C=320 (150 + 2 × 85).
- **Quadro:** "QUANTIDADE: 1 x 20 PENTES" / "DESCRIÇÃO: 3 { 10 mm (CA-50) com 220 mm + 2 { 8 mm (CA-50)".
- **Correções (aprovadas):**
  - fuste do pino desenhado com 8 mm, quando ele é ø10;
  - cabeça de 32,5 mm, quando o catálogo dá 32 mm;
  - trilhos ø8 desenhados com 5 mm de largura na planta, que passam a ter a largura real.

### 1.2 Cobrinha: `PUN_P02-R01.DWG`

- **Vistas:**
  - SEÇÃO A-A, girada 90°, com a cobrinha desenvolvida duas vezes: pelas faces e pelos eixos (notas 3 e 4);
  - VISTA EM PLANTA (ARM. PUNÇÃO);
  - VISTA EM PLANTA (COLAPSO PROGRESSIVO);
  - DET. PLANTA "GABARITO PENTES MESTRES";
  - NOTAS IMPORTANTES (4 notas).
- **Título:** "P2" (222).
- **Malha:**
  - 17 × 17, com a 1ª linha a 11 cm das faces e 4 linhas além de cada face nas duas direções (11 + 3 × 17 = 62).
  - Dentro do pilar, a malha continua com espaços ajustados, com o acréscimo no meio: 172 = 8 × 17 + 2 × 18 e 72 = 17 + 19 + 19 + 17.
- **N1, 17 ø10 C=450 (ferro genérico):** 17 cobrinhas paralelas ao lado de 50, a cada 17 cm (18 no meio).
  - Cada uma tem 11 pernas e 12 trechos horizontais (10 × 17 + 2 × 19). Na ponta de y menor começa por um trecho de cima e termina, na outra ponta, por um de baixo (conferido no corte, na E1).
  - Na planta, os trechos de cima são tracejados e os de baixo, contínuos.
  - Os pontos do ferro estão pelos eixos: pernas de 22 entre eixos, logo 450 = 208 + 11 × 22.
  - No corte, as faces externas da cobrinha ficam a **2,0 cm** das faces da laje (altura externa 23 = 27 − 2 − 2). Ver a pergunta Q1.
- **Barras de flexão no corte:**
  - em cima, a 1ª camada vai de 3,3 a 4,8 cm da face, logo abaixo do trecho superior da cobrinha, e a 2ª de 4,8 a 5,8 cm;
  - embaixo, espelhada.
- **N2, 11 ø12,5 C=395:** montagem positiva, perpendicular às cobrinhas, uma por linha de pernas, 60 cm além da última linha. 150 + 2 × (62 + 60) = 394, que arredondado vira 395.
- **Colapso:** N3 3 ø10 C=320 e N4 8 ø10 C=220, 85 cm além da face.
- **Gabarito:** retângulo dos "pentes mestres" a 11 cm das faces, com a chamada "PENTE MESTRE P/ LOCAÇÃO".
- **Bloco `COBRINHA 12`:** a cobrinha em planta.
  - Linha dupla de 1,6 cm de largura, contínua nos trechos de baixo e tracejada nos de cima, com círculos de 1,6 cm nas pernas.
  - A largura é a de uma barra de 16 mm, para uma cobrinha ø10 (pergunta Q2).

### 1.3 Camadas, blocos e ferros (mantidos como estão)

| Uso no modelo | Níveis |
|---|---|
| Título / repetição / dimensões | 222 / 202 / 220 |
| Títulos das vistas, letras de corte | 226 (bloco `$CORTEA` do TQS) |
| Cotas (objetos IPOCOT) | 221 |
| Notas: corpo / "NOTA n:" / título do quadro | 227 / 242 / 220 |
| Contornos dos pinos | 200 |
| Pilar e eixos (tracejados) | 203, 204, 205 |
| Laje em corte, molduras | 240, 0 |
| Pinos, pentes, barras desenhadas nas vistas | 0, 233, 241, 243, 245, 253, 254 |
| Linhas de identificação dos ferros inteligentes | 246 (colapso), 244 (montagem N2), 242 (cobrinha N1) |
| Textos dos ferros inteligentes | 1 |

- **Ferros inteligentes:** só o colapso, a montagem e a cobrinha. As barras dentro das vistas são linhas comuns.
- **Pentes:** são blocos e ficam só no quadro de texto (decisão P11).
- **Regra das camadas:** o app grava cada elemento no nível, na cor e no estilo do modelo. Não aplica as convenções dos outros apps e não altera a `TABPLTA`.

---

## 2. Conector Trejor

Especificação: <https://www.trejor.com/conector-de-combate-a-puncao>. A tabela está no catálogo "Conectores de Combate a Punção" (2019, p. 3) ligado à página.

| Pino CA-50 (mm) | 6,3 | 8 | 10 | 12,5 | 16 | 20 | 25 | 32 |
|---|---|---|---|---|---|---|---|---|
| Diâmetro do bolt (cabeça), mm | 20 | 28 | 32 | 40 | 51 | 63 | 79 | 101 |
| Resistência (kN) | 14,2 | 25,2 | 39,3 | 56,5 | 100,5 | 157,1 | 245,4 | 402 |

- **Pinos:** cabeça dupla, forjados, sem solda estrutural.
- **Comprimento:** sob medida, a partir de 110 mm.
- **Ligação:** os pinos são ligados por vergalhões que garantem o espaçamento.
- **Montagem:** "anterior à armadura" (trilho embaixo, como no modelo) ou "posterior" (trilho em cima).
- **Espessura da cabeça:** o catálogo não informa; o modelo usa 0,8 cm mais 0,2 cm de concordância (pergunta Q3).
- **No app:** a tabela fica em `nucleo\catalogo_trejor.json`.

---

## 3. Arquitetura: tudo local

```
Punção_Detalhamento\            (= o repositório)
  nucleo\      Python puro (só a biblioteca padrão): parâmetros -> geometria ->
               prancha em primitivas (linha, arco, círculo, texto, cota, bloco, ferro),
               cada uma com o nível do modelo; verificações
  dwg_tqs\     gravação pelo TQS: primitivas -> DWG-TQS com ferros inteligentes,
               PDF e DXF do TQS (correção do CONTINUOUS e cores da plotagem)
  janela\      interface (Tk), no estilo do app de telas soldadas (E5)
  ferramentas\ leitura e comparação de DWG-TQS, imagens de conferência, penas
  exemplos\    projetos .json (P02 com conectores, P2 com cobrinha, lote)
  testes\      reproduzem os números dos dois modelos
  saidas\      resultados (fora do repositório)
  DesenhosReferencia\   modelos do parceiro (fora do repositório: não são
               necessários para rodar o app)
```

- **Requisitos:** Windows, Python 3.13 e TQS V25 com a `TQSPythonInterface` (2.1.7 ou mais nova).
- **Núcleo e prévia:** rodam sem o TQS, só para conferir.
- **Saídas:** o DWG-TQS, o PDF (com o carimbo da licença) e o DXF saem pelo TQS.
- **Pastas com nomes próprios:** o gerador fica em `dwg_tqs\`, não em `tqs\`, porque no Windows o nome se confundiria com o pacote `TQS`.
- **Interface:** com o uso local, a página HTML perdeu a razão de ser. A interface fica em Tk, como a do app de telas: os módulos de ribbon, ícones, vista e diálogos são copiados para `janela\`, com a origem anotada.
- **Lote pela linha de comando:** `python detalhar.py projeto.json`.
- **Independência:** nada vem de `..\`. O que for aproveitado é copiado com a origem anotada:
  - `txt_tqs`, a troca de caracteres para as fontes do TQS;
  - `_dxf_continuo` e `_dxf_com_cores`, as correções do DXF;
  - `_pdf_nome`, o nome do PDF com mais de 23 caracteres;
  - os módulos da janela de telas.
- **Penas dos níveis:** as cores e penas da `TABPLTA` e da `PLOTPENA.PEN` são copiadas para `nucleo\niveis.json`, para a prévia ficar igual em qualquer máquina.
- **Repositório:** público no GitHub, com git desde a E0 e um commit por etapa. O `gh` não está instalado nesta máquina. O usuário cria o repositório vazio no site, e o envio é feito pelo `git push`; o Git for Windows pede o login pelo navegador.

---

## 4. Interface (E5)

A janela segue o app de telas soldadas:

- **Barras:** menus, acesso rápido e ribbon com as abas Pilar, Cobrinha, Conectores, Colapso, Lote, Exibir e Saídas.
- **À esquerda:** árvore do projeto (projeto > pilares > vistas) e propriedades.
- **Área gráfica:** fundo preto, com as cores de tela do TQS.
  - Zoom pela roda, deslocamento pelo arrasto e enquadramento por duplo clique.
  - Dica sob o mouse com o nível e a medida.
  - Alternância para as cores de plotagem.
- **Abas de vista:** Planta da punção, Corte, Colapso, Prancha e Tabela.
- **Rodapé:** mensagens das verificações e barra de status.
- **Comportamento:** atualização automática e atalhos.
- **Lote:** menu suspenso do pilar atual, com "+ Pilar", "Duplicar" e "Colar do Excel".

---

## 5. Dados de entrada

Padrões dos modelos. Os itens marcados com † foram acrescentados e aprovados pelo usuário em 03/11/2026.

**Comuns (por pilar):**

| Parâmetro | Padrão | Observação |
|---|---|---|
| Título do pilar | P02 | nível 222 e nome do arquivo (`PUN_P02`); um DWG por pilar |
| Repetições | 1 | "1X" no 202 e "1 x 20 PENTES" no quadro |
| Dimensões do pilar (b × h) | 50 × 150 | b na horizontal da prancha |
| Espessura da laje | 27 | |
| Cobrimento superior / inferior | 2,5 / 2,5 | o pino e a cobrinha vão até eles (P4) |
| Solução | conectores / cobrinha | |
| Bitolas da negativa † | ø10 / ø10 | camada externa e interna, para a altura útil (seção 6.1) |
| Altura útil d † | calculada (seção 6.1) | pode ser digitada |
| Colapso: bitola | ø10 | |
| Colapso: comprimento além da face | 85 | |
| Colapso: barras por face | 8 nas faces de 150, 3 nas de 50 | |
| Escala † | 1:15 | |

**Cobrinha:**

| Parâmetro | Padrão | Observação |
|---|---|---|
| Espaçamento da malha | 17 | opção de um valor por direção |
| Distância da face à 1ª linha (s0) † | 11 | |
| Linhas de pernas além da face | 4 | contando a de s0; opção de um valor por direção |
| Bitola da cobrinha | ø10 | |
| Bitola da montagem positiva (N2) | ø12,5 | |
| Montagem além da última linha † | 30 | 60 no modelo; 30 pelo usuário em 03/11/2026; arredondada para cima a 5 cm |
| Direção das cobrinhas † | paralela ao lado menor | com opção de mudar (P6) |
| Altura externa | h − c_sup − c_inf | pontos do ferro pelo eixo: altura − ø (P4; Q1) |

**Conectores:**

| Parâmetro | Padrão | Observação |
|---|---|---|
| Distância da face à 1ª linha de pinos (s0) | 11 | |
| Distância entre linhas de pinos (sr) | 17 | |
| Pinos por pente † | 3 | "3P" no nome do bloco |
| Pentes na face vertical / horizontal | 5 / 3 | |
| Distância do pente ao canto † | 5 | |
| Pentes inclinados nos cantos | automático | o menor número que deixa os pinos externos a ≤ 2d; opção "cruz" (P9) |
| Bitola do pino | ø10 | cabeça de 32 mm pelo catálogo |
| Comprimento do pino | h − c_sup − c_inf | arredondado para baixo a 5 mm; mínimo de 110 mm (P4) |
| Espessura da cabeça † | 1,0 cm | 0,8 + 0,2 de concordância, do modelo (Q3) |
| Trilhos † | 2 ø8 | desenhados com a largura real (P10) |
| Montagem positiva | desligada | opcional; a prioridade são as armaduras de flexão existentes (P7) |

---

## 6. Regras e verificações (sem dimensionamento)

### 6.1 Altura útil (P3)

A NBR 6118:2026 (19.5.2.1) define d = (dx + dy)/2, em que dx e dy são as alturas úteis nas duas direções. No pilar interno, elas vão até o centro das barras da negativa.

O pino e a cobrinha ocupam o cobrimento: as extremidades da armadura de punção "deve[m] estar ancorada[s] fora do plano da armadura de flexão" (19.5.3.3). Por isso a negativa fica abaixo da cabeça do pino ou do trecho superior da cobrinha. É o que os dois modelos mostram no corte (seção 1).

Logo:

```
dx = h − c_sup − e − ø1/2          (camada externa)
dy = h − c_sup − e − ø1 − ø2/2     (camada interna)
d  = (dx + dy)/2 = h − c_sup − e − (3·ø1 + ø2)/4      (= h − c_sup − e − ø, com ø1 = ø2)
e  = espessura da cabeça do pino (1,0 cm no modelo) ou bitola da cobrinha
```

Nos modelos (h = 27; negativa ø10):

| Modelo | c_sup | e | d | 0,5d | 0,75d | 2d | Situação |
|---|---|---|---|---|---|---|---|
| Conectores | 2,5 | 1,0 | 22,5 | 11,25 | 16,9 | 45 | s0 = 11 passa; **sr = 17 passa de 0,75d por 1 mm**; 39 ≤ 2d passa |
| Cobrinha | 2,0 (Q1) | 1,0 | 23,0 | 11,5 | 17,25 | 46 | passa |
| Cobrinha com c = 2,5 | 2,5 | 1,0 | 22,5 | 11,25 | 16,9 | 45 | sr = 17 passa de 0,75d por 1 mm |

A fórmula antiga do plano (h − c_sup − ø) deixava d 1 cm maior, contra a segurança. A verificação gera aviso, sem bloquear o desenho.

### 6.2 Geometria

**Cobrinha** (com as regras do usuário de 03/11/2026; detalhes na E1):
- **Malha:** as linhas partem de s0 em cada face; entre as linhas de s0, n = parte inteira do vão ÷ s, com a sobra no meio.
- **Nada passa por cima do pilar.**
- **Peças:** toda peça começa na face do pilar (ou no prolongamento dela) pelo trecho de baixo; a ponta de fora tem o comprimento s.
- **Montagem:** interrompida nas faces e 30 cm além da última linha.

**Conectores:**
- **Pentes nas faces:** distribuídos por igual entre as distâncias ao canto.
- **Pentes inclinados:** a 45° (ou em leque) a partir do canto, com o 1º pino a s0 do canto.

**Colapso:** barras retas na face inferior, passando dentro do pilar. O critério de espaçamento sai da medida dos modelos (E1).

### 6.3 Verificações da NBR 6118:2026 (avisos)

- s0 ≤ 0,5d e sr ≤ 0,75d (19.5.3.3, Figura 19.9);
- três ou mais linhas (19.5.3.3);
- pinos vizinhos do último contorno a ≤ 2d, ou aviso de cruz (19.5.3.4, Figura 19.8);
- bitola da cobrinha ≤ h/20 e contato com barras de bitola maior ou igual nos vértices (20.4);
- pino ≥ 110 mm (catálogo);
- cobrimentos e d coerentes com a espessura.

---

## 7. Etapas

Cada etapa termina com a aprovação do usuário e um commit.

**E0. Base e padrão do desenho** (feita em 03/11/2026; falta a conferência do usuário no TQS)
- Pasta como repositório: `README.md`, `CLAUDE.md`, `.gitignore`, `.gitattributes`, `git init`.
- `ferramentas\ler_modelo.py`, `comparar.py`, `imagem.py` e `extrair_penas.py`.
- `PADRAO_desenho.md`, com o inventário dos modelos e o que a gravação precisa (seção 10).
- `nucleo\niveis.json` (penas da TABPLTA e cores de tela de um DWG 9/13, iguais às dos modelos), `nucleo\catalogo_trejor.json` e `nucleo\textos.py`.
- `dwg_tqs\arquivo.py`: desenho novo no padrão e gravação de DWG, PDF e DXF.
- `dwg_tqs\teste_gravacao.py` e `testes\teste_e0_replica.py`: réplica dos dois modelos pela interface.
  - Conectores: 956 de 957 entidades iguais, com cor e nível dos objetos.
  - Cobrinha: 1681 de 1692, com as diferenças conhecidas.
  - Ferros com os comprimentos do TQS iguais aos do modelo.
  - Cores diferentes na réplica (relatos do usuário), duas causas:
    - o objeto dos ferros caía no nível atual (221, 222); agora vai no 220;
    - a tabela de níveis de tela dos modelos (34 níveis próprios), que o `File.Open` da interface escondia; agora é gravada em todo desenho.
  - As cotas continuam com as cores padrão (3 e 7) guardadas em cada uma; falta o usuário conferir no editor.
- **Aceite:** o usuário abre `saidas\e0\REPLICA_PUN_P02.DWG` e `REPLICA_PUN_P02_R01.DWG` no TQS (editor e tabela de ferros).

**E1. Núcleo da cobrinha (pilar interno)** (feita em 03/11/2026)
- **Parâmetros e altura útil:** `nucleo\parametros.py`, com padrões, validação e d pela seção 6.1. O projeto é um `.json` com o formato `puncao-detalhamento` 1 e uma lista de pilares.
- **Geometria:**
  - `nucleo\cobrinha.py`: malha, cobrinhas, pontos pelo eixo, montagem e gabarito;
  - `nucleo\colapso.py`.
- **Verificações e montagem:**
  - `nucleo\verificacoes.py`: avisos da seção 6.3, mais o maior espaçamento entre pernas vizinhas ≤ 2d;
  - `nucleo\detalhe.py`: junta tudo e numera os ferros (cobrinhas, montagem, colapso em x, colapso em y). Linha de comando: `python -m nucleo.detalhe <projeto.json>`.
- **Testes e exemplos:**
  - `testes\teste_e1_cobrinha.py`: 20 testes, que não dependem do TQS nem dos modelos;
  - `exemplos\P2_cobrinha.json` e `exemplos\lote_cobrinha.json`.
- **Conferência:** `ferramentas\esquema.py` grava a imagem da geometria em `saidas\e1\` (planta, colapso e dois cortes).
- **1ª versão:** reproduzia o P2 do modelo, com 17 N1 ø10 C=450 passando por cima do pilar e os mesmos 24 pontos do ferro genérico.
- **Regras do usuário (03/11/2026), na versão atual:**
  - **Nada passa por cima do pilar:** evita interferência com a armadura do pilar ("é a forma correta").
  - **Peças começando na face:** toda cobrinha começa na face do pilar pelo trecho de baixo (na face inferior da laje).
  - **Montagem:** interrompida nas faces do pilar e com 30 cm além da última linha de cobrinhas (no modelo, 60).
- **Como as regras foram aplicadas:**
  - **Linhas diante das faces** (as que passavam por cima do pilar): duas peças, cada uma da face para fora: trecho de baixo até s0, pernas e uma ponta de s além da última.
  - **Linhas ao lado do pilar:** inteiras (decisão do usuário, Q6), começando na ponta de fora pelo trecho de baixo.
    - Entre as pernas de s0, o número de espaços ao lado da face é ímpar: o menor que deixa cada um ≤ s, com as pernas arredondadas a 0,5 cm e simétricas.
    - No P2, são 5 espaços (14,5 / 14,5 / 14 / 14,5 / 14,5), com pernas em 3,5 / 18 / 32 / 46,5.
    - Motivo: a montagem é reta e precisa achar a dobra de baixo do mesmo lado em todas as cobrinhas de uma fileira. Com o número ímpar, a linha inteira tem as dobras do mesmo lado que as peças da face.
    - A 1ª versão desta regra cortava as linhas laterais em três peças.
  - **Montagem:** uma barra por fileira de pernas, encostada na perna do lado do trecho de baixo.
    - Fileiras fora da faixa do pilar: contínuas.
    - Fileiras ao lado do pilar: duas barras, da face do pilar até 30 cm além da última linha.
    - Comprimento arredondado para cima a 5 cm.
- **Resultado no P2:**
  - N1 18 ø10 C=167 (79 + 4 × 22, da face para fora);
  - N2 8 ø10 C=472 (208 + 12 × 22, inteiras ao lado do pilar);
  - N3 8 ø12,5 C=335 e N4 8 ø12,5 C=95 (montagem);
  - N5 3 ø10 C=320 e N6 8 ø10 C=220 (colapso);
  - linhas em 7×17, 18, 18 e 7×17;
  - d = 23, sem avisos.
- **Outras regras adotadas (a confirmar):**
  - **Espaços entre as linhas de s0:** n = parte inteira do vão ÷ s, com a sobra no espaço do meio (ou metade em cada um dos dois do meio). Isso reproduz o 18 + 18 e o 19 + 19 do modelo. Como nada passa mais por cima do pilar, a regra só define as linhas diante das faces e as pernas ao lado delas; o espaço maior (28 num pilar de 40) passa pelo aviso de 2d.
  - **Montagem:** no núcleo, encostada na perna, a (ø cobrinha + ø montagem)/2 = 1,125 do eixo; o modelo desenha a 1,5. A E2 desenha a 1,125, porque a cobrinha passou a ter a bitola real.
  - **Colapso:** n barras por face, cada uma no meio da sua faixa ((i + ½)·L/n), como nos dois modelos; comprimento = lado + 2 × 85, arredondado para cima ao centímetro.

**E2. Prancha da cobrinha em DWG-TQS** (feita em 04/11/2026; falta a conferência do usuário no TQS)
- **Módulos:**
  - `nucleo\folha.py`: folha em primitivas, sem TQS (linha, polilinha, círculo, arco, texto, cota, bloco, ferro), com o contorno de barra e a linha de quebra;
  - `nucleo\prancha_cobrinha.py`: o leiaute;
  - `dwg_tqs\gravar.py`: transcreve a folha para o DWG;
  - `dwg_tqs\prancha.py`: grava DWG, PDF e DXF e confere os comprimentos do TQS com os do núcleo;
  - `detalhar.py` (raiz): linha de comando, um DWG por pilar (`PUN_<pilar>`), em `saidas\<projeto>\`.
- **Vistas, no padrão do R01 e com as camadas dele:**
  - **SEÇÃO A-A e SEÇÃO B-B:** giradas como no modelo e alinhadas com a planta.
    - A-A pela linha diante da face mais perto do meio, com o pilar cortado; B-B pela linha ao lado do pilar, com o pilar tracejado.
    - Laje e pilar com quebras (0 e 240); cobrinha em contorno (224 cheio e 233) e eixo em traço-ponto (0).
    - Barras nos vértices: negativa no 254 e montagem no 243. Colapso: em corte no 245 e, na A-A, a barra em y no 245, interrompida nos trechos de baixo.
    - Flexão de referência em traço-ponto; chamadas da NOTA 1 (225 e 210) na A-A.
  - **Para cada cobrinha, dois detalhes:**
    - o ferro inteligente com os trechos entre eixos (o TQS escreve os comprimentos; NOTA 3) e as cotas em relação às faces do pilar (68 / 11 / 50 / 11 / 68);
    - o desenho pelas faces (NOTA 4), com as barras nos vértices e as cotas entre faces (18/16, 23, 11,5 e 17,5).
  - **VISTA EM PLANTA (ARM. PUNÇÃO):**
    - cobrinhas em blocos `COBRINHA N<pos> <ø>`, com a bitola real (Q2), trechos de cima tracejados e pernas em círculo, inseridas no 241;
    - montagem no 243 e pilar no 227;
    - cotas das linhas, das fileiras diante das faces, das pernas ao lado do pilar e do s0;
    - "PENTE MESTRE P/ LOCAÇÃO" e marcas dos cortes (letra e bandeira no 253);
    - embaixo, N3 e N4 identificadas (244), com as cotas de 30 e do vão.
  - **VISTA EM PLANTA (COLAPSO PROGRESSIVO):** como no modelo (203/240, 245, N5 e N6 no 246, cotas de 85 e os dois textos).
  - **DET. PLANTA:** gabarito dos pentes mestres a 1:25, com as cotas em valores reais (`dimlfc`).
  - **NOTAS IMPORTANTES** (as 4 do modelo) e título com nome, "Nx" e dimensões.
- **Ferros:** objeto no 220; inserções no 242 (cobrinhas), 244 (montagem) e 246 (colapso).
- **Resultado:** os comprimentos do TQS conferem com os do núcleo nos quatro pilares do `exemplos\lote_cobrinha.json`. No P2: 18 ø10 C=167, 8 ø10 C=472, 8 ø12,5 C=335, 8 ø12,5 C=95, 3 ø10 C=320 e 8 ø10 C=220. A folha do P2 tem 80,4 × 34,4 cm (largura útil do A1).
- **Achado:** o TQS arredonda cada trecho do ferro genérico ao centímetro.
  - Com as pernas ao lado da face em meio centímetro, o N2 dava C=474 no TQS e 472 no núcleo.
  - Agora essas pernas ficam em centímetros inteiros (no P2: 14 / 15 / 14 / 15 / 14), e o núcleo soma os trechos arredondados, como o TQS.
- **Escolhas desta etapa (a confirmar):**
  - **Montagem em planta:** fica a 1,125 da perna (encostada), não a 1,5 do modelo, porque a cobrinha passou a ser desenhada com a bitola real (Q2).
  - **Cortes:** dois (A-A e B-B), porque há dois tipos de cobrinha.
  - **Detalhes:** dois por cobrinha.
- **Pendente:** prancha com as cobrinhas em x (opção da P6). O núcleo calcula, mas a folha avisa que ainda não desenha.
- **Testes:** `testes\teste_e2_prancha.py`, sem o TQS (folha, blocos, ferros, só níveis dos modelos) e com ele (DWG do P2 e comprimentos).

**E3. Núcleo dos conectores (radial)** (feita em 05/11/2026)
- **Aceite:** reproduz o P02: 20 pentes "3P 17 cm", 220 mm, cotas 35, 20 e 39, N1 8 ø10 C=220 e N2 3 ø10 C=320.
- **Resultado:**
  - os 20 pentes saem nas mesmas posições e ângulos dos blocos do modelo, como os contornos (11, 28 e 45), os espaçamentos entre pentes (35 nas faces de 150, 20 nas de 50) e as oito distâncias de 39,1 nos cantos (a cota "39");
  - pino de 220 mm, cabeça de 32 mm, d = 22,5;
  - quadro igual ao do modelo, linha a linha;
  - colapso N1 8 ø10 C=220 e N2 3 ø10 C=320.
- **Módulos:** `nucleo\conectores.py` (pentes, leque dos cantos, pino pelo catálogo, contornos, distâncias, quadro) e `verificacoes.conectores`. O `detalhe.py` junta tudo: os pentes não são ferros do TQS (P11), e os ferros são só os do colapso.
- **Regras implementadas:**
  - **Pentes das faces:** por igual entre as distâncias ao canto (`con_dist_canto`); um só fica no meio da face.
  - **Inclinados (P9):** saem do canto, com o 1º pino a s0 dele, e os ângulos repartidos por igual entre as direções das duas faces (k = 1: a 45°; k = 3: 202,5°, 225° e 247,5° no canto inferior esquerdo).
    - `con_inclinados` = "auto" (padrão): o menor k que deixa os pinos de fora vizinhos nos cantos a ≤ 2d.
    - "cruz" = nenhum.
    - Também aceita um número fixo.
    - O "auto" só olha os cantos. O espaçamento entre pentes da mesma face depende do nº de pentes nela e tem verificação própria ("aumente o nº de pentes na face").
  - **Pino:** h − c_sup − c_inf, arredondado para baixo a 5 mm. A cabeça vem do catálogo; fora dele, aviso, e a cabeça é desenhada com 3,2·ø.
  - **Trilhos:** eixo encostado nas cabeças, a (cabeça + ø do trilho)/2 do eixo dos pinos (ø8 com cabeça de 32: 2,0; no modelo, 1,875).
- **Verificações (avisos):**
  - s0 ≤ 0,5d e sr ≤ 0,75d;
  - 3 pinos ou mais por pente;
  - pinos de fora vizinhos nos cantos e ao longo das faces a ≤ 2d (19.5.3.4, Figura 19.8; "cruz" avisa que o C'' fica interrompido nos cantos);
  - pino do catálogo e ≥ 110 mm.

  No P02, o único aviso é o já conhecido: sr = 17 passa de 0,75d = 16,875 por 1 mm.
- **Outros casos (lote de conferência):**
  - pilar 40 × 40: 1 inclinado por canto;
  - 5 pinos por pente: 3 inclinados (pinos de fora a 79 do canto);
  - laje de 18: 3 inclinados (2d = 27);
  - face de 100 com 2 pentes: aviso de 90 > 2d.
- **Testes:** `testes\teste_e3_conectores.py`, com 17 testes sem o TQS; a suíte inteira tem 44.
- **Exemplo:** `exemplos\P02_conectores.json`.
- **Conferência:** `python ferramentas/esquema.py exemplos/P02_conectores.json --saida saidas/e3`. A imagem mostra a planta dos pinos (inclinados em roxo, trilhos com a largura real, contornos e as distâncias nos cantos), o colapso e um pente em corte.
- **Linha de comando:** o `detalhar.py` imprime o núcleo dos conectores e avisa que a prancha é a E4.
- **Montagem positiva nos conectores (P7):** o parâmetro existe (`con_montagem`, desligado), mas a geometria não está definida. Ligado, só gera um aviso (pergunta Q7).
- **Correção de passagem:** `dwg_tqs\arquivo.py` fechava mal os arquivos lidos e gravados (`ResourceWarning` nos testes); agora usa `with`.

**E4. Prancha dos conectores em DWG-TQS**
- Inclui as correções do pino ø10 e dos trilhos ø8.

**E5. Janela (Tk)**
- Interface da seção 4, com prévia, propriedades e avisos.

**E6. Lote e saídas**
- Lote de pilares, um DWG por pilar (`PUN_<pilar>`), PDF e DXF do TQS, relatório.
- `detalhar.py` pela linha de comando.

**E7. Fechamento do repositório**
- README de uso, exemplos e teste num clone limpo (sem os modelos), do clone ao DWG.

**Depois desta rodada:**
- pilares de borda e de canto;
- pilares circulares;
- aberturas;
- conectores "posterior à armadura";
- troca de dados, por JSON, com o app de punção e com o modelo do TQS.

---

## 8. Decisões do usuário (03/11/2026)

- **GitHub:** só como repositório (código e evolução). O usuário baixa e usa no PC. O repositório traz tudo o que é preciso para o processamento.
- **P1.** Seguir o uso local acima.
- **P2.** Repositório público. Os desenhos de referência entram só se forem necessários para rodar o app; não são, e ficam fora.
- **P3.** Verificar a fórmula da altura útil, porque os studs e a cobrinha vão até o cobrimento. Feito na seção 6.1.
- **P4.** O pino e a cobrinha vão de cobrimento a cobrimento (h − c_sup − c_inf); o pino é arredondado.
- **P5.** A cobrinha continua sobre o pilar, como no modelo.
- **P6.** Cobrinhas paralelas ao lado menor, com opção de mudar a direção.
- **P7.** Montagem positiva nos conectores opcional e desligada: pela nota, a prioridade é usar as armaduras negativa e positiva existentes.
- **P8.** Pinos por pente e distância ao canto viram parâmetros.
- **P9.** Pentes inclinados automáticos, com opção de cruz.
- **P10.** Trilhos desenhados com a largura real.
- **P11.** Aço dos pentes só no quadro.
- **P12.** Montagem da cobrinha 60 cm além da última linha.
- **P13.** Um DWG por pilar.
- **P14.** Ordem: cobrinha, depois conectores.

### Respostas às perguntas da E0 (03/11/2026)

- **Q1.** Sim: o modelo R01 usou cobrimento de 2,0 cm. O teste da E1 reproduz o C=450 com c = 2,0.
- **Q2.** A cobrinha em planta é desenhada com a bitola real.
- **Q3.** A cabeça do pino fica com 1,0 cm (0,8 + 0,2, como no modelo) até a Trejor informar.
- **Q4.** As cotas usam a configuração do modelo de conectores (texto no 221; linhas e símbolo no 253). Os níveis dos modelos não mudam, como já combinado.

### Perguntas da E1

- **Q5. Espaços por cima do pilar.** Superada pela decisão do usuário de 03/11/2026: nada passa mais por cima do pilar. A regra (sobra no meio) ficou só para as linhas diante das faces e as pernas ao lado delas, e o espaço maior passa pelo aviso de 2d.
- **Q6. Linhas ao lado do pilar.** Resposta do usuário (03/11/2026): linha inteira, com número ímpar de espaços ao lado da face (no P2, 5 de cerca de 14,4 em vez de 17, 19, 19, 17). A outra opção era cortar a linha em três peças.

### Perguntas da E3

- **Q7. Montagem positiva nos conectores (P7).** O parâmetro está pronto, mas falta a geometria. Proposta: uma barra reta por linha de pinos em cada face, paralela a ela, apoiada nos trilhos (face inferior), dos pentes de um canto aos do outro, mais `mont_ext` além. Nos cantos, as barras de faces vizinhas se cruzam em camadas diferentes. Outra opção: só uma barra, na linha dos pinos de fora. Qual vale, ou fica sem montagem?
- **Q8. Leque dos cantos.** Com mais de um inclinado por canto, os ângulos ficam repartidos por igual entre as direções das duas faces (k = 3: 22,5°, 45° e 67,5° a partir da face). A outra opção reparte o ângulo contando também o afastamento dos pentes das faces a 5 cm do canto, o que deixa os espaços um pouco mais iguais. A regra atual serve?

### Perguntas da E0 (texto original)

- **Q1. Cobrimento da cobrinha no modelo R01.** Lá, as faces da cobrinha ficam a 2,0 cm das faces da laje: altura externa 23 e pernas de 22 pelo eixo, o que dá C=450. Com c = 2,5, as pernas ficam com 21 pelo eixo e C=439. O R01 usou cobrimento de 2,0? (O teste da E1 reproduz o modelo com c = 2,0.)
- **Q2. Largura da cobrinha em planta.** O bloco `COBRINHA 12` desenha a cobrinha com 1,6 cm de largura (barra de 16 mm), mas ela é ø10. Desenhar com a bitola real, como os trilhos (P10)?
- **Q3. Cabeça do pino.** A espessura, que entra em d, fica em 1,0 cm (0,8 + 0,2, como no modelo) até a Trejor informar?
- **Q4. Níveis das cotas.**
  - No modelo de conectores, as 44 cotas têm o texto no 221 e as linhas e o símbolo no 253.
  - No de cobrinha está misturado: 26 assim, 25 inteiras no 221 e o resto no 253 ou no 224.
  - Usar nos dois a configuração dos conectores?
