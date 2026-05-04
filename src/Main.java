import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;
import java.util.Scanner;

public class Main {
    private static final String DATASET_PEQUENO_PATH = "dataset_p";
    private static final String DATASET_GRANDE_PATH = "dataset_g";

    public static void main(String[] args) {
        if (args.length > 0) {
            runBenchmark(args);
            return;
        }

        runInteractive();
    }

    private static void runInteractive() {
        try (Scanner scanner = new Scanner(System.in)) {
            DatasetOption datasetOption = readDatasetOption(scanner);
            StrategyOption strategyOption = readSearchStrategy(scanner);
            String targetName = readTargetName(scanner);

            long startTime = System.nanoTime();
            SearchResult result = strategyOption.strategy().search(datasetOption.path(), targetName);
            long endTime = System.nanoTime();

            double elapsedMilliseconds = (endTime - startTime) / 1_000_000.0;
            printResult(datasetOption.name(), strategyOption.strategy().getName(), targetName, result, elapsedMilliseconds);
        } catch (IllegalArgumentException | IOException e) {
            System.err.println("Erro: " + e.getMessage());
        }
    }

    private static void runBenchmark(String[] args) {
        try {
            CliArguments cliArguments = CliArguments.parse(args);
            DatasetOption datasetOption = benchmarkDatasetOption(cliArguments.getDataset());
            StrategyOption strategyOption = benchmarkStrategyOption(cliArguments);

            DatasetUtils.listTxtFiles(datasetOption.path());

            long heapUsedBeforeBytes = BenchmarkMetrics.usedHeapBytes();
            BenchmarkMetrics.ProcessCpuSnapshot cpuBefore = BenchmarkMetrics.processCpuSnapshot();
            long startTime = System.nanoTime();
            SearchResult searchResult = strategyOption.strategy().search(datasetOption.path(), cliArguments.getTargetName());
            long endTime = System.nanoTime();
            BenchmarkMetrics.ProcessCpuSnapshot cpuAfter = BenchmarkMetrics.processCpuSnapshot();
            long heapUsedAfterBytes = BenchmarkMetrics.usedHeapBytes();

            BenchmarkMetrics metrics = new BenchmarkMetrics(
                    endTime - startTime,
                    heapUsedBeforeBytes,
                    heapUsedAfterBytes,
                    cpuBefore.getTimeNs(),
                    cpuAfter.getTimeNs(),
                    cpuBefore.isSupported() && cpuAfter.isSupported()
            );

            BenchmarkRunResult runResult = new BenchmarkRunResult(
                    datasetOption.benchmarkName(),
                    strategyOption.benchmarkName(),
                    strategyOption.threadsPerFile(),
                    cliArguments.getTargetName(),
                    searchResult,
                    metrics
            );

            if (cliArguments.getFormat().equals("csv")) {
                System.out.println(BenchmarkFormatter.toCsv(runResult));
            } else {
                System.out.println(BenchmarkFormatter.toJson(runResult));
            }
        } catch (IllegalArgumentException | IOException e) {
            System.err.println("Erro: " + e.getMessage());
            System.exit(1);
        }
    }

    private static DatasetOption readDatasetOption(Scanner scanner) {
        System.out.println("=== Escolha o Dataset ===");
        System.out.println("1 - Dataset pequeno");
        System.out.println("2 - Dataset grande");
        System.out.print("Opcao: ");

        String option = scanner.nextLine().trim();

        if (option.equals("1")) {
            return new DatasetOption("Pequeno", "pequeno", resolveDatasetPath(DATASET_PEQUENO_PATH));
        }

        if (option.equals("2")) {
            return new DatasetOption("Grande", "grande", resolveDatasetPath(DATASET_GRANDE_PATH));
        }

        throw new IllegalArgumentException("Opcao de dataset invalida.");
    }

    private static DatasetOption benchmarkDatasetOption(String dataset) {
        if (dataset.equals("pequeno")) {
            return new DatasetOption("Pequeno", "pequeno", resolveDatasetPath(DATASET_PEQUENO_PATH));
        }

        if (dataset.equals("grande")) {
            return new DatasetOption("Grande", "grande", resolveDatasetPath(DATASET_GRANDE_PATH));
        }

        throw new IllegalArgumentException("Dataset invalido. Use pequeno ou grande.");
    }

