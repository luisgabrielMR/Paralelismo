# Busca de Nomes em Arquivos `.txt`

Projeto em **Java puro** com apoio de **Python** para comparar estrategias sequenciais e paralelas de busca de nomes em arquivos `.txt`.

O Java executa a busca e mede o tempo oficial. O Python automatiza as repeticoes, coleta os JSONs retornados pelo Java, gera CSVs e cria um relatorio HTML com tabelas e graficos SVG.

## Estrutura do projeto

```text
PARALELISMO/
├── src/
│   ├── Main.java
│   ├── SearchStrategy.java
│   ├── SearchResult.java
│   ├── DatasetUtils.java
│   ├── SequentialSearch.java
│   ├── SingleThreadSearch.java
│   ├── OneThreadPerFileSearch.java
│   ├── MultiThreadPerFileSearch.java
│   ├── BenchmarkFormatter.java
│   ├── BenchmarkMetrics.java
│   ├── BenchmarkRunResult.java
│   └── CliArguments.java
├── scripts/
│   ├── benchmark.py
│   └── generate_report.py
├── dataset_p/
├── dataset_g/
├── out/
├── results/
├── README.md
├── .gitignore
└── LICENSE
```

As classes Java continuam no **default package** para simplificar a compilacao.

## Regras da busca

Cada arquivo `.txt` possui um nome completo por linha. A busca compara a linha inteira com o nome pesquisado:

```java
line.trim().equalsIgnoreCase(targetName.trim())
```

O projeto nao usa `contains`, porque a busca nao deve encontrar apenas parte do nome.

## Estrategias

| Estrategia | Argumento | Classe |
| --- | --- | --- |
| Sequencial pura | `sequencial` | `SequentialSearch.java` |
| Sequencial dentro de uma Thread | `singleThread` | `SingleThreadSearch.java` |
| Uma Thread por arquivo | `oneThreadPerFile` | `OneThreadPerFileSearch.java` |
| N Threads por arquivo | `multiThreadPerFile` | `MultiThreadPerFileSearch.java` |

## Como compilar manualmente

Na raiz do projeto:

```bash
javac -d out src/*.java
```

No PowerShell, se o `*.java` nao for expandido pelo ambiente, use:

```powershell
javac -d out (Get-ChildItem src -Filter *.java)
```

O `benchmark.py` tambem compila automaticamente antes de executar os testes quando `COMPILE_BEFORE_RUN = True`.

## Como executar o modo interativo

Depois de compilar:

```bash
java -cp out Main
```

O modo interativo permite escolher o dataset, escolher a estrategia, digitar o nome e visualizar uma saida humana:

```text
=== Resultado da Busca ===
Dataset: Pequeno
Estrategia: Sequencial
Nome pesquisado: Ana Silva
Encontrado: Sim
Arquivo: nomes_01.txt
Linha: 348
Conteudo da linha: Ana Silva
Tempo de execucao: 12.45 ms
```

## Como executar o modo benchmark manual

O modo benchmark do Java nao usa entrada interativa e imprime apenas JSON no stdout.

```bash
java -cp out Main --benchmark --dataset pequeno --strategy sequencial --name "Ana Silva" --format json
```

```bash
java -cp out Main --benchmark --dataset grande --strategy multiThreadPerFile --name "Ana Silva" --threads-per-file 4 --format json
```

Para executar manualmente com um dataset personalizado gerado na raiz do projeto:

```bash
java -cp out Main --benchmark --dataset custom --dataset-path "dataset_xg" --strategy sequencial --name "Ana Silva" --format json
```

Argumentos aceitos:

| Argumento | Obrigatorio | Valores |
| --- | --- | --- |
| `--benchmark` | Sim | indica modo automatico |
| `--dataset` | Sim | `pequeno`, `grande`, `custom` |
| `--dataset-path` | Apenas para `--dataset custom` | caminho para uma pasta de dataset personalizada |
| `--strategy` | Sim | `sequencial`, `singleThread`, `oneThreadPerFile`, `multiThreadPerFile` |
| `--name` | Sim | nome completo pesquisado |
| `--threads-per-file` | Apenas para `multiThreadPerFile` | inteiro maior que zero |
| `--format` | Nao | `json`, `csv`; padrao: `json` |

O tempo medido pelo Java considera apenas:

```java
long start = System.nanoTime();
SearchResult result = strategy.search(datasetPath, targetName);
long end = System.nanoTime();
```

Ou seja, nao inclui menus, parse de argumentos, validacao, criacao da estrategia nem impressao do resultado.

## Benchmark automatico com Python

Execute:

```bash
python scripts/benchmark.py
```

O script:

