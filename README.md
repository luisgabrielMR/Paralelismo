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
dataset_p/
dataset_g/
```

## Como compilar

Opcao recomendada, gerando os `.class` fora da raiz:

```bash
javac -d out *.java
```

## Como executar

```bash
java -cp out Main
```

Tambem e possivel compilar diretamente na raiz:

```bash
javac *.java
java Main
```

## Observacao

Os caminhos dos datasets estao configurados em `Main.java`:

```java
private static final String DATASET_PEQUENO_PATH = "dataset_p";
private static final String DATASET_GRANDE_PATH = "dataset_g";
```
