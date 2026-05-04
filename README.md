# Busca de Nomes em Arquivos `.txt`

Projeto em **Java puro** para comparar estrategias sequenciais e paralelas de busca de nomes em arquivos `.txt`.

O programa funciona em dois modos:

- **modo interativo**, para uso humano pelo terminal;
- **modo benchmark**, para ser chamado automaticamente por scripts, como um futuro `benchmark.py`.

## Datasets

O projeto usa dois datasets:

```text
dataset_p/  -> Dataset pequeno
dataset_g/  -> Dataset grande
```

Cada arquivo `.txt` deve seguir estas regras:

- cada linha possui exatamente um nome completo;
- cada linha representa um nome diferente;
- a busca compara a linha inteira;
- a busca para o quanto antes quando encontra o nome.

A comparacao usada pelas estrategias e equivalente a:

```java
line.trim().equalsIgnoreCase(targetName.trim())
```

O programa nao usa `contains`, porque a busca nao deve encontrar apenas parte do nome.

## Estrategias

As estrategias implementadas sao:

| Estrategia | Argumento | Classe |
| --- | --- | --- |
| Sequencial pura | `sequencial` | `SequentialSearch.java` |
| Sequencial dentro de uma Thread | `singleThread` | `SingleThreadSearch.java` |
| Uma Thread por arquivo | `oneThreadPerFile` | `OneThreadPerFileSearch.java` |
| N Threads por arquivo | `multiThreadPerFile` | `MultiThreadPerFileSearch.java` |

### Sequencial

Percorre os arquivos um por um e le cada arquivo linha por linha. Esta versao nao usa `Thread`, `Runnable`, `ExecutorService`, `Callable` nem `CompletableFuture`.

### Single Thread

Executa a mesma logica sequencial dentro de uma unica `Thread`. Ela serve para comparar a busca sequencial pura com a execucao dentro de uma thread separada.

### Uma Thread por Arquivo

Cria uma tarefa por arquivo `.txt`. Quando uma tarefa encontra o nome, sinaliza parada para as demais.

### N Threads por Arquivo

Divide as linhas de cada arquivo em blocos e cria N tarefas para procurar nesses blocos. O numero real da linha comeca em 1.

## Compilacao

Para compilar gerando `.class` na pasta raiz:

```bash
javac *.java
```

Para compilar na pasta `out`:

```bash
javac -d out *.java
```

## Modo Interativo

Quando o programa e executado sem argumentos, ele abre o menu interativo:

```bash
java Main
```

Se tiver compilado com `javac -d out *.java`:

```bash
java -cp out Main
```

O usuario escolhe:

1. dataset;
2. estrategia;
3. nome completo buscado;
4. quantidade de threads por arquivo, somente na estrategia `multiThreadPerFile`.

Exemplo de saida humana:

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

No modo interativo, o tempo medido nao inclui escolha de dataset, escolha de estrategia, digitacao do nome nem validacao das opcoes. Ele mede apenas a chamada:

```java
long start = System.nanoTime();
SearchResult result = strategy.search(datasetPath, targetName);
long end = System.nanoTime();
```

## Modo Benchmark

Quando o programa recebe argumentos, ele roda em modo benchmark. Esse modo nao usa entrada interativa e imprime no stdout apenas o resultado estruturado.

Mensagens de erro sao enviadas para stderr. Em caso de erro, o codigo de saida e diferente de `0`.

Formato geral:

