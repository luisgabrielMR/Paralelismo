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

public class MultiThreadPerFileSearch implements SearchStrategy {
    private final int threadsPerFile;

    public MultiThreadPerFileSearch(int threadsPerFile) {
        if (threadsPerFile < 1) {
            throw new IllegalArgumentException("A quantidade de Threads por arquivo deve ser maior que zero.");
        }

        this.threadsPerFile = threadsPerFile;
    }

    @Override
    public SearchResult search(Path datasetPath, String targetName) throws IOException {
        List<Path> files = DatasetUtils.listTxtFiles(datasetPath);
        ExecutorService executor = Executors.newFixedThreadPool(threadsPerFile);
        AtomicBoolean foundFlag = new AtomicBoolean(false);
        AtomicReference<SearchResult> resultRef = new AtomicReference<>(SearchResult.notFound());

        try {
            for (Path file : files) {
                if (foundFlag.get()) {
                    break;
                }

                List<String> lines = readAllLines(file);
                List<Future<?>> futures = submitBlockTasks(executor, file, lines, targetName, foundFlag, resultRef);
                waitForTasks(futures);
            }

            return resultRef.get();
        } finally {
            executor.shutdownNow();
        }
    }

    @Override
    public String getName() {
        return "N Threads por arquivo (N = " + threadsPerFile + ")";
    }

    private List<String> readAllLines(Path file) throws IOException {
        try {
            return Files.readAllLines(file);
        } catch (IOException e) {
            throw new IOException("Erro de leitura no arquivo " + file.getFileName() + ": " + e.getMessage(), e);
        }
    }

    private List<Future<?>> submitBlockTasks(
            ExecutorService executor,
            Path file,
            List<String> lines,
            String targetName,
            AtomicBoolean foundFlag,
            AtomicReference<SearchResult> resultRef
    ) {
        List<Future<?>> futures = new ArrayList<>();

        if (lines.isEmpty()) {
            return futures;
        }

        int taskCount = Math.min(threadsPerFile, lines.size());
        int blockSize = (int) Math.ceil((double) lines.size() / taskCount);

        for (int startIndex = 0; startIndex < lines.size(); startIndex += blockSize) {
            int endIndex = Math.min(startIndex + blockSize, lines.size());
            final int blockStartIndex = startIndex;
            final int blockEndIndex = endIndex;
            futures.add(executor.submit(() ->
                    searchBlock(file, lines, blockStartIndex, blockEndIndex, targetName, foundFlag, resultRef)));
        }

        return futures;
    }

    private void searchBlock(
            Path file,
            List<String> lines,
            int startIndex,
            int endIndex,
            String targetName,
            AtomicBoolean foundFlag,
            AtomicReference<SearchResult> resultRef
    ) {
        for (int index = startIndex; index < endIndex && !foundFlag.get(); index++) {
            String line = lines.get(index);

            if (line.trim().equalsIgnoreCase(targetName.trim())) {
                int lineNumber = index + 1;
                resultRef.set(SearchResult.found(file.getFileName().toString(), lineNumber, line));
                foundFlag.set(true);
                return;
            }
        }
    }

    private void waitForTasks(List<Future<?>> futures) throws IOException {
        for (Future<?> future : futures) {
            try {
                future.get();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                cancelPendingTasks(futures);
                throw new IOException("A busca foi interrompida.", e);
            } catch (ExecutionException e) {
                cancelPendingTasks(futures);
                throw new IOException("Erro durante a busca: " + e.getCause().getMessage(), e.getCause());
            }
        }

        cancelPendingTasks(futures);
    }

    private void cancelPendingTasks(List<Future<?>> futures) {
        for (Future<?> future : futures) {
            if (!future.isDone()) {
                future.cancel(true);
            }
        }
    }
}
