public class BenchmarkRunResult {
    private final String dataset;
    private final String strategy;
    private final int threadsPerFile;
    private final String targetName;
    private final SearchResult searchResult;
    private final BenchmarkMetrics metrics;

    public BenchmarkRunResult(
            String dataset,
            String strategy,
            int threadsPerFile,
            String targetName,
            SearchResult searchResult,
            BenchmarkMetrics metrics
    ) {
        this.dataset = dataset;
        this.strategy = strategy;
        this.threadsPerFile = threadsPerFile;
        this.targetName = targetName;
        this.searchResult = searchResult;
        this.metrics = metrics;
    }

    public String getDataset() {
        return dataset;
    }

    public String getStrategy() {
        return strategy;
    }

    public int getThreadsPerFile() {
        return threadsPerFile;
    }

    public String getTargetName() {
        return targetName;
    }

    public SearchResult getSearchResult() {
        return searchResult;
    }

    public BenchmarkMetrics getMetrics() {
        return metrics;
    }
}