- pede para escolher o dataset, incluindo pastas personalizadas `dataset_*` encontradas na raiz do projeto;
- sorteia 5 nomes diferentes existentes nos arquivos `.txt`;
- executa 5 repeticoes por nome;
- testa 6 configuracoes:
  - `sequencial`;
  - `singleThread`;
  - `oneThreadPerFile`;
  - `multiThreadPerFile N=2`;
  - `multiThreadPerFile N=4`;
  - `multiThreadPerFile N=8`;
- coleta o JSON retornado pelo Java;
- salva dados brutos e medias em CSV/JSON;
- calcula Speedup usando a media da estrategia sequencial como base;
- gera `relatorio.html` automaticamente.

O experimento padrao possui:

```text
5 nomes x 5 repeticoes x 6 configuracoes = 150 execucoes
```

O tempo oficial vem dos campos `wallTimeMs` e `wallTimeNs` retornados pelo Java. O Python nao mede o tempo da busca.

Além das opções fixas:

```text
1 - Dataset pequeno (dataset_p)
2 - Dataset grande (dataset_g)
```

o `benchmark.py` lista automaticamente outras pastas cujo nome começa com `dataset_`, como `dataset_xg`, `dataset_20x50k` ou `dataset_teste`. As pastas `dataset_p` e `dataset_g` aparecem somente nas opções fixas.

## Saida do benchmark

Cada execucao cria uma pasta em `results/`:

```text
results/
└── DATA_HORA_MAQUINA/
    ├── relatorio.html
    └── data/
        ├── resultados_brutos.json
        ├── resultados_brutos.csv
        ├── medias_por_nome.csv
        ├── medias_gerais.csv
        ├── speedup.csv
        └── resumo_benchmark.json
```

Arquivos gerados:

| Arquivo | Conteudo |
| --- | --- |
| `resultados_brutos.json` | Metadados, nomes sorteados e todas as execucoes com o JSON completo retornado pelo Java. |
| `resultados_brutos.csv` | Uma linha por execucao, pronta para Excel/LibreOffice. |
| `medias_por_nome.csv` | Media, menor e maior tempo agrupados por nome e estrategia. |
| `medias_gerais.csv` | Media, menor e maior tempo agrupados por estrategia. |
| `speedup.csv` | Speedup por estrategia/configuracao. |
| `resumo_benchmark.json` | Resumo geral da tentativa. |
| `relatorio.html` | Relatorio visual com cards, tabelas, graficos SVG e conclusao automatica. |

## Como abrir o relatorio

Abra diretamente no navegador:

```text
results/DATA_HORA_MAQUINA/relatorio.html
```

Nao e necessario servidor web.

Tambem e possivel gerar o relatorio manualmente a partir de uma pasta de resultados existente:

```bash
python scripts/generate_report.py results/DATA_HORA_MAQUINA
```

O script procura os dados em:

```text
results/DATA_HORA_MAQUINA/data/
```

E escreve:

```text
results/DATA_HORA_MAQUINA/relatorio.html
```

## Relatorio consolidado do grupo

Cada integrante deve rodar o benchmark na propria maquina:

```bash
python scripts/benchmark.py
```

Isso gera uma pasta individual dentro de `results/`. Para montar o relatorio consolidado, junte as pastas geradas pelos integrantes dentro de `results/` e execute:

```bash
python scripts/compare_results.py
```

Opcionalmente, informe outro diretorio de resultados:

```bash
python scripts/compare_results.py --results-dir results
```

O script procura automaticamente pastas que tenham:

```text
data/resultados_brutos.csv
data/medias_gerais.csv
data/speedup.csv
data/resumo_benchmark.json
```

Pastas incompletas sao ignoradas com aviso. Relatorios consolidados antigos `group_report_*` tambem sao ignorados para nao entrar na comparacao.

A saida gerada fica em:

```text
results/
└── group_report_DATA_HORA/
    ├── group_report.html
    └── data/
        ├── resultados_consolidados.csv
        ├── medias_por_maquina.csv
        ├── medias_gerais_grupo.csv
        ├── speedup_por_maquina.csv
        ├── speedup_geral_grupo.csv
        └── resumo_grupo.json
```

O HTML consolidado tem duas partes:

1. Analise Principal da Atividade:
   - usa apenas os datasets `pequeno` e `grande`;
   - mostra tempo medio, menor tempo e maior tempo;
   - calcula Speedup;
   - compara as maquinas;
   - responde diretamente ao que foi pedido na atividade.

2. Analises Complementares:
   - usa datasets maiores, como `dataset_xg` ou `dataset_100x200k`;
   - mostra CPU, quando disponivel;
   - mostra memoria heap, quando disponivel;
   - compara o impacto de `multiThreadPerFile` com N=2, N=4 e N=8;
   - aprofunda a analise de overhead e paralelismo.

Como `results/` e ignorado pelo Git, as pastas de resultado devem ser compartilhadas manualmente entre os integrantes antes de rodar o comparador.

