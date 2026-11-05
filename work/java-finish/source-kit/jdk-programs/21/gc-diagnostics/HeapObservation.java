import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;

public class HeapObservation {
    private static byte[] retained;
    public static void main(String[] args) {
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        long before = memory.getHeapMemoryUsage().getUsed();
        retained = new byte[256 * 1024];
        long after = memory.getHeapMemoryUsage().getUsed();
        System.out.println("beforeBytes=" + before);
        System.out.println("afterBytes=" + after);
        System.out.println("retainedBytes=" + retained.length);
        retained = null;
    }
}
