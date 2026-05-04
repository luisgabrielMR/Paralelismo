import java.lang.management.ManagementFactory;
import java.net.InetAddress;

public class BenchmarkMetrics {
    private final long wallTimeNs;
    private final long heapUsedBeforeBytes;
    private final long heapUsedAfterBytes;
    private final int availableProcessors;
    private final String javaVersion;
    private final String osName;
    private final String osArch;
    private final String machineName;
    private final boolean processCpuTimeSupported;
    private final Long processCpuTimeNs;
    private final Double cpuUsageApproxPercent;

    public BenchmarkMetrics(
            long wallTimeNs,
            long heapUsedBeforeBytes,
            long heapUsedAfterBytes,
            long processCpuTimeBeforeNs,
            long processCpuTimeAfterNs,
            boolean processCpuTimeSupported
    ) {
        this.wallTimeNs = wallTimeNs;
        this.heapUsedBeforeBytes = heapUsedBeforeBytes;
        this.heapUsedAfterBytes = heapUsedAfterBytes;
        this.availableProcessors = Runtime.getRuntime().availableProcessors();
        this.javaVersion = System.getProperty("java.version");
        this.osName = System.getProperty("os.name");
        this.osArch = System.getProperty("os.arch");
        this.machineName = resolveMachineName();
        this.processCpuTimeSupported = processCpuTimeSupported;

        if (processCpuTimeSupported && processCpuTimeBeforeNs >= 0 && processCpuTimeAfterNs >= processCpuTimeBeforeNs) {
            this.processCpuTimeNs = processCpuTimeAfterNs - processCpuTimeBeforeNs;
            this.cpuUsageApproxPercent = calculateCpuUsage(this.processCpuTimeNs, wallTimeNs, availableProcessors);
        } else {
            this.processCpuTimeNs = null;
            this.cpuUsageApproxPercent = null;
        }
    }

    public static long usedHeapBytes() {
        Runtime runtime = Runtime.getRuntime();
        return runtime.totalMemory() - runtime.freeMemory();
    }

    public static ProcessCpuSnapshot processCpuSnapshot() {
        java.lang.management.OperatingSystemMXBean bean = ManagementFactory.getOperatingSystemMXBean();

        if (bean instanceof com.sun.management.OperatingSystemMXBean) {
            com.sun.management.OperatingSystemMXBean osBean = (com.sun.management.OperatingSystemMXBean) bean;
            long processCpuTimeNs = osBean.getProcessCpuTime();

            if (processCpuTimeNs >= 0) {
                return new ProcessCpuSnapshot(true, processCpuTimeNs);
            }
        }

        return new ProcessCpuSnapshot(false, -1L);
    }

    private static Double calculateCpuUsage(long processCpuTimeNs, long wallTimeNs, int availableProcessors) {
        if (wallTimeNs <= 0 || availableProcessors <= 0) {
            return null;
        }

        return ((double) processCpuTimeNs / wallTimeNs) / availableProcessors * 100.0;
    }

    private static String resolveMachineName() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (Exception e) {
            return "unknown";
        }
    }

    public long getWallTimeNs() {
        return wallTimeNs;
    }

    public double getWallTimeMs() {
        return wallTimeNs / 1_000_000.0;
    }

    public long getHeapUsedBeforeBytes() {
        return heapUsedBeforeBytes;
    }

    public long getHeapUsedAfterBytes() {
        return heapUsedAfterBytes;
    }

    public long getHeapDeltaBytes() {
        return heapUsedAfterBytes - heapUsedBeforeBytes;
    }

    public int getAvailableProcessors() {
        return availableProcessors;
    }

    public String getJavaVersion() {
        return javaVersion;
    }

    public String getOsName() {
        return osName;
    }

    public String getOsArch() {
        return osArch;
    }

    public String getMachineName() {
        return machineName;
    }

    public boolean isProcessCpuTimeSupported() {
        return processCpuTimeSupported;
    }

    public Double getProcessCpuTimeMs() {
        if (processCpuTimeNs == null) {
            return null;
        }

        return processCpuTimeNs / 1_000_000.0;
    }

    public Double getCpuUsageApproxPercent() {
        return cpuUsageApproxPercent;
    }

    public static class ProcessCpuSnapshot {
        private final boolean supported;
        private final long timeNs;

        private ProcessCpuSnapshot(boolean supported, long timeNs) {
            this.supported = supported;
            this.timeNs = timeNs;
        }

        public boolean isSupported() {
            return supported;
        }

        public long getTimeNs() {
            return timeNs;
        }
    }
}
