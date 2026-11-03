# Padrão do desenho (inventário dos modelos)

Levantado em 03/11/2026 dos dois desenhos de referência, lidos em cópia pelo `ferramentas\ler_modelo.py`. **Os níveis, as cores e os estilos daqui são os que o app usa, sem alteração** (desenho feito em parceria).

| Modelo | Solução | Pilar | Origem usada abaixo |
|---|---|---|---|
| `PUN_P02.DWG` | conectores (studs) | P02, 50 × 150 (b na horizontal) | canto inferior esquerdo do pilar na planta dos pinos, que no desenho já é (0, 0) |
| `PUN_P02-R01.DWG` | cobrinha | P2, 150 × 50 | canto inferior esquerdo do pilar na planta da punção, em (−1034,57; 85,02) no desenho |

## 1. Geral

- **Tipo do desenho:** sistema 9, subsistema 13 ("TQS AGC2 - Desenho de armação"), com a tabela de plotagem `TABPLTA`; `rebarDrawing` = 2.
- **Escala:** 15 (1:15). As coordenadas estão em cm reais; altura de texto no papel = altura no desenho ÷ 15.
- **Tabela de níveis:** a de um DWG 9/13 novo é igual, nível a nível, à dos dois modelos (cor e estilo de tela; conferido em 03/11/2026 em `nucleo\niveis.json`). Basta criar o desenho como 9/13.
- **Laje e espessura:** laje de 27 cm nos dois.
- **Cobrimentos:** 2,5 cm no modelo de conectores. No de cobrinha, as faces da cobrinha ficam a 2,0 cm das faces da laje (pergunta Q1 do plano).

## 2. Alturas de texto

| Texto | Nível | No desenho | No papel (cm) |
|---|---|---|---|
| Título do pilar ("P02") | 222 | 7,50 | 0,50 |
| Repetição ("1X") | 202 | 6,75 | 0,45 |
| Dimensões ("(50x150)") | 220 | 6,75 | 0,45 |
| Título de vista | 226 | 5,25 | 0,35 |
| "ESCALA 1:15" | 0 | 3,30 | 0,22 |
| Letra de corte ("A") | 226 (conectores) / 253 (cobrinha) | 4,50 | 0,30 |
| "ARMADURA DA FACE INFERIOR" | 226 | 3,75 | 0,25 |
| "(barras contra colapso progressivo)" | 0 | 3,75 | 0,25 |
| "NOTAS IMPORTANTES" | 220 | 5,55 | 0,37 |
| Corpo das notas | 227 | 3,75 | 0,25 |
| "NOTA n:" (sobre o corpo, que começa com 8 espaços) | 242 | 3,75 | 0,25 |
| Quadro "ARMADURA DE COMBATE À PUNÇÃO" (título 220, linhas 242) | 220 / 242 | 4,80 | 0,32 |
| Texto das cotas | 221 | 2,70 | 0,18 |
| Texto dos ferros inteligentes | 1 | 3,00 | 0,20 |
| Chamadas "NOTA 1", "NOTA 2"... e "TOPO LAJE" | 221 / 253 | 3,75 | 0,25 |
| "DET. PLANTA" / "GABARITO PENTES MESTRES" | 220 | 5,25 / 3,00 | 0,35 / 0,20 |

## 3. Níveis por elemento

### 3.1 Conectores (`PUN_P02`)

