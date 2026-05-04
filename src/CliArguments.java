import java.util.HashMap;
import java.util.Map;

public class CliArguments {
    private final String dataset;
    private final String strategy;
    private final String targetName;
    private final String format;
    private final int threadsPerFile;

    private CliArguments(String dataset, String strategy, String targetName, String format, int threadsPerFile) {
        this.dataset = dataset;
        this.strategy = strategy;
        this.targetName = targetName;
        this.format = format;
        this.threadsPerFile = threadsPerFile;
    }

    public static CliArguments parse(String[] args) {
        Map<String, String> values = new HashMap<>();
        boolean benchmark = false;

        for (int index = 0; index < args.length; index++) {
            String arg = args[index];

            if (arg.equals("--benchmark")) {
                benchmark = true;
                continue;
            }

            if (!arg.startsWith("--")) {
                throw new IllegalArgumentException("Argumento invalido: " + arg);
            }

            if (!isKnownArgument(arg)) {
                throw new IllegalArgumentException("Argumento desconhecido: " + arg + ".");
            }

            if (index + 1 >= args.length || args[index + 1].startsWith("--")) {
                throw new IllegalArgumentException("Valor ausente para o argumento " + arg + ".");
            }

            values.put(arg, args[++index]);
        }

        if (!benchmark) {
            throw new IllegalArgumentException("Use --benchmark para executar em modo automatico.");
        }

        String dataset = require(values, "--dataset");
        String strategy = require(values, "--strategy");
        String targetName = require(values, "--name");
        String format = values.getOrDefault("--format", "json");

        if (!dataset.equals("pequeno") && !dataset.equals("grande")) {
            throw new IllegalArgumentException("Dataset invalido. Use pequeno ou grande.");
        }

        if (!strategy.equals("sequencial")
                && !strategy.equals("singleThread")
                && !strategy.equals("oneThreadPerFile")
                && !strategy.equals("multiThreadPerFile")) {
            throw new IllegalArgumentException("Estrategia invalida. Use sequencial, singleThread, oneThreadPerFile ou multiThreadPerFile.");
        }

        if (targetName.trim().isEmpty()) {
            throw new IllegalArgumentException("O nome pesquisado nao pode estar vazio.");
        }

        if (!format.equals("json") && !format.equals("csv")) {
            throw new IllegalArgumentException("Formato invalido. Use json ou csv.");
        }

        int threadsPerFile = 0;

        if (strategy.equals("multiThreadPerFile")) {
            String input = require(values, "--threads-per-file");
            threadsPerFile = parseThreadsPerFile(input);
        } else if (values.containsKey("--threads-per-file")) {
            threadsPerFile = parseThreadsPerFile(values.get("--threads-per-file"));
        }

        return new CliArguments(dataset, strategy, targetName, format, threadsPerFile);
    }

    private static String require(Map<String, String> values, String name) {
        String value = values.get(name);

        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException("Argumento obrigatorio ausente: " + name + ".");
        }

        return value;
    }

    private static boolean isKnownArgument(String arg) {
        return arg.equals("--dataset")
                || arg.equals("--strategy")
                || arg.equals("--name")
                || arg.equals("--threads-per-file")
                || arg.equals("--format");
    }

    private static int parseThreadsPerFile(String input) {
        try {
            int threadsPerFile = Integer.parseInt(input);

            if (threadsPerFile < 1) {
                throw new IllegalArgumentException("--threads-per-file deve ser inteiro maior que zero.");
            }

            return threadsPerFile;
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("--threads-per-file deve ser um numero inteiro.");
        }
    }

    public String getDataset() {
        return dataset;
    }

    public String getStrategy() {
        return strategy;
    }

    public String getTargetName() {
        return targetName;
    }

    public String getFormat() {
        return format;
    }

    public int getThreadsPerFile() {
        return threadsPerFile;
    }
}
