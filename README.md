# Busca de Nomes em Arquivos `.txt`

## Visao Geral

Este projeto compara estrategias sequenciais e paralelas para buscar nomes completos em arquivos `.txt`.

O sistema tem duas partes:

- **Java**: executa a busca, mede o tempo oficial e retorna o resultado.
- **Python**: automatiza os benchmarks, gera CSV/JSON, cria relatorios HTML e consolida resultados de varias maquinas.

O objetivo principal e analisar quando o uso de Threads melhora ou piora o desempenho em relacao a busca sequencial.

## Objetivo da Atividade

A atividade consiste em comparar diferentes estrategias de busca em datasets de nomes:

- dataset pequeno;
- dataset grande;
- datasets sinteticos maiores, quando desejado.

As metricas principais sao:

- tempo medio de execucao;
- menor e maior tempo;
- Speedup em relacao a busca sequencial;
- comparacao entre maquinas, no relatorio consolidado do grupo.

## Funcionamento da Busca

Cada arquivo `.txt` possui um nome completo por linha.

A busca compara a linha inteira com o nome pesquisado:

```java
line.trim().equalsIgnoreCase(targetName.trim())
```

Isso significa que:

- a busca ignora diferencas entre maiusculas e minusculas;
- espacos extras no inicio e no fim sao ignorados;
- a linha completa precisa ser igual ao nome buscado;
- o projeto nao usa `contains`.

## Estrategias Implementadas

| Estrategia | Argumento | Classe |
| --- | --- | --- |
| Sequencial pura | `sequencial` | `SequentialSearch.java` |
| Sequencial dentro de uma Thread | `singleThread` | `SingleThreadSearch.java` |
| Uma Thread por arquivo | `oneThreadPerFile` | `OneThreadPerFileSearch.java` |
| N Threads por arquivo | `multiThreadPerFile` | `MultiThreadPerFileSearch.java` |

As configuracoes usadas pelo benchmark automatico sao:

```text
sequencial
singleThread
oneThreadPerFile
multiThreadPerFile N=2
multiThreadPerFile N=4
multiThreadPerFile N=8
```

## Estrutura do Projeto