| Vista | Elemento | Nível (estilo) |
|---|---|---|
| Folha | moldura (−106 a 434 × −225,5 a 320) | 0 |
| Título | "P02" / "1X" / "(50x150)" | 222 / 202 / 220 |
| Quadro | moldura do quadro / linhas internas | 240 (hachura de 25 %) / 0 |
| Planta dos pinos | contorno do pilar | 203 (tracejado) e 240 (hachura de 25 %) |
| | eixos do pilar | 204 (traço-ponto) |
| | pente (bloco `PUN 3P 17 cm`, inserido no 0) | cabeças 241, fustes 245, trilhos e ganchos 0 |
| | contornos dos pinos (retângulos de cantos arredondados) | 200 (pontilhado) |
| | cotas | objeto IPOCOT 221 (seção 5) |
| | ferro N1 (linha de identificação) | 246 |
| | corte A-A (bloco `$CORTEA` do TQS, escala 13,98) | 226; o bloco tem um polígono no 79 |
| Colapso | contorno do pilar | 203 e 240 |
| | barras desenhadas | 245 |
| | ferro N2 (linha de identificação) | 246 |
| Corte A-A | laje e pilar em corte (contorno com quebras) | 0 e 240 (hachura de 25 %) |
| | pinos (bloco `Pino 22 cm em corte`, inserido no 0) | 241 |
| | barras de flexão: longitudinais / em corte | 0 (linha dupla) / 0 (círculo ø10) |
| | barras de colapso em corte (N2) | 245 |
| | trilhos ø8 entre os pinos | 245 |
| | eixos | 204, 205 |
| | "TOPO LAJE" | 253 |
| | chamadas "NOTA 1", "NOTA 2", "NOTA 3" | 221 |
| Notas | moldura do título / linhas / corpo / "NOTA n:" | 240 / 0 e 227 / 227 / 242 |

### 3.2 Cobrinha (`PUN_P02-R01`)

| Vista | Elemento | Nível (estilo) |
|---|---|---|
| Folha | moldura | 0 |
| Título | "P2" | 222 |
| Seção A-A (girada 90°) | laje e pilar em corte | 0 e 240 |
| | cobrinha (contorno fechado da barra) | 224 (hachura cheia) e 233 |
| | eixo da cobrinha | 0 (traço-ponto) |
| | barras de flexão: em corte / longitudinais | 254 e 243 (N2) / 245 e 0 |
| | chamadas da NOTA 1 até os vértices | 210 (pontilhado) |
| | caixa da "NOTA 1" | 225 |
| | letras A / "TOPO LAJE" | 253 / 221 |
| Cobrinha pelas faces (N1) | linha de identificação do ferro genérico | 242 |
| | cotas | IPOCOT 221 |
| Cobrinha pelos eixos | cobrinha / eixo | 224 e 233 / 0 |
| | barras nos vértices | 254, 243, 245 |
| | cotas | IPOCOT 221 |
| Planta da punção | cobrinhas (bloco `COBRINHA 12`, inserido no 241) | linhas 241 (contínuas embaixo, tracejadas em cima), círculos 241 e 233 |
| | contorno do pilar | 227 |
| | montagem N2 desenhada / identificação | 243 / 244 |
| | eixos | 204 |
| | "PENTE MESTRE P/ LOCAÇÃO" | 253 |
| | cotas | IPOCOT 221 e 253 |
| Colapso | contorno do pilar | 203 e 240 |
| | barras | 245 |
| | N3 e N4 (identificação) | 246 |
| Gabarito | pilar / retângulo dos pentes mestres | 203 e 240 / 233 |
| | cotas | IPOCOT 253 (150 e 50) e 224 (11) |
| Notas | como nos conectores | 240, 0, 227, 242, 220 |

## 4. Blocos

- **`PUN 3P 17 cm` (planta, um por pente):** 3 pinos a 0, 17 e 34 cm do ponto de inserção, que é o 1º pino, a s0 da face; a direção do bloco aponta para fora do pilar. Cada pino tem:
  - cabeça: círculo no 241, r = 1,625;
  - fuste: círculo no 245, r = 0,4 (**errado: ø10 = r 0,5**).

  Os 2 trilhos (linhas e arcos no 0) correm dos dois lados dos pinos:
  - largura de 0,5 (**errado: ø8 = 0,8**), com o eixo a 1,87 do eixo dos pinos;
  - gancho com raio de 3,0 pelo eixo numa ponta, um trilho para cada lado.

  Nome a gerar: `PUN {n}P {sr} cm`.
- **`Pino 22 cm em corte` (corte, nível 241):** polilinha fechada do pino com 22 de altura.
  - Cabeças de 3,25 de largura (32,5 mm) e 0,8 de altura.
  - Concordância até o fuste, de 0,8 de largura (**errado: 1,0**), 0,2 abaixo da cabeça.

  Nome a gerar: `Pino {L} cm em corte`.
