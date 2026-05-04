import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

public class OneThreadPerFileSearch implements SearchStrategy {
    @Override
    public SearchResult search(Path datasetPath, String targetName) throws IOException {
        List<Path> files = DatasetUtils.listTxtFiles(datasetPath);
        ExecutorService executor = Executors.newFixedThreadPool(files.size());
        AtomicBoolean foundFlag = new AtomicBoolean(false);
        AtomicReference<SearchResult> resultRef = new AtomicReference<>(SearchResult.notFound());
        List<Future<?>> futures = new ArrayList<>();

        try {
            for (Path file : files) {
                futures.add(executor.submit(() -> {
                    searchInFile(file, targetName, foundFlag, resultRef);
                    return null;
                }));
            }

            for (Future<?> future : futures) {
                if (foundFlag.get()) {
                    cancelPendingTasks(futures);
                    break;
                }

                try {
                    future.get();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    cancelPendingTasks(futures);
                    throw new IOException("A busca foi interrompida.", e);
                } catch (ExecutionException e) {
                    cancelPendingTasks(futures);
                    throw asIOException(e.getCause());
                }
            }

            return resultRef.get();
        } finally {
            executor.shutdownNow();
        }
    }

    @Override
    public String getName() {
        return "Uma Thread por arquivo";
    }

    private void searchInFile(
            Path file,
            String targetName,
            AtomicBoolean foundFlag,
            AtomicReference<SearchResult> resultRef
    ) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(file)) {
            String line;
            int lineNumber = 1;

            while (!foundFlag.get() && (line = reader.readLine()) != null) {
                if (line.trim().equalsIgnoreCase(targetName.trim())) {
                    resultRef.set(SearchResult.found(file.getFileName().toString(), lineNumber, line));
                    foundFlag.set(true);
                    return;
                }

                lineNumber++;
            }
        } catch (IOException e) {
            throw new IOException("Erro de leitura no arquivo " + file.getFileName() + ": " + e.getMessage(), e);
        }
    }

    private void cancelPendingTasks(List<Future<?>> futures) {
        for (Future<?> future : futures) {
            if (!future.isDone()) {
                future.cancel(true);
            }
        }
    }

    private IOException asIOException(Throwable cause) {
        if (cause instanceof IOException) {
            return (IOException) cause;
        }

        return new IOException("Erro durante a busca: " + cause.getMessage(), cause);
    }
}