```text
PARALELISMO/
|-- src/
|   |-- Main.java
|   |-- SearchStrategy.java
|   |-- SearchResult.java
|   |-- DatasetUtils.java
|   |-- SequentialSearch.java
|   |-- SingleThreadSearch.java
|   |-- OneThreadPerFileSearch.java
|   |-- MultiThreadPerFileSearch.java
|   |-- BenchmarkFormatter.java
|   |-- BenchmarkMetrics.java
|   |-- BenchmarkRunResult.java
|   `-- CliArguments.java
|
|-- scripts/
|   |-- benchmark.py
|   |-- generate_report.py
|   |-- generate_dataset.py
|   `-- compare_results.py
|
|-- dataset_p/
|-- dataset_g/
|-- out/
|-- results/
|-- README.md
|-- .gitignore
`-- LICENSE
```

As classes Java estao no **default package** para manter a compilacao simples.

## Como executar o projeto

Esta e a parte principal para usar o projeto. Ela separa a execucao direta pelo Java da automacao feita pelos scripts Python.

### 1. Execucao pelo Java

O Java pode ser usado de duas formas:

- modo interativo no terminal;
- modo benchmark manual, com argumentos.

#### 1.1 Modo interativo no terminal

Use este modo quando quiser testar manualmente:

- escolher o dataset;
- escolher a estrategia;
- digitar o nome;
- ver o resultado no terminal.

Primeiro, compile:

```bash
javac -d out src/*.java
```

Depois execute:

```bash
java -cp out Main
```

Fluxo esperado:

1. o programa pergunta o dataset;
2. o programa pergunta a estrategia;
3. o usuario digita o nome completo;
4. o Java executa a busca;
5. o resultado aparece no terminal.

Exemplo resumido de saida:

```text
=== Resultado da Busca ===
Dataset: Pequeno
Estrategia: Sequencial
Nome pesquisado: Ana Silva
Encontrado: Sim
Arquivo: nomes_01.txt
Linha: 348
Tempo de execucao: 12.45 ms
```

Importante:

- esse modo e bom para testar rapidamente;
- esse modo e manual;
- esse modo nao gera os arquivos completos de analise em CSV/JSON.

#### 1.2 Modo benchmark manual pelo Java

Use este modo quando quiser chamar o Java diretamente com argumentos, sem menus.

Exemplos:

```bash
java -cp out Main --benchmark --dataset pequeno --strategy sequencial --name "Ana Silva" --format json
```

```bash
java -cp out Main --benchmark --dataset grande --strategy oneThreadPerFile --name "Ana Silva" --format json
```

```bash
java -cp out Main --benchmark --dataset grande --strategy multiThreadPerFile --name "Ana Silva" --threads-per-file 4 --format json
```

```bash
java -cp out Main --benchmark --dataset custom --dataset-path "dataset_xg" --strategy sequencial --name "Ana Silva" --format json
```

Neste modo:

- o Java imprime apenas JSON ou CSV;
- nao aparecem menus;
- ele e usado principalmente pelo Python;
- o tempo medido considera apenas a chamada da busca;
- o tempo nao inclui digitacao, escolha de menu, parse de argumentos ou impressao.

Exemplo pequeno de JSON retornado:

```json
{
  "dataset": "pequeno",
  "strategy": "sequencial",
  "threadsPerFile": 0,
  "targetName": "Ana Silva",
  "found": true,
  "fileName": "nomes_01.txt",
  "lineNumber": 348,
  "wallTimeMs": 12.45
}
```

Argumentos principais:

| Argumento | Uso |
| --- | --- |
| `--benchmark` | ativa o modo automatico |
| `--dataset pequeno` | usa `dataset_p` |
| `--dataset grande` | usa `dataset_g` |
| `--dataset custom --dataset-path "dataset_xg"` | usa uma pasta de dataset personalizada |
| `--strategy` | escolhe a estrategia |
| `--name` | nome completo pesquisado |
| `--threads-per-file` | obrigatorio apenas em `multiThreadPerFile` |
| `--format` | `json` ou `csv` |

### 2. Execucao pelo Python

Os scripts Python automatizam a parte de analise. Eles chamam o Java em modo benchmark, coletam os resultados e geram arquivos para estudo.

#### 2.1 Rodar benchmark automatico

Este e o comando principal para gerar resultados:

```bash
python scripts/benchmark.py
```

O que acontece:

1. o usuario escolhe o dataset no terminal;
2. o Python lista `dataset_p`, `dataset_g` e datasets personalizados `dataset_*`;
3. o Python sorteia 5 nomes diferentes;
4. para cada nome, executa 5 repeticoes por estrategia;
5. testa as 6 configuracoes padrao;
6. coleta os JSONs retornados pelo Java;
7. gera CSVs, JSONs e relatorio HTML.

Total padrao:

```text
5 nomes x 5 repeticoes x 6 configuracoes = 150 execucoes
```

Exemplo de menu:

```text
=== Benchmark de Busca de Nomes ===

Escolha o dataset:
1 - Dataset pequeno (dataset_p)
2 - Dataset grande (dataset_g)
3 - dataset_xg
```

Estrutura de saida:

```text
results/
`-- DATA_HORA_MAQUINA/
    |-- relatorio.html
    `-- data/
        |-- resultados_brutos.json
        |-- resultados_brutos.csv
        |-- medias_por_nome.csv
        |-- medias_gerais.csv
        |-- speedup.csv
        `-- resumo_benchmark.json
```

Esse e o modo recomendado para gerar os dados da analise.

#### 2.2 Gerar relatorio individual manualmente

Normalmente, `benchmark.py` ja gera o relatorio individual automaticamente.

Se precisar gerar novamente:

```bash
python scripts/generate_report.py results/DATA_HORA_MAQUINA
```

Esse script:

- le os arquivos dentro de `data/`;
- gera ou atualiza `relatorio.html`;
- cria um HTML que pode ser aberto diretamente no navegador.

#### 2.3 Gerar dataset sintetico

Datasets maiores podem ser criados com:

```bash
python scripts/generate_dataset.py --output dataset_xg --files 10 --names-per-file 100000 --seed 42
```

Exemplo maior:

```bash
python scripts/generate_dataset.py --output dataset_50x200k --files 50 --names-per-file 200000 --no-shuffle --force
```

Todo dataset cujo nome comeca com `dataset_` aparece automaticamente no menu do benchmark.

Datasets sinteticos sao uteis para testar se o paralelismo passa a compensar em volumes maiores, ja que em datasets pequenos o custo de criar e coordenar Threads pode ser maior que o ganho.

#### 2.4 Gerar relatorio consolidado do grupo

Fluxo recomendado:

1. cada integrante roda:

```bash
python scripts/benchmark.py
```

2. cada integrante envia a pasta gerada dentro de `results/`;
3. todas as pastas sao colocadas dentro de `results/` na maquina que vai gerar o relatorio final;
4. execute:

```bash
python scripts/compare_results.py
```

ou:

```bash
python scripts/compare_results.py --results-dir results
```

Estrutura gerada:

```text
results/
`-- group_report_DATA_HORA/
    |-- group_report.html
    `-- data/
        |-- resultados_consolidados.csv
        |-- medias_por_maquina.csv
        |-- medias_gerais_grupo.csv
        |-- speedup_por_maquina.csv
        |-- speedup_geral_grupo.csv
        `-- resumo_grupo.json
```

O relatorio consolidado tem duas partes:

| Parte | Conteudo |
| --- | --- |
| Analise Principal da Atividade | usa apenas `pequeno` e `grande`, mostra tempo medio, Speedup e comparacao entre maquinas |
| Analises Complementares | usa datasets maiores, CPU, memoria, quantidade de Threads e observacoes de overhead |

## Como abrir os resultados

Os relatorios sao arquivos HTML. Eles podem ser abertos diretamente no navegador, sem servidor web.

### Relatorio individual

Caminho:

```text
results/DATA_HORA_MAQUINA/relatorio.html
```

No PowerShell:

```powershell
start results\DATA_HORA_MAQUINA\relatorio.html
```

Tambem e possivel abrir manualmente pelo Explorador de Arquivos.

### Relatorio consolidado do grupo

Caminho:

```text
results/group_report_DATA_HORA/group_report.html
```

No PowerShell:

```powershell
start results\group_report_DATA_HORA\group_report.html
```

## Relatorio Consolidado do Grupo

O relatorio consolidado junta varias execucoes individuais e compara os resultados entre maquinas.

Ele procura automaticamente, dentro de `results/`, pastas que tenham:

```text
data/resultados_brutos.csv
data/medias_gerais.csv
data/speedup.csv
data/resumo_benchmark.json
```

Pastas incompletas sao ignoradas com aviso. Relatorios consolidados antigos `group_report_*` tambem sao ignorados para nao entrar na comparacao.

Arquivos gerados:

| Arquivo | Conteudo |
| --- | --- |
| `resultados_consolidados.csv` | todas as linhas brutas de todas as execucoes |
| `medias_por_maquina.csv` | medias agrupadas por maquina, dataset e estrategia |
| `medias_gerais_grupo.csv` | medias do grupo por dataset e estrategia |
| `speedup_por_maquina.csv` | Speedup calculado separadamente por maquina e dataset |
| `speedup_geral_grupo.csv` | Speedup geral do grupo por dataset |
| `resumo_grupo.json` | resumo da consolidacao |
| `group_report.html` | relatorio visual consolidado |

## Geracao de Datasets Sinteticos

O script `scripts/generate_dataset.py` gera datasets `.txt` maiores para testar melhor as estrategias.

Cada arquivo gerado contem exatamente um nome completo por linha. Todos os nomes completos sao unicos no dataset inteiro. O mesmo primeiro nome ou sobrenome pode aparecer em varias linhas; o que nao se repete e a linha completa.

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

Formatos escolhidos automaticamente:

| Tamanho solicitado | Formato |
| --- | --- |
| ate 10.000 nomes | Nome + Sobrenome |
| ate 1.000.000 nomes | Nome + Sobrenome + Sobrenome |
| ate 100.000.000 nomes | Nome + Nome + Sobrenome + Sobrenome |
| ate 10.000.000.000 nomes | Nome + Nome + Sobrenome + Sobrenome + Sobrenome |

O arquivo `manifest.json` registra a configuracao usada, seed, formato escolhido, capacidade, data/hora, versao do Python, sistema operacional e nome da maquina.

## Metricas Coletadas

O Java retorna as metricas principais e complementares:

| Metrica | Descricao |
| --- | --- |
| `wallTimeMs` / `wallTimeNs` | tempo oficial da busca |
| `processCpuTimeMs` | tempo de CPU do processo, quando suportado |
| `cpuUsageApproxPercent` | uso aproximado de CPU, quando suportado |
| `heapDeltaBytes` | variacao de heap durante a busca |
| `availableProcessors` | processadores disponiveis |
| `javaVersion` | versao do Java |
| `osName` / `osArch` | sistema operacional e arquitetura |
| `machineName` | nome da maquina reportado pelo Java |

Metricas nulas sao ignoradas nos calculos de media correspondentes.

## Como Interpretar os Resultados

Use `wallTimeMs` como metrica principal de tempo.

O Speedup e calculado assim:

```text
Speedup = tempo medio sequencial / tempo medio da estrategia
```

Interpretacao:

| Speedup | Significado |
| --- | --- |
| maior que 1 | a estrategia foi mais rapida que a sequencial |
| igual a 1 | desempenho equivalente |
| menor que 1 | a estrategia foi mais lenta que a sequencial |

Se estrategias paralelas forem mais lentas em datasets pequenos, isso normalmente indica overhead de Threads: criacao, agendamento, sincronizacao e coordenacao podem custar mais que a busca em si.

Datasets sinteticos maiores ajudam a observar se o paralelismo passa a compensar quando ha mais trabalho para dividir.

## Observacao sobre Git

As pastas `out/` e `results/` sao ignoradas pelo Git porque contem arquivos gerados localmente:

- `out/`: classes `.class` compiladas;
- `results/`: dados e relatorios de benchmark de cada maquina.

Neste repositorio, `dataset_p/`, `dataset_g/` e datasets personalizados `dataset_*/` permanecem como dados locais ignorados pelo Git. Os fontes em `src/` e os scripts em `scripts/` nao sao ignorados.

Como `results/` e ignorado, as pastas de resultado devem ser compartilhadas manualmente entre os integrantes para gerar o relatorio consolidado do grupo.

## Ordem Recomendada de Uso

### Para testar localmente

1. Compilar Java:

```bash
javac -d out src/*.java
```

2. Rodar modo interativo:

```bash
java -cp out Main
```

3. Rodar benchmark:

```bash
python scripts/benchmark.py
```

4. Abrir relatorio:

```text
results/DATA_HORA_MAQUINA/relatorio.html
```

### Para analise do grupo

1. Cada integrante roda:

```bash
python scripts/benchmark.py
```

2. Cada um compartilha a pasta de resultado.
3. Junte todas as pastas em `results/`.
4. Rode:

```bash
python scripts/compare_results.py
```

5. Abra:

```text
results/group_report_DATA_HORA/group_report.html
```

### Para testar datasets maiores

1. Gerar dataset:

```bash
python scripts/generate_dataset.py --output dataset_xg --files 10 --names-per-file 100000 --seed 42
```

2. Rodar benchmark:

```bash
python scripts/benchmark.py
```

3. Escolher `dataset_xg` no menu.
4. Abrir o relatorio individual.
5. Depois, incluir esse resultado no relatorio consolidado.
