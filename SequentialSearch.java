import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public class SequentialSearch implements SearchStrategy {
    @Override
    public SearchResult search(Path datasetPath, String targetName) throws IOException {
        List<Path> files = DatasetUtils.listTxtFiles(datasetPath);

        for (Path file : files) {
            SearchResult result = searchInFile(file, targetName);

            if (result.isFound()) {
                return result;
            }
        }

        return SearchResult.notFound();
    }

    @Override
    public String getName() {
        return "Sequencial";
    }

    private SearchResult searchInFile(Path file, String targetName) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(file)) {
            String line;
            int lineNumber = 1;

            while ((line = reader.readLine()) != null) {
                if (line.trim().equalsIgnoreCase(targetName.trim())) {
                    return SearchResult.found(file.getFileName().toString(), lineNumber, line);
                }

                lineNumber++;
            }
        } catch (IOException e) {
            throw new IOException("Erro de leitura no arquivo " + file.getFileName() + ": " + e.getMessage(), e);
        }

        return SearchResult.notFound();
    }
}