- **`COBRINHA 12` (planta, nível 241, uma inserção por cobrinha):** a cobrinha vista de cima.
  - Linha dupla de 1,6 de largura: contínua (estilo 0) nos trechos de baixo e tracejada (estilo 1) nos de cima.
  - Círculos de r = 0,8 nos níveis 241 e 233 em cada perna.
  - A largura é a de uma barra de 16 mm (pergunta Q2).
- **`C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA`:** letra de corte do TQS, inserida no 226 com escala ±13,98 (espelhada do outro lado).

## 5. Cotas (objetos IPOCOT)

Configuração lida dos objetos:
- **texto:** nível 221, altura 2,70 (0,18 cm), 0,81 acima da linha de cota;
- **linha de cota, chamadas e símbolo:** nível 253;
- **símbolo:** dois círculos concêntricos de r = 0,528 e 0,264 (0,035 e 0,018 cm no papel);
- **chamadas:** começam a 1,5 do ponto cotado (0,10 cm) e passam 1,5 da linha de cota (0,10 cm);
- **linha de cota:** passa 2,25 do símbolo (0,15 cm).

Como os modelos usam essa configuração:
- **Conectores:** todas as 44 cotas seguem a configuração acima.
- **Cobrinha:** está misturado.
  - 26 cotas seguem a configuração acima;
  - 25 estão inteiras no 221 (texto, linhas e símbolo), entre elas as da planta da punção e a de 122 da montagem;
  - as 4 cotas de "11" do gabarito têm o texto no 224 e o resto no 253;
  - há outras 7 cotas avulsas: 3 sem texto (só linhas, no 221) e 4 no 253.

Proposta: usar a configuração dos conectores (texto no 221, resto no 253) em tudo, porque o desenho do R01 parece ter sido editado à mão (pergunta Q4).

## 6. Ferros inteligentes

Todos têm a linha de identificação fora da vista, com o texto padrão do TQS (nível 1, altura 0,20 cm, sem linha de chamada). As barras dentro das vistas são linhas comuns.

| Modelo | Posição | Tipo | Qtde. | ø | C | Inserção (relativa à origem) | Nível | Patas |
|---|---|---|---|---|---|---|---|---|
| Conectores | N1 colapso | reto | 8 | 10 | 220 | (−85; 250), 0° | 246 | 1 |
| Conectores | N2 colapso | reto | 3 | 10 | 320 | (149; −85), 90° | 246 | 1 |
| Cobrinha | N1 cobrinha | genérico | 17 | 10 | 450 | (−206,66; −129,00), 0° | 242 | 0 |
| Cobrinha | N2 montagem | reto | 11 | 12,5 | 395 | (−123,00; −128,22), 0° | 244 | 1 |
| Cobrinha | N3 colapso | reto | 3 | 10 | 320 | (303,55; −128,22), 0° | 246 | 1 |
| Cobrinha | N4 colapso | reto | 8 | 10 | 220 | (642,40; −85,00), 90° | 246 | 1 |

Atributos comuns:
- `ident` = 1, `idobra` = 1, sem ganchos, `bendTickDisplay` = 0, `leaderLine` = 0, `textHeigth` = 0,2, `straightBarTextPosition` = 2.
- **Conectores:** `straightBarZone` = 1 (negativa), `bendDimRadius` = 0 e `cover` de 2,5 e 7.
- **Cobrinha:** `straightBarZone` = 0, `bendDimRadius` = 1 e `cover` = 3.

**Cobrinha N1 (ferro genérico):** 24 pontos pelo eixo, relativos à inserção.
- Começa em (−22; 50); segue (−22; 67), (0; 67), (0; 84), (−22; 84)... e termina em (0; 258). O x é a altura e o y corre ao longo da cobrinha.
- C=450 = 208 + 11 × 22.
- A tabela do TQS dá 23,0 de desconto de raios (450 − 23 = 427 no peso).

## 7. Leiaute (coordenadas relativas à origem)

**Conectores:**

