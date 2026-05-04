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

Argumentos aceitos:

| Argumento | Obrigatorio | Valores |
| --- | --- | --- |
| `--benchmark` | Sim | indica modo automatico |
| `--dataset` | Sim | `pequeno`, `grande` |
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

- pede para escolher apenas o dataset;
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

Neste repositório, `dataset_p/` e `dataset_g/` permanecem como datasets locais ignorados pelo Git, seguindo a configuracao que ja existia no projeto. Os fontes em `src/` e os scripts em `scripts/` nao sao ignorados.

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
