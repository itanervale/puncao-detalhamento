# Detalhamento de armadura de punção: regras do repositório

App só de detalhamento (sem cálculo) da armadura de punção de pilares, em DWG-TQS: cobrinha em malha ortogonal e conectores Trejor em arranjo radial. Feito em parceria. Responda em português.

- **Plano e decisões:** `PLANO_Detalhamento_Puncao.md`, com etapas, respostas do usuário e perguntas abertas.
- **Padrão gráfico:** `PADRAO_desenho.md`, com o mapa elemento → nível e as medidas dos modelos.

## Regras
- **Independência:** este repositório não importa nada de fora da própria pasta. Se for aproveitar código de outro app, copie e anote a origem no comentário.
- **Camadas dos modelos intocadas:**
  - cada elemento vai para o nível, a cor e o estilo que tem nos desenhos de referência (`PADRAO_desenho.md`);
  - não use convenções de outros apps;
  - não altere a tabela de plotagem do TQS.
- **Desenhos de referência:** ficam em `DesenhosReferencia\`, fora do repositório (`.gitignore`). Leia sempre por cópia (`ferramentas\ler_modelo.py`). Os testes que dependem deles são pulados quando a pasta não existe.
- **Segurança:**
  - nunca grave em `C:\TQS` nem em `C:\TQSW`;
  - os resultados vão para `saidas\`;
  - antes de regravar um DWG que o usuário possa ter editado, copie o anterior para `saidas\anteriores\`.
- **Commits:** um por etapa aprovada, com a mensagem dizendo a etapa.

## Lições do TQS (interface Python 2.1.7)
- **Fontes:**
  - os textos são gravados em latin-1: caractere fora dele derruba a gravação;
  - as fontes não têm "³", "≥", "ª", "º", "×", "ø": use "m3", ">=", "a", "o", "x" e "{" (símbolo de bitola);
  - o "°" sai.
- **PDF:**
  - `file.SaveAs("X.PDF")` só gera conteúdo com o diretório atual na pasta do desenho;
  - grava `X-R00.PDF`; nome com mais de 23 caracteres recebe a revisão no meio: ache o PDF novo pela listagem e renomeie;
  - o estilo "do nível" (`style = -1`) sai contínuo: para tracejar, grave o estilo na entidade.
- **Nomes:** DWG sem ponto no nome; com ponto, a plotagem falha.
- **DXF:**
  - o `SaveAs(".DXF")` grava duas entradas CONTINUOUS na tabela LTYPE, e os leitores desenham tudo tracejado: tire a repetida;
  - as cores do DXF são as de tela; para as da plotagem, troque pela pena do nível.
- **Ferro genérico (`ICPFGN`):**
  - pontos pelo eixo, relativos ao ponto de inserção;
  - o TQS cota as faces externas;
  - desligue `bendDimRadius`, `bendDimPerimeter` e `bendTickDisplay` para tirar as marcas de dobra.
- **Leitura dos ferros:** depois de criar, leia `RebarScheduleInfo` para usar os comprimentos do TQS.
- **Nível do objeto do ferro:** o objeto do ferro inteligente fica no nível atual do desenho, e o editor desenha o ferro na cor desse nível. Fixe `dwg.draw.level = 220` (`NV_OBJETO_FERRO`) antes de cada `SmartRebar`; sem isso, os ferros da réplica saíram verdes e vermelhos.
- **Cobrinha (C pela soma dos trechos pelo eixo, como no modelo):** `bendTotalLengthMode` = 2, `bendBendLengthMode` = 2 e `bendRadiusDisplay` = 0.
- **Texto do ferro reposicionado:** `RebarTextDisplayPosition(x, y, altura em cm plotados, ângulo, 0, ICPCENTR_ESQUERD, ICPQUEBR_SEMQUEBRA)`.
- **Cotas dos modelos:** `dimblk` "DOT" e `dimtsz` 0,2114; os demais valores em `dwg_tqs\arquivo.py` (`COTA`).
- **Bloco da biblioteca do TQS:** `BlockLoadFromDwg` com o caminho sem extensão dá ao bloco esse caminho como nome, igual ao do modelo.
- **`DimNote`:** grava uma polilinha comum e, depois dele, o iterador em memória derruba o Python. Desenhe as chamadas como polilinha.
- **Teste de regressão:** `python -m unittest testes.teste_e0_replica -v` refaz os dois modelos e compara entidade a entidade (`PADRAO_desenho.md`, seção 10).
- **Cotas:**
  - `dim.dimtxu` vale só para a próxima cota;
  - sem ele, o TQS escreve a medida;
  - num DWG novo, defina `idmniv`, `idmnic`, `idmnil` e `idmnib`, senão chamadas e ticks saem no 216.
- **Iterador:** pula os níveis desligados (`dwg.settings.levelsReadMode = 0` para ler todos) e entrega o conteúdo dos blocos em coordenadas globais.
- **Console:** use `PYTHONIOENCODING=utf-8`; as listagens do TQS estão em cp1252.
