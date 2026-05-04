import java.util.Locale;

public class BenchmarkFormatter {
    public static String toJson(BenchmarkRunResult runResult) {
        SearchResult result = runResult.getSearchResult();
        BenchmarkMetrics metrics = runResult.getMetrics();
        StringBuilder builder = new StringBuilder();

        builder.append("{\n");
        appendJsonString(builder, "dataset", runResult.getDataset(), true);
        appendJsonString(builder, "strategy", runResult.getStrategy(), true);
        appendJsonNumber(builder, "threadsPerFile", runResult.getThreadsPerFile(), true);
        appendJsonString(builder, "targetName", runResult.getTargetName(), true);
        appendJsonBoolean(builder, "found", result.isFound(), true);
        appendJsonNullableString(builder, "fileName", result.isFound() ? result.getFileName() : null, true);
        appendJsonNullableNumber(builder, "lineNumber", result.isFound() ? result.getLineNumber() : null, true);
        appendJsonNullableString(builder, "lineContent", result.isFound() ? result.getLineContent() : null, true);
        appendJsonNumber(builder, "wallTimeMs", formatDouble(metrics.getWallTimeMs()), true);
        appendJsonNumber(builder, "wallTimeNs", metrics.getWallTimeNs(), true);
        appendJsonBoolean(builder, "processCpuTimeSupported", metrics.isProcessCpuTimeSupported(), true);
        appendJsonNullableNumber(builder, "processCpuTimeMs", formatNullableDouble(metrics.getProcessCpuTimeMs()), true);
        appendJsonNullableNumber(builder, "cpuUsageApproxPercent", formatNullableDouble(metrics.getCpuUsageApproxPercent()), true);
        appendJsonNumber(builder, "heapUsedBeforeBytes", metrics.getHeapUsedBeforeBytes(), true);
        appendJsonNumber(builder, "heapUsedAfterBytes", metrics.getHeapUsedAfterBytes(), true);
        appendJsonNumber(builder, "heapDeltaBytes", metrics.getHeapDeltaBytes(), true);
        appendJsonNumber(builder, "availableProcessors", metrics.getAvailableProcessors(), true);
        appendJsonString(builder, "javaVersion", metrics.getJavaVersion(), true);
        appendJsonString(builder, "osName", metrics.getOsName(), true);
        appendJsonString(builder, "osArch", metrics.getOsArch(), true);
        appendJsonString(builder, "machineName", metrics.getMachineName(), false);
        builder.append("}");

        return builder.toString();
    }

    public static String toCsv(BenchmarkRunResult runResult) {
        SearchResult result = runResult.getSearchResult();
        BenchmarkMetrics metrics = runResult.getMetrics();

        return String.join(",",
                csv(runResult.getDataset()),
                csv(runResult.getStrategy()),
                Integer.toString(runResult.getThreadsPerFile()),
                csv(runResult.getTargetName()),
                Boolean.toString(result.isFound()),
                csv(result.isFound() ? result.getFileName() : ""),
                result.isFound() ? Integer.toString(result.getLineNumber()) : "",
                formatDouble(metrics.getWallTimeMs()),
                Long.toString(metrics.getWallTimeNs()),
                formatCsvNullableDouble(metrics.getProcessCpuTimeMs()),
                formatCsvNullableDouble(metrics.getCpuUsageApproxPercent()),
                Long.toString(metrics.getHeapUsedBeforeBytes()),
                Long.toString(metrics.getHeapUsedAfterBytes()),
                Long.toString(metrics.getHeapDeltaBytes()),
                Integer.toString(metrics.getAvailableProcessors()),
                csv(metrics.getJavaVersion()),
                csv(metrics.getOsName()),
                csv(metrics.getOsArch()),
                csv(metrics.getMachineName())
        );
    }

    private static void appendJsonString(StringBuilder builder, String name, String value, boolean comma) {
        appendJsonName(builder, name);
        builder.append("\"").append(escapeJson(value)).append("\"");
        appendComma(builder, comma);
    }

    private static void appendJsonNullableString(StringBuilder builder, String name, String value, boolean comma) {
        appendJsonName(builder, name);

        if (value == null) {
            builder.append("null");
        } else {
            builder.append("\"").append(escapeJson(value)).append("\"");
        }

        appendComma(builder, comma);
    }

    private static void appendJsonBoolean(StringBuilder builder, String name, boolean value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value);
        appendComma(builder, comma);
    }

    private static void appendJsonNumber(StringBuilder builder, String name, long value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value);
        appendComma(builder, comma);
    }

    private static void appendJsonNumber(StringBuilder builder, String name, int value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value);
        appendComma(builder, comma);
    }

    private static void appendJsonNumber(StringBuilder builder, String name, String value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value);
        appendComma(builder, comma);
    }

    private static void appendJsonNullableNumber(StringBuilder builder, String name, Integer value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value == null ? "null" : value);
        appendComma(builder, comma);
    }

    private static void appendJsonNullableNumber(StringBuilder builder, String name, String value, boolean comma) {
        appendJsonName(builder, name);
        builder.append(value == null ? "null" : value);
        appendComma(builder, comma);
    }

    private static void appendJsonName(StringBuilder builder, String name) {
        builder.append("  \"").append(name).append("\": ");
    }

    private static void appendComma(StringBuilder builder, boolean comma) {
        if (comma) {
            builder.append(",");
        }

        builder.append("\n");
    }

    private static String escapeJson(String value) {
        StringBuilder builder = new StringBuilder();

        for (int index = 0; index < value.length(); index++) {
            char ch = value.charAt(index);

            switch (ch) {
                case '"':
                    builder.append("\\\"");
                    break;
                case '\\':
                    builder.append("\\\\");
                    break;
                case '\b':
                    builder.append("\\b");
                    break;
                case '\f':
                    builder.append("\\f");
                    break;
                case '\n':
                    builder.append("\\n");
                    break;
                case '\r':
                    builder.append("\\r");
                    break;
                case '\t':
                    builder.append("\\t");
                    break;
                default:
                    if (ch < 0x20) {
                        builder.append(String.format("\\u%04x", (int) ch));
                    } else {
                        builder.append(ch);
                    }
            }
        }

        return builder.toString();
    }

    private static String csv(String value) {
        if (value == null) {
            return "";
        }

        boolean needsQuotes = value.contains(",") || value.contains("\"") || value.contains("\n") || value.contains("\r");
        String escaped = value.replace("\"", "\"\"");

        if (needsQuotes) {
            return "\"" + escaped + "\"";
        }

        return escaped;
    }

    private static String formatDouble(double value) {
        return String.format(Locale.US, "%.6f", value);
    }

    private static String formatNullableDouble(Double value) {
        if (value == null) {
            return null;
        }

        return formatDouble(value);
    }

    private static String formatCsvNullableDouble(Double value) {
        if (value == null) {
            return "";
        }

        return formatDouble(value);
    }
}
