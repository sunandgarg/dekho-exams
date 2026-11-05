import java.util.Arrays;
import java.util.Spliterator;
import java.util.concurrent.atomic.AtomicInteger;
public class PartitionedReceiptAmounts {
    public static void main(String[] args) {
        Spliterator<Integer> remaining = Arrays.asList(12, 18, 25, 45).spliterator();
        Spliterator<Integer> prefix = remaining.trySplit();
        AtomicInteger total = new AtomicInteger();
        if (prefix != null) prefix.forEachRemaining(total::addAndGet);
        remaining.forEachRemaining(total::addAndGet);
        System.out.println(total.get());
        System.out.println(remaining.hasCharacteristics(Spliterator.ORDERED));
    }
}
