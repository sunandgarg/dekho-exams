import java.util.ArrayList;
import java.util.List;

public class ReceiptBatch {
    public static void main(String[] args) {
        List<String> receiptIds = new ArrayList<>();
        receiptIds.add("R-104");
        receiptIds.add("R-105");
        receiptIds.set(0, "R-104-corrected");
        System.out.println(receiptIds.get(0));
    }
}
