import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class DatasetUtils {
    public static List<Path> listTxtFiles(Path datasetPath) throws IOException {
        if (!Files.exists(datasetPath)) {
            throw new IOException("A pasta do dataset nao existe: " + datasetPath);
        }

        if (!Files.isDirectory(datasetPath)) {
            throw new IOException("O caminho informado nao e uma pasta: " + datasetPath);
        }

        List<Path> txtFiles;

        try (Stream<Path> paths = Files.list(datasetPath)) {
            txtFiles = paths
                    .filter(Files::isRegularFile)
                    .filter(DatasetUtils::isTxtFile)
                    .sorted(Comparator.comparing(path -> path.getFileName().toString().toLowerCase()))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            throw new IOException("Erro ao listar arquivos do dataset: " + e.getMessage(), e);
        }

        if (txtFiles.isEmpty()) {
            throw new IOException("Nao ha arquivos .txt na pasta do dataset: " + datasetPath);
        }

        return txtFiles;
    }

    private static boolean isTxtFile(Path path) {
        return path.getFileName().toString().toLowerCase().endsWith(".txt");
    }
}