| Elemento | Posição |
|---|---|
| Título "P02" | (−98; 305) |
| "1X" | (−98; 294) |
| "(50x150)" | (−98; 282) |
| Título da planta dos pinos / escala | (−98; 268) / (−98; 262) |
| Planta do colapso | pilar em x = 269 a 319 (269 à direita do pilar principal); título em (149; 268) |
| Corte A-A | título em (−85; −83); laje entre y = −130 e −157; os pinos alinhados em x com a planta |
| Quadro | moldura de x = 279 a 434 e y = 281 a 320; textos em x = 283, y = 312,6 / 301,6 / 293,4 / 285,3 |
| Notas | título em (241; −154,8); linhas a cada 7,5 a partir de y = −163,8; moldura do título de x = 238 a 434 |

**Cobrinha:**

| Elemento | Posição |
|---|---|
| Título "P2" | (−361,7; 304,4) |
| Seção A-A (laje vertical) | x = −354 a −246 |
| Cobrinha pelas faces | x ≈ −229 a −202 |
| Cobrinha pelos eixos | x ≈ −172 a −149 |
| Planta da punção | título em (−125,1; 182,5); "SEÇÃO A-A" em (−124,5; 157,2) |
| Planta do colapso | pilar em x = 388,6 a 538,6; título em (303,5; 182,5) |
| Notas | título em (275,5; 315,1) |
| Gabarito | x = 522,5 a 674,3 e y = 234,6 a 324 |

## 8. Textos fixos

**Quadro dos conectores:**

```
ARMADURA DE COMBATE À PUNÇÃO
QUANTIDADE: {rep} x {n} PENTES
DESCRIÇÃO: {pinos} { {ø} mm (CA-50)
com {L} mm + {trilhos} { {ø trilho} mm (CA-50)
```

**Notas dos conectores** (corpo no 227; "NOTA n:" no 242):

1. NO MÍNIMO UMA EXTREMIDADE ALARGADA DA ARMADURA DE PUNÇÃO DE CADA PENTE DEVERÁ CONTER UMA BARRA DA ARMADURA DE FLEXÃO DA LAJE.
2. COTAGEM EM RELAÇÃO AO EIXOS DOS PINOS DA ARMADURA DE COMBATE À PUNÇÃO.
3. AS ARMADURAS DE COMBATE À PUNÇÃO DEVERÃO SER LOCADAS COM BASE NAS COTAGENS REPRESENTADAS NESTE DESENHO, ADMITINDO-SE UMA VARIAÇÃO MÁXIMA IGUAL A MEIO DIÂMETRO DO PINO DE PUNÇÃO.

**Notas da cobrinha:**

1. CADA VÉRTICE DA ARM. DE PUNÇÃO DEVERÁ CONTER UMA BARRA SUPERIOR CONFORME ARMADURA NEGATIVA. CASO A ARMADURA NÃO COINCIDA COM O VÉRTICE UTILIZAR BARRAS ADICIONAIS DA MESMA BITOLA DA ARMADURA SUPERIOR (NEGATIVA).
2. LOCAR NA FORMA A POSIÇÃO DO PINO MESTRE DE PUNÇÃO CONFORME SEÇÃO A-A.
3. ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS ENTRE EIXOS DAS BARRAS.
4. ESTA REPRESENTAÇÃO DO FERRO MOSTRA COMPRIMENTOS DE DOBRAS ENTRE FACES DAS BARRAS.

Ajustes de texto (o app reproduz o sentido sem os resíduos):
- no modelo R01, alguns textos das notas trazem quebras de linha soltas;
- "AO EIXOS" está no original e fica como está até o usuário decidir.

## 9. Aparência na plotagem

- **Hachuras da `TABPLTA`:**
  - 240: preenchimento de 25 % (laje e pilar em corte, pilar em planta, cabeçalhos);
  - 224: cheio (a cobrinha em corte sai preta);
  - 225: 20 %.
- **Penas grossas** (pena 1, 0,6 mm): 220, 226, 242, 243 e 245.
- **Penas finas** (0,1 mm): 0, 200, 204, 205, 241, 246, 253 e outros.

O detalhe por nível está em `nucleo\niveis.json`.

## 10. Gravação pela interface (E0, 03/11/2026)

