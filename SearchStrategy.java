import java.io.IOException;
import java.nio.file.Path;

public interface SearchStrategy {
    SearchResult search(Path datasetPath, String targetName) throws IOException;

    String getName();
}
