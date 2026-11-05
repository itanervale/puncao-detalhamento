# Detalhamento de armadura de punção: regras do repositório

App só de detalhamento (sem cálculo) da armadura de punção de pilares, em DWG-TQS: cobrinha em malha ortogonal e conectores Trejor em arranjo radial. Feito em parceria. Responda em português.

- **Plano e decisões:** `PLANO_Detalhamento_Puncao.md`, com etapas, respostas do usuário e perguntas abertas.
- **Padrão gráfico:** `PADRAO_desenho.md`, com o mapa elemento → nível e as medidas dos modelos.

## Estrutura
- `nucleo\`: Python puro, sem o TQS.
  - Parâmetros e altura útil (`parametros.py`), cobrinha (`cobrinha.py`), conectores (`conectores.py`, com o catálogo da Trejor em `catalogo_trejor.json`), colapso (`colapso.py`) e verificações (`verificacoes.py`).
  - O conjunto (`detalhe.py`, `python -m nucleo.detalhe <projeto.json>`).
  - Folha em primitivas (`folha.py`) e leiaute das pranchas da cobrinha (`prancha_cobrinha.py`) e dos conectores (`prancha_conectores.py`).
- `dwg_tqs\`: gravação pelo TQS.
  - `arquivo.py`: desenho novo e gravação.
  - `gravar.py`: primitivas para o DWG.
  - `prancha.py`: um pilar, com a conferência dos comprimentos.
- `detalhar.py` (raiz): linha de comando, um DWG por pilar.
- `janela\` (E5): `app.py` (a janela), `cena.py` (prévia da folha na área CAD) e os módulos copiados do app de telas (`cad_ribbon`, `cad_vista`, `cad_dialogo`, `cad_icones`, com a origem no cabeçalho). Abertura: `Detalhar Punção.bat` / `janela_puncao.pyw`.
- `ferramentas\`: leitura e comparação de DWG, imagens, esquema da geometria.
- `testes\`: os da E1 e da E3 não precisam do TQS; os da E0 e os DWG da E2 e da E4 são pulados sem ele ou sem os modelos.
- **Unidades e convenções:** comprimentos em cm, bitolas em mm. `bx` é a dimensão do pilar na horizontal da prancha e `by` na vertical; as coordenadas são relativas ao canto inferior esquerdo do pilar.

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
- **Repositório:** <https://github.com/itanervale/puncao-detalhamento> (público, branch `main`).
  - O autor dos commits usa o e-mail "noreply" do GitHub (`269206119+itanervale@users.noreply.github.com`), configurado só neste repositório, para não expor o e-mail pessoal.
  - O envio usa a credencial do Git Credential Manager.

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
- **Tabela de níveis (cores de tela):** os modelos têm uma tabela própria (34 níveis diferentes da padrão).
  - O `File.Open` e o `LoadColors` da interface a trocam pela padrão do sistema (`CarregarCores`).
  - Para ler a tabela verdadeira, use `dwg_tqs.arquivo.abrir_sem_cores`.
  - Para gravar, `aplicar_tabela_niveis` (feito em `novo_desenho` e de novo em `salvar`).
  - Nos métodos de `LevelsTable`, passe o nível como texto (`"221"`): com número, a interface muda o nível atual.
- **Cotas:** guardam as cores calculadas na criação, e o módulo de cotas da interface usa sempre as cores padrão (3 e 7). Nada que testamos mudou isso (`PADRAO_desenho.md`, seção 10).
- **DWG aberto no TQS:** o `SaveAs` falha sem avisar. O `salvar` confere a data do arquivo e grava `<nome>_HHMMSS.DWG`, com aviso.
- **Cobrinha (C pela soma dos trechos pelo eixo, como no modelo):** `bendTotalLengthMode` = 2, `bendBendLengthMode` = 2 e `bendRadiusDisplay` = 0.
  - O TQS arredonda cada trecho ao centímetro: com trechos de 14,5, o C sai 2 cm maior. Mantenha as pernas em centímetros inteiros; o núcleo soma os trechos arredondados.
- **Texto do ferro reposicionado:** `RebarTextDisplayPosition(x, y, altura em cm plotados, ângulo, 0, ICPCENTR_ESQUERD, ICPQUEBR_SEMQUEBRA)`.
- **Cotas dos modelos:** `dimblk` "DOT" e `dimtsz` 0,2114; os demais valores em `dwg_tqs\arquivo.py` (`COTA`).
- **Bloco da biblioteca do TQS:** `BlockLoadFromDwg` com o caminho sem extensão dá ao bloco esse caminho como nome, igual ao do modelo.
- **`DimNote`:** grava uma polilinha comum e, depois dele, o iterador em memória derruba o Python. Desenhe as chamadas como polilinha.
- **Teste de regressão:** `python -m unittest testes.teste_e0_replica -v` refaz os dois modelos e compara entidade a entidade (`PADRAO_desenho.md`, seção 10).
- **Cotas:**
  - `dim.dimtxu` vale só para a próxima cota;
  - sem ele, o TQS escreve a medida;
  - num DWG novo, defina `idmniv`, `idmnic`, `idmnil` e `idmnib`, senão chamadas e ticks saem no 216.
- **Cota alinhada (`DimAligned`):** o texto segue o sentido do 1º ao 2º ponto; com os pontos da direita para a esquerda, ele sai de cabeça para baixo. Ordene os pontos da esquerda para a direita.
- **Arquivos:** leia e grave com `with` ou `pathlib`; os testes rodam limpos com `-W error::ResourceWarning`.

## Lições do Tk (janela)
- **Threads:** a gravação pelo TQS roda numa thread e devolve o resultado por uma fila. As variáveis do Tk (`StringVar.get()`) só podem ser lidas na thread principal: leia tudo antes de abrir a thread.
- **Ícones:** a `PhotoImage` pertence ao interpretador Tk em que foi criada. Com outra raiz no mesmo processo (testes), o cache é refeito (`cad_icones.foto`).
- **Fechar a janela:** cancele os `after()` pendentes direto no Tcl (`after cancel`). O `after_cancel` do Python falha em comandos já apagados, e a janela não fechava.
- **Conferir sem a tela:** `ferramentas/capturar_janela.py` grava a janela em PNG pelo `PrintWindow` (o `ImageGrab` pega a tela bloqueada).
- **Iterador:** pula os níveis desligados (`dwg.settings.levelsReadMode = 0` para ler todos) e entrega o conteúdo dos blocos em coordenadas globais.
- **Console:** use `PYTHONIOENCODING=utf-8`; as listagens do TQS estão em cp1252.