```bash
java Main --benchmark --dataset pequeno --strategy sequencial --name "Ana Silva" --format json
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

Exemplos JSON:

```bash
java Main --benchmark --dataset pequeno --strategy sequencial --name "Ana Silva" --format json
java Main --benchmark --dataset pequeno --strategy singleThread --name "Ana Silva" --format json
java Main --benchmark --dataset grande --strategy oneThreadPerFile --name "Ana Silva" --format json
java Main --benchmark --dataset grande --strategy multiThreadPerFile --name "Ana Silva" --threads-per-file 4 --format json
```

Exemplo CSV:

```bash
java Main --benchmark --dataset grande --strategy sequencial --name "Ana Silva" --format csv
```

Exemplo de erro esperado:

```bash
java Main --benchmark --dataset grande --strategy multiThreadPerFile --name "Ana Silva"
```

Esse comando falha porque `multiThreadPerFile` exige `--threads-per-file`.

## Saida JSON

No formato JSON, o stdout contem um objeto valido com dados da busca e metricas complementares:

```json
{
  "dataset": "grande",
  "strategy": "oneThreadPerFile",
  "threadsPerFile": 0,
  "targetName": "Ana Silva",
  "found": true,
  "fileName": "nomes_03.txt",
  "lineNumber": 1200,
  "lineContent": "Ana Silva",
  "wallTimeMs": 12.450000,
  "wallTimeNs": 12450000,
  "processCpuTimeSupported": true,
  "processCpuTimeMs": 8.300000,
  "cpuUsageApproxPercent": 22.400000,
  "heapUsedBeforeBytes": 12345678,
  "heapUsedAfterBytes": 13456789,
  "heapDeltaBytes": 111111,
  "availableProcessors": 8,
  "javaVersion": "25.0.3",
  "osName": "Windows 10",
  "osArch": "amd64",
  "machineName": "NOME-DA-MAQUINA"
}
```

Quando o nome nao e encontrado, `found` fica `false` e os campos `fileName`, `lineNumber` e `lineContent` ficam `null`.

## Saida CSV

No formato CSV, o stdout contem uma unica linha, sem cabecalho:

```text
dataset,strategy,threadsPerFile,targetName,found,fileName,lineNumber,wallTimeMs,wallTimeNs,processCpuTimeMs,cpuUsageApproxPercent,heapUsedBeforeBytes,heapUsedAfterBytes,heapDeltaBytes,availableProcessors,javaVersion,osName,osArch,machineName
```

Exemplo:

```text
grande,sequencial,0,Ana Silva,true,nomes_03.txt,1200,12.450000,12450000,8.300000,22.400000,12345678,13456789,111111,8,25.0.3,Windows 10,amd64,NOME-DA-MAQUINA
```

Se o nome nao for encontrado, `fileName` e `lineNumber` ficam vazios.

## Medicao de Tempo

O tempo principal do benchmark e `wallTimeNs`, medido com `System.nanoTime()`.

No modo benchmark, o tempo nao inclui:

- parse dos argumentos;
- validacao dos argumentos;
- criacao da estrategia;
- impressao do resultado.

Ele mede apenas:

```java
long start = System.nanoTime();
SearchResult result = strategy.search(datasetPath, targetName);
long end = System.nanoTime();
```

## Metricas Coletadas

O modo benchmark retorna:

- `wallTimeNs`;
- `wallTimeMs`;
- `heapUsedBeforeBytes`;
- `heapUsedAfterBytes`;
- `heapDeltaBytes`;
- `availableProcessors`;
- `javaVersion`;
- `osName`;
- `osArch`;
- `machineName`;
- `processCpuTimeSupported`;
- `processCpuTimeMs`, quando suportado pela JVM/SO;
- `cpuUsageApproxPercent`, quando o tempo de CPU do processo esta disponivel.

O programa nao chama `System.gc()` antes ou depois da busca.

## Uso Futuro com Python

O modo benchmark foi preparado para uso por `subprocess.run` em Python:

```python
subprocess.run([
    "java",
    "Main",
    "--benchmark",
    "--dataset",
    "grande",
    "--strategy",
    "multiThreadPerFile",
    "--name",
    nome,
    "--threads-per-file",
    "4",
    "--format",
    "json"
], capture_output=True, text=True)
```

O futuro script Python podera sortear nomes, repetir buscas, testar todas as estrategias, salvar JSON/CSV por maquina, calcular medias, Speedup e gerar graficos.

Nesta etapa, o Java apenas fornece resultados confiaveis e estruturados para essa automacao futura.

## Benchmark com Python

O arquivo `benchmark.py` automatiza a execucao dos testes usando o modo benchmark do Java.

Ele permite escolher apenas o dataset no terminal:

```bash
python benchmark.py
```

Depois da escolha, o script:

- sorteia 5 nomes diferentes que existem no dataset escolhido;
- executa 5 repeticoes para cada nome;
- testa 6 configuracoes de estrategia;
- chama o Java por `subprocess.run`;
- coleta o JSON retornado pelo Java;
- salva os dados brutos em JSON e CSV;
- gera medias por nome;
- gera medias gerais por estrategia;
- calcula Speedup usando a media da estrategia `sequencial` como base.

As configuracoes testadas sao:

```text
sequencial
singleThread
oneThreadPerFile
multiThreadPerFile N=2
multiThreadPerFile N=4
multiThreadPerFile N=8
```

O experimento padrao executa:

```text
5 nomes x 5 repeticoes x 6 configuracoes = 150 execucoes
```

O tempo oficial do benchmark vem do Java, pelos campos `wallTimeMs` e `wallTimeNs`. O Python nao mede o tempo da busca; ele apenas organiza as execucoes e consolida os resultados.

### Arquivos Gerados

Cada execucao cria uma pasta dentro de `results/` com data, hora e nome da maquina:

```text
results/
  DATA_HORA_MAQUINA/
    resultados_brutos.json
    resultados_brutos.csv
    medias_por_nome.csv
    medias_gerais.csv
    speedup.csv
    resumo_benchmark.json
