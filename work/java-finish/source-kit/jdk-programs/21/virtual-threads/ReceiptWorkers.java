import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;

public class ReceiptWorkers {
    public static void main(String[] args) throws Exception {
        Semaphore downstream = new Semaphore(2);
        List<Future<String>> receipts = new ArrayList<>();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int index = 1; index <= 3; index++) {
                final int receiptId = index;
                receipts.add(executor.submit(() -> {
                    downstream.acquire();
                    try { return "receipt-" + receiptId; }
                    finally { downstream.release(); }
                }));
            }
            for (Future<String> receipt : receipts) System.out.println(receipt.get());
        }
    }
}
