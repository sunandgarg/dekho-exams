import java.util.ArrayList;
import java.util.List;

public class ReceiptBatches {
    record ReceiptBatch(String id, List<String> receiptIds) {
        ReceiptBatch {
            if (id == null || id.isBlank()) throw new IllegalArgumentException("Batch ID required");
            receiptIds = List.copyOf(receiptIds);
        }
    }
    public static void main(String[] args) {
        List<String> imported = new ArrayList<>(List.of("r-41", "r-52"));
        ReceiptBatch batch = new ReceiptBatch("batch-8", imported);
        imported.clear();
        System.out.println(batch.receiptIds().size());
        System.out.println(batch.equals(new ReceiptBatch("batch-8", List.of("r-41", "r-52"))));
    }
}