## Geração de datasets sintéticos

O script `scripts/generate_dataset.py` gera datasets `.txt` maiores para testar melhor as estrategias sequenciais e paralelas.

Datasets maiores sao uteis porque, em bases pequenas, a estrategia sequencial pode vencer com frequencia: o custo de criar, agendar e coordenar Threads pode ser maior do que o custo real da busca. Com mais arquivos e mais nomes por arquivo, fica mais facil observar quando as estrategias paralelas passam a compensar.

Cada arquivo gerado contem exatamente um nome completo por linha. Todos os nomes completos sao unicos no dataset inteiro. O mesmo primeiro nome ou sobrenome pode aparecer em varias linhas, e sobrenomes podem se repetir dentro do mesmo nome completo; o que nao se repete e a linha completa.

Exemplo:

```bash
python scripts/generate_dataset.py --output dataset_xg --files 10 --names-per-file 100000 --seed 42
```

Isso gera:

```text
dataset_xg/
├── arq_1.txt
├── arq_2.txt
├── ...
├── arq_10.txt
└── manifest.json
```

Argumentos:

| Argumento | Descricao |
| --- | --- |
| `--output` | Pasta de saida do dataset. |
| `--files` | Quantidade de arquivos `.txt`. |
| `--names-per-file` | Quantidade de nomes por arquivo. |
| `--seed` | Seed opcional para embaralhamento reprodutivel. |
| `--force` | Apaga e recria a pasta de saida se ela ja existir. |
| `--no-shuffle` | Gera os nomes em ordem deterministica, sem embaralhar. |

Exemplos:

```bash
python scripts/generate_dataset.py --output dataset_xg --files 10 --names-per-file 100000 --seed 42
```

```bash
python scripts/generate_dataset.py --output dataset_20x50k --files 20 --names-per-file 50000 --seed 123 --force
```

```bash
python scripts/generate_dataset.py --output dataset_ordem --files 10 --names-per-file 100000 --no-shuffle --force
```

O script escolhe automaticamente o formato necessario conforme o total solicitado:

| Formato | Exemplo | Limite usado pelo script |
| --- | --- | --- |
| Nome + Sobrenome | `Ana Silva` | ate 10.000 nomes |
| Nome + Sobrenome + Sobrenome | `Ana Silva Santos` | ate 1.000.000 nomes |
| Nome + Nome + Sobrenome + Sobrenome | `Ana Clara Silva Santos` | ate 100.000.000 nomes |
| Nome + Nome + Sobrenome + Sobrenome + Sobrenome | `Ana Clara Silva Santos Costa` | ate 10.000.000.000 nomes |

O `manifest.json` registra a configuracao usada, quantidade de arquivos, total de nomes, formato escolhido, capacidade, seed, se houve shuffle, data/hora, versao do Python, sistema operacional e nome da maquina.

O gerador usa indices combinatorios para garantir unicidade sem precisar manter todos os nomes completos em memoria.

Depois de gerar um dataset com nome iniciado por `dataset_`, ele aparece automaticamente no menu do benchmark:

```bash
python scripts/benchmark.py
```

Exemplo de menu:

```text
Escolha o dataset:
1 - Dataset pequeno (dataset_p)
2 - Dataset grande (dataset_g)
3 - dataset_xg
4 - dataset_20x50k
```

Ao escolher uma pasta personalizada, o Python chama o Java com `--dataset custom --dataset-path caminho_do_dataset`.

## Metricas coletadas

O Java retorna metricas principais e complementares:

- `wallTimeNs`;
- `wallTimeMs`;
- `processCpuTimeMs`, quando suportado;
- `cpuUsageApproxPercent`, quando suportado;
- `heapUsedBeforeBytes`;
- `heapUsedAfterBytes`;
- `heapDeltaBytes`;
- `availableProcessors`;
- `javaVersion`;
- `osName`;
- `osArch`;
- `machineName`.

Metricas nulas sao ignoradas nos calculos de media correspondentes.

## Observacao sobre Git

As pastas `out/` e `results/` sao ignoradas pelo Git porque contem arquivos gerados localmente:

- `out/`: classes `.class` compiladas;
- `results/`: dados e relatorios de benchmark de cada maquina.

Neste repositório, `dataset_p/`, `dataset_g/` e datasets personalizados `dataset_*/` permanecem como dados locais ignorados pelo Git. Os fontes em `src/` e os scripts em `scripts/` nao sao ignorados.

## Teste rapido

1. Compilar:

```bash
javac -d out src/*.java
```

2. Rodar interativo:

```bash
java -cp out Main
```

3. Rodar benchmark automatico:

```bash
python scripts/benchmark.py
```

4. Abrir relatorio:

```text
results/PASTA_DA_EXECUCAO/relatorio.html
```
