# Busca Sequencial de Nomes

Programa Java puro para buscar um nome completo em arquivos `.txt`.

Nesta primeira versao, a busca e totalmente sequencial.

## Estrutura

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

## Como compilar

Opcao simples:

```bash
javac *.java
```

Opcao alternativa, gerando os `.class` fora da raiz:

```bash
javac -d out *.java
```

## Como executar

Se compilou com `javac *.java`:

```bash
java Main
```

Se compilou com `javac -d out *.java`:

```bash
java -cp out Main
```

Ou, se entrar na pasta `out`:

```bash
java Main
```

## Estrategias

1 - Sequencial
2 - Sequencial em uma Thread
3 - Uma Thread por arquivo
4 - N Threads por arquivo

## Observacao

Os caminhos dos datasets estao configurados em `Main.java`:

```java
private static final String DATASET_PEQUENO_PATH = "dataset_p";
private static final String DATASET_GRANDE_PATH = "dataset_g";
```