    private static Path resolveDatasetPath(String datasetPath) {
        Path directPath = Paths.get(datasetPath);

        if (directPath.isAbsolute() || Files.exists(directPath)) {
            return directPath;
        }

        Path classDirectory = getClassDirectory();

        if (classDirectory != null) {
            Path pathNextToClasses = classDirectory.resolve(datasetPath);

            if (Files.exists(pathNextToClasses)) {
                return pathNextToClasses;
            }

            Path projectDirectory = classDirectory.getParent();

            if (projectDirectory != null) {
                Path pathNextToOutputDirectory = projectDirectory.resolve(datasetPath);

                if (Files.exists(pathNextToOutputDirectory)) {
                    return pathNextToOutputDirectory;
                }
            }
        }

        return directPath;
    }

    private static Path getClassDirectory() {
        try {
            Path location = Paths.get(Main.class.getProtectionDomain().getCodeSource().getLocation().toURI());

            if (Files.isRegularFile(location)) {
                return location.getParent();
            }

            return location;
        } catch (Exception e) {
            return null;
        }
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

    private static StrategyOption readSearchStrategy(Scanner scanner) {
        System.out.println();
        System.out.println("=== Escolha a Estrategia de Busca ===");
        System.out.println("1 - Sequencial");
        System.out.println("2 - Sequencial em uma Thread");
        System.out.println("3 - Uma Thread por arquivo");
        System.out.println("4 - N Threads por arquivo");
        System.out.print("Opcao: ");

        String option = scanner.nextLine().trim();

        if (option.equals("1")) {
            return new StrategyOption("sequencial", new SequentialSearch(), 0);
        }

        if (option.equals("2")) {
            return new StrategyOption("singleThread", new SingleThreadSearch(), 0);
        }

        if (option.equals("3")) {
            return new StrategyOption("oneThreadPerFile", new OneThreadPerFileSearch(), 0);
        }

        if (option.equals("4")) {
            int threadsPerFile = readThreadsPerFile(scanner);
            return new StrategyOption("multiThreadPerFile", new MultiThreadPerFileSearch(threadsPerFile), threadsPerFile);
        }

        throw new IllegalArgumentException("Opcao de estrategia invalida.");
    }

    private static StrategyOption benchmarkStrategyOption(CliArguments cliArguments) {
        String strategy = cliArguments.getStrategy();

        if (strategy.equals("sequencial")) {
            return new StrategyOption(strategy, new SequentialSearch(), 0);
        }

        if (strategy.equals("singleThread")) {
            return new StrategyOption(strategy, new SingleThreadSearch(), 0);
        }

        if (strategy.equals("oneThreadPerFile")) {
            return new StrategyOption(strategy, new OneThreadPerFileSearch(), 0);
        }

        if (strategy.equals("multiThreadPerFile")) {
            int threadsPerFile = cliArguments.getThreadsPerFile();
            return new StrategyOption(strategy, new MultiThreadPerFileSearch(threadsPerFile), threadsPerFile);
        }

        throw new IllegalArgumentException("Estrategia invalida. Use sequencial, singleThread, oneThreadPerFile ou multiThreadPerFile.");
    }

    private static int readThreadsPerFile(Scanner scanner) {
        System.out.print("Quantas Threads por arquivo deseja usar? ");
        String input = scanner.nextLine().trim();

        try {
            int threadsPerFile = Integer.parseInt(input);

            if (threadsPerFile < 1) {
                throw new IllegalArgumentException("A quantidade de Threads por arquivo deve ser maior que zero.");
            }

            return threadsPerFile;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("A quantidade de Threads por arquivo deve ser um numero inteiro.");
        }
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

        System.out.printf(Locale.US, "Tempo de execucao: %.2f ms%n", elapsedMilliseconds);
    }

    private static class DatasetOption {
        private final String name;
        private final String benchmarkName;
        private final Path path;

        private DatasetOption(String name, String benchmarkName, Path path) {
            this.name = name;
            this.benchmarkName = benchmarkName;
            this.path = path;
        }

        private String name() {
            return name;
        }

        private String benchmarkName() {
            return benchmarkName;
        }

        private Path path() {
            return path;
        }
    }

    private static class StrategyOption {
        private final String benchmarkName;
        private final SearchStrategy strategy;
        private final int threadsPerFile;

        private StrategyOption(String benchmarkName, SearchStrategy strategy, int threadsPerFile) {
            this.benchmarkName = benchmarkName;
            this.strategy = strategy;
            this.threadsPerFile = threadsPerFile;
        }

        private String benchmarkName() {
            return benchmarkName;
        }

        private SearchStrategy strategy() {
            return strategy;
        }

        private int threadsPerFile() {
            return threadsPerFile;
        }
    }
}
