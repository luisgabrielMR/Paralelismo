import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Scanner;

public class Main {
    private static final String DATASET_PEQUENO_PATH = "dataset_p";
    private static final String DATASET_GRANDE_PATH = "dataset_g";

    public static void main(String[] args) {
        try (Scanner scanner = new Scanner(System.in)) {
            DatasetOption datasetOption = readDatasetOption(scanner);
            SearchStrategy strategy = readSearchStrategy(scanner);
            String targetName = readTargetName(scanner);

            long startTime = System.nanoTime();
            SearchResult result = strategy.search(datasetOption.path(), targetName);
            long endTime = System.nanoTime();

            double elapsedMilliseconds = (endTime - startTime) / 1_000_000.0;
            printResult(datasetOption.name(), strategy.getName(), targetName, result, elapsedMilliseconds);
        } catch (IllegalArgumentException | IOException e) {
            System.out.println("Erro: " + e.getMessage());
        }
    }

    private static DatasetOption readDatasetOption(Scanner scanner) {
        System.out.println("=== Escolha o Dataset ===");
        System.out.println("1 - Dataset pequeno");
        System.out.println("2 - Dataset grande");
        System.out.print("Opcao: ");

        String option = scanner.nextLine().trim();

        if (option.equals("1")) {
            return new DatasetOption("Pequeno", Paths.get(DATASET_PEQUENO_PATH));
        }

        if (option.equals("2")) {
            return new DatasetOption("Grande", Paths.get(DATASET_GRANDE_PATH));
        }

        throw new IllegalArgumentException("Opcao de dataset invalida.");
    }

    private static String readTargetName(Scanner scanner) {
        System.out.println();
        System.out.println("Digite o nome completo para buscar:");
        String targetName = scanner.nextLine();

        if (targetName.trim().isEmpty()) {
            throw new IllegalArgumentException("O nome pesquisado nao pode estar vazio.");
        }

        return targetName;
    }

    private static SearchStrategy readSearchStrategy(Scanner scanner) {
        System.out.println();
        System.out.println("=== Escolha a Estrategia de Busca ===");
        System.out.println("1 - Sequencial");
        System.out.print("Opcao: ");

        String option = scanner.nextLine().trim();

        if (option.equals("1")) {
            return new SequentialSearch();
        }

        throw new IllegalArgumentException("Opcao de estrategia invalida.");
    }

    private static void printResult(
            String datasetName,
            String strategyName,
            String targetName,
            SearchResult result,
            double elapsedMilliseconds
    ) {
        System.out.println();
        System.out.println("=== Resultado da Busca ===");
        System.out.println("Dataset: " + datasetName);
        System.out.println("Estrategia: " + strategyName);
        System.out.println("Nome pesquisado: " + targetName);
        System.out.println("Encontrado: " + (result.isFound() ? "Sim" : "Nao"));

        if (result.isFound()) {
            System.out.println("Arquivo: " + result.getFileName());
            System.out.println("Linha: " + result.getLineNumber());
            System.out.println("Conteudo da linha: " + result.getLineContent());
        }

        System.out.printf("Tempo de execucao: %.2f ms%n", elapsedMilliseconds);
    }

    private static class DatasetOption {
        private final String name;
        private final Path path;

        private DatasetOption(String name, Path path) {
            this.name = name;
            this.path = path;
        }

        private String name() {
            return name;
        }

        private Path path() {
            return path;
        }
    }
}