```

Descricao dos arquivos:

| Arquivo | Conteudo |
| --- | --- |
| `resultados_brutos.json` | Metadados do benchmark, nomes sorteados e lista completa das execucoes com o JSON integral retornado pelo Java. |
| `resultados_brutos.csv` | Uma linha por execucao, com os campos principais extraidos para Excel/LibreOffice. |
| `medias_por_nome.csv` | Media, menor e maior tempo agrupados por nome e estrategia. |
| `medias_gerais.csv` | Media, menor e maior tempo agrupados por estrategia. |
| `speedup.csv` | Speedup calculado com base na media geral da estrategia sequencial. |
| `resumo_benchmark.json` | Resumo da execucao, total de sucessos/erros, melhor estrategia e maior Speedup. |

Os arquivos gerados podem ser compartilhados entre integrantes do grupo para comparacao posterior entre maquinas. Essa comparacao entre maquinas e a geracao de graficos ainda nao sao feitas nesta etapa.

### Configuracoes do Script

No topo de `benchmark.py` existem constantes faceis de alterar:

```python
DATASET_PEQUENO_PATH = "dataset_p"
DATASET_GRANDE_PATH = "dataset_g"

JAVA_COMMAND = "java"
JAVAC_COMMAND = "javac"
JAVA_MAIN_CLASS = "Main"

NOMES_ALEATORIOS = 5
REPETICOES_POR_ESTRATEGIA = 5
MULTI_THREAD_VALUES = [2, 4, 8]

COMPILE_BEFORE_RUN = True
RESULTS_DIR = "results"
```

Se `COMPILE_BEFORE_RUN` estiver como `True`, o script tenta compilar os arquivos `.java` antes de iniciar as 150 execucoes. No Windows, o Python lista os arquivos `.java` com `pathlib`, porque o `subprocess.run` nao expande `*.java` automaticamente.

## Estrutura

```text
Main.java
benchmark.py
CliArguments.java
BenchmarkMetrics.java
BenchmarkRunResult.java
BenchmarkFormatter.java
SearchStrategy.java
SearchResult.java
DatasetUtils.java
SequentialSearch.java
SingleThreadSearch.java
OneThreadPerFileSearch.java
MultiThreadPerFileSearch.java
dataset_p/
dataset_g/
```
