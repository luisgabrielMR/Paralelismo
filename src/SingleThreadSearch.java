import java.io.IOException;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicReference;

public class SingleThreadSearch implements SearchStrategy {
    @Override
    public SearchResult search(Path datasetPath, String targetName) throws IOException {
        AtomicReference<SearchResult> resultRef = new AtomicReference<>(SearchResult.notFound());
        AtomicReference<IOException> exceptionRef = new AtomicReference<>();

        Thread thread = new Thread(() -> {
            try {
                resultRef.set(new SequentialSearch().search(datasetPath, targetName));
            } catch (IOException e) {
                exceptionRef.set(e);
            }
        });

        thread.start();

        try {
            thread.join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("A busca foi interrompida.", e);
        }

        if (exceptionRef.get() != null) {
            throw exceptionRef.get();
        }

        return resultRef.get();
    }

    @Override
    public String getName() {
        return "Sequencial em uma Thread";
    }
}
