import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
public class ReceiptStreamLifetime {
    public static void main(String[] args) {
        AtomicInteger closed = new AtomicInteger();
        try (Stream<String> receiptIds = Stream.of("R-21", "R-22").onClose(closed::incrementAndGet)) {
            System.out.println(receiptIds.count());
            System.out.println("before close=" + closed.get());
        }
        System.out.println("after close=" + closed.get());
    }
}
