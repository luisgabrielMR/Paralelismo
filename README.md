# Busca de Nomes em Arquivos `.txt` com Estrategias Sequenciais e Paralelas

Esta e uma versao um pouco melhor do projeto desenvolvido em **Java puro** para a disciplina de **Programacao Paralela e Distribuida**.

O objetivo e buscar um **nome completo** dentro de arquivos `.txt`, comparando diferentes estrategias de execucao:

- busca sequencial;
- busca sequencial executada dentro de uma Thread;
- busca paralela com uma Thread por arquivo;
- busca paralela com N Threads por arquivo.

A ideia central e analisar se o uso de Threads melhora o tempo de busca e, posteriormente, calcular a metrica de **Speedup** entre a versao sequencial e as versoes paralelas.

---

## Ideia Geral

O programa trabalha com dois datasets:

```text
dataset_p/  -> Dataset pequeno
dataset_g/  -> Dataset grande
```

Cada arquivo `.txt` contem nomes completos, seguindo estas regras:

- cada linha possui exatamente um nome completo;
- cada nome e formado por nome + sobrenome;
- todos os nomes sao unicos;
- a busca deve encontrar no maximo uma ocorrencia.

Exemplo de arquivo:

```text
Ana Silva
Joao Oliveira
Pedro Santos
Maria Souza
```

Ao encontrar o nome pesquisado, o programa informa:

- dataset utilizado;
- estrategia de busca utilizada;
- nome pesquisado;
- se o nome foi encontrado;
- arquivo onde o nome esta;
- numero da linha;
- conteudo da linha;
- tempo de execucao.

## Regras da Busca

A busca e feita comparando a linha inteira com o nome pesquisado.
Ou seja, o programa nao procura pedacos do texto.

A comparacao usada e:

```java
linha.trim().equalsIgnoreCase(nomeBuscado.trim())
```

Isso significa que:

- diferencas entre maiusculas e minusculas sao ignoradas;
- espacos extras no inicio ou no fim da linha sao ignorados;
- o nome precisa bater com a linha completa.

Por exemplo, se o nome buscado for:

```text
Ana Silva
```

O programa aceita:

```text
Ana Silva
```

Mas nao aceita:

```text
Mariana Silva
Ana Silva Santos
```

## Estrategias Implementadas

O projeto foi organizado para que cada estrategia de busca seja uma classe separada.

### 1. Busca Sequencial

Classe:

```text
SequentialSearch.java
```

Essa e a versao base do projeto. Ela percorre os arquivos um por um e, dentro de cada arquivo, le linha por linha ate encontrar o nome.

Importante:

- nao usa Thread;
- nao usa paralelismo;
- serve como referencia para comparar as outras estrategias.

### 2. Busca Sequencial em uma Thread

Classe:

```text
SingleThreadSearch.java
```

Essa estrategia executa a mesma logica da busca sequencial, mas dentro de uma unica Thread.

Ela e util para observar se existe diferenca pratica entre executar a busca diretamente no fluxo principal do programa ou dentro de uma Thread separada.

### 3. Uma Thread por Arquivo

Classe:

```text
OneThreadPerFileSearch.java
```

Essa estrategia cria uma tarefa para cada arquivo `.txt`.

Exemplo:

```text
Arquivo 1 -> Thread 1
Arquivo 2 -> Thread 2
Arquivo 3 -> Thread 3
```

Cada Thread busca o nome em um arquivo diferente.
Quando uma Thread encontra o nome, o programa sinaliza para as demais pararem o quanto antes.

### 4. N Threads por Arquivo

Classe:

```text
MultiThreadPerFileSearch.java
```

Essa estrategia permite escolher quantas Threads serao usadas por arquivo.

Exemplo com um arquivo de 2.000 linhas e 2 Threads:

```text
Thread 1 -> linhas 1 ate 1000
Thread 2 -> linhas 1001 ate 2000
```

Exemplo com 4 Threads:

```text
Thread 1 -> linhas 1 ate 500
Thread 2 -> linhas 501 ate 1000
Thread 3 -> linhas 1001 ate 1500
Thread 4 -> linhas 1501 ate 2000
```

Essa estrategia permite testar diferentes niveis de paralelismo e analisar se aumentar a quantidade de Threads melhora ou piora o desempenho.

## Estrutura do Projeto