`dwg_tqs\teste_gravacao.py` refez os dois modelos a partir do despejo, sem copiar o arquivo, e comparou entidade a entidade (`testes\teste_e0_replica.py`):

| Modelo | Entidades iguais | Diferenças | Ferros pelo TQS |
|---|---|---|---|
| Conectores | 910 de 911 | o rótulo "N2" que o modelo guarda dentro do ferro N2 (marca da barra no corte) | N1 8 ø10 C=220 e N2 3 ø10 C=320 |
| Cobrinha | 1624 de 1626 | dois textos vazios das notas (resíduo de quebra de linha) | N1 17 ø10 C=450, N2 11 ø12,5 C=395, N3 3 ø10 C=320, N4 8 ø10 C=220 |

Os PDF e DXF das réplicas saíram do TQS normalmente (`saidas\e0\`).

O que a gravação precisa para ficar igual aos modelos:

- **Desenho:** 9/13, escala 15 e `LoadColors()`. A tabela de níveis sai igual à dos modelos.
- **Cotas:** `dimblk` = "DOT", `dimtsz` = 0,2114 (raio do símbolo = 2,497 × `dimtsz` × escala ÷ 15 = 0,528), `dimtxt` = 0,18, `dimexo` = 0,10, `dimexe` = 0,10 e `dimdle` = 0,15.
  - Níveis: `idmniv` 221 (texto) e `idmnic`, `idmnil`, `idmnib` 253.
  - As cotas "39" entre pentes são inclinadas (`DimInclined`, no ângulo da linha de cota), e o texto "39" é fixo (`dimtxu`): a medida é 39,1, que o TQS escreveria "39.1".
- **Cobrinha (ferro genérico):** para C=450 (soma dos trechos pelo eixo), use:
  - `bendTotalLengthMode` = 2;
  - `bendBendLengthMode` = 2;
  - `bendRadiusDisplay` = 0 (raio de dobra manual).

  Com os padrões, o TQS dá 427 ou 473. A tabela traz 23 de desconto de raios.
- **Texto principal dos ferros:** o texto principal da cobrinha ("17 N1 { 10 C=450") é vertical, ao lado do ferro; o autor o reposicionou. Use `RebarTextDisplayPosition` (início do texto, altura em cm plotados, ângulo, alinhamento à esquerda). Os demais ferros também têm o texto posicionado assim.
- **Ferros retos:** atributos lidos dos modelos.
  - `straightBarTextPosition` = 2 (abaixo da linha) e `straightBarTextDirection` = 0.
  - Conectores: `straightBarZone` = 1, `bendDimRadius` = 0.
  - Cobrinha: `straightBarZone` = 0, `bendDimRadius` = 1.
- **Bloco `$CORTEA` do TQS:** carregue com `BlockLoadFromDwg("C:/TQSW/SUPORTE/BLOCOS/GERAIS/$CORTEA")`, o caminho sem extensão. Assim o bloco fica com o nome do modelo; com a extensão, ficaria "$CORTEA". O arquivo é da instalação do TQS e não vai para o repositório.
- **Blocos próprios:** `BlockOpen(nome, 0, 0)`, elementos em coordenadas locais (o 1º pino na origem, direção +x), `BlockClose` e `BlockInsert` com o ângulo.
- **Chamadas com flecha:** no modelo, são objetos de cota sem símbolo; o app as desenha como polilinha comum com a flecha. O `DimNote` da interface:
  - grava uma polilinha comum, com a flecha no 1º ponto;
  - depois dele, o iterador em memória derruba o Python (acesso inválido), embora o arquivo gravado se leia normalmente.

## 11. Correções e pontos em aberto

- **Corrigir** (aprovado em 03/11/2026):
  - fuste do pino ø10 (r 0,5 na planta; 1,0 no corte);
  - cabeça de 32 mm (r 1,6);
  - trilhos com a largura real (ø8 = 0,8).
- **Confirmar** (perguntas do plano):
  - Q1: cobrimento de 2,0 na cobrinha do R01;
  - Q2: largura da cobrinha em planta;
  - Q3: espessura da cabeça do pino;
  - Q4: níveis das cotas na cobrinha.
