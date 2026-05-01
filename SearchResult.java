public class SearchResult {
    private final boolean found;
    private final String fileName;
    private final int lineNumber;
    private final String lineContent;

    private SearchResult(boolean found, String fileName, int lineNumber, String lineContent) {
        this.found = found;
        this.fileName = fileName;
        this.lineNumber = lineNumber;
        this.lineContent = lineContent;
    }

    public static SearchResult found(String fileName, int lineNumber, String lineContent) {
        return new SearchResult(true, fileName, lineNumber, lineContent);
    }

    public static SearchResult notFound() {
        return new SearchResult(false, null, -1, null);
    }

    public boolean isFound() {
        return found;
    }

    public String getFileName() {
        return fileName;
    }

    public int getLineNumber() {
        return lineNumber;
    }

    public String getLineContent() {
        return lineContent;
    }
}