```text
Main.java
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

## Descricao dos Arquivos

| Arquivo | Funcao |
| --- | --- |
| `Main.java` | Controla o menu, entrada do usuario, escolha do dataset, escolha da estrategia e exibicao do resultado. |
| `SearchStrategy.java` | Interface comum para todas as estrategias de busca. |
| `SearchResult.java` | Representa o resultado da busca. |
| `DatasetUtils.java` | Lista e valida os arquivos `.txt` dos datasets. |
| `SequentialSearch.java` | Busca sequencial pura. |
| `SingleThreadSearch.java` | Busca sequencial dentro de uma Thread. |
| `OneThreadPerFileSearch.java` | Busca paralela com uma Thread por arquivo. |
| `MultiThreadPerFileSearch.java` | Busca paralela com N Threads por arquivo. |
| `dataset_p/` | Pasta do dataset pequeno. |
| `dataset_g/` | Pasta do dataset grande. |

## Configuracao dos Datasets

Os caminhos dos datasets estao configurados no arquivo `Main.java`:

```java
private static final String DATASET_PEQUENO_PATH = "dataset_p";
private static final String DATASET_GRANDE_PATH = "dataset_g";
```

Se as pastas `dataset_p` e `dataset_g` estiverem na mesma pasta dos arquivos `.java`, nao e necessario alterar nada.

Caso estejam em outro local, altere os caminhos manualmente.

Exemplo no Windows:

```java
private static final String DATASET_PEQUENO_PATH = "C:/Users/User/Documents/GitHub/Paralelismo/dataset_p";
private static final String DATASET_GRANDE_PATH = "C:/Users/User/Documents/GitHub/Paralelismo/dataset_g";
```

## Como Compilar

Opcao simples, gerando os arquivos `.class` na propria pasta raiz:

```bash
javac *.java
```

Opcao alternativa, gerando os arquivos `.class` dentro de uma pasta separada chamada `out`:

```bash
javac -d out *.java
```

## Como Executar

Se compilou com `javac *.java`:

```bash
java Main
```

Se compilou com `javac -d out *.java`:

```bash
java -cp out Main
```

Ou entre na pasta `out` e execute:

```bash
java Main
```

## Fluxo de Uso

Ao executar o programa, o usuario devera:

1. escolher o dataset;
2. escolher a estrategia de busca;
3. digitar o nome completo que deseja procurar;
4. aguardar o resultado.

Menu esperado:

```text
=== Escolha o Dataset ===
1 - Dataset pequeno
2 - Dataset grande
```

Depois:

```text
=== Escolha a Estrategia de Busca ===
1 - Sequencial
2 - Sequencial em uma Thread
3 - Uma Thread por arquivo
4 - N Threads por arquivo
```

Se a estrategia escolhida for a opcao `4`, o programa tambem solicitara a quantidade de Threads por arquivo.

## Exemplo de Saida

Quando o nome e encontrado:

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

Quando o nome nao e encontrado:

```text
=== Resultado da Busca ===
Dataset: Grande
Estrategia: Uma Thread por arquivo
Nome pesquisado: Ana Silva
Encontrado: Nao
Tempo de execucao: 38.91 ms
```

## Metrica de Speedup

A metrica de Speedup pode ser usada para comparar o desempenho das versoes paralelas com a versao sequencial.

A formula e:

```text
Speedup = Tempo Sequencial / Tempo Paralelo
```

Exemplo:

```text
Tempo sequencial: 100 ms
Tempo paralelo: 25 ms
Speedup = 100 / 25
Speedup = 4
```

Nesse caso, a versao paralela foi 4 vezes mais rapida que a versao sequencial.

## Observacoes Importantes

- A busca sequencial pura nao utiliza Threads.
- As estrategias paralelas devem parar o quanto antes quando o nome for encontrado.
- O tempo medido considera apenas a execucao da busca.
- A digitacao do usuario nao entra no calculo do tempo.
- O resultado da busca deve ser sempre o mesmo entre as estrategias.
- O desempenho pode variar conforme o tamanho dos arquivos, posicao do nome e caracteristicas da maquina.

## Possiveis Evolucoes Futuras

Algumas melhorias podem ser adicionadas posteriormente:

- execucao automatica de testes varias vezes;
- calculo automatico de media dos tempos;
- calculo automatico de Speedup;
- geracao de arquivos `.csv` com os resultados;
- script em Python para sortear nomes e executar os testes;
- geracao de graficos;
- coleta complementar de uso de CPU e memoria;
- comparacao dos resultados entre maquinas diferentes.

## Requisitos

- Java JDK instalado.
- Terminal ou PowerShell.
- Arquivos `.txt` organizados nas pastas dos datasets.

Para verificar se o Java esta instalado corretamente:

```bash
java -version
javac -version
```
