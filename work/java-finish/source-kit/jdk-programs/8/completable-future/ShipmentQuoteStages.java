import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
public class ShipmentQuoteStages {
    public static void main(String[] args) {
        ExecutorService workers = Executors.newFixedThreadPool(2);
        try {
            CompletableFuture<Integer> rate = CompletableFuture.supplyAsync(() -> 120, workers);
            CompletableFuture<Integer> insurance = CompletableFuture.supplyAsync(() -> 30, workers);
            int total = rate.thenCombine(insurance, Integer::sum).join();
            System.out.println("quote=" + total);
            CompletableFuture<String> tracking = new CompletableFuture<>();
            tracking.completeExceptionally(new IllegalStateException("Carrier unavailable"));
            System.out.println(tracking.exceptionally(failure -> "unavailable").join());
        } finally {
            workers.shutdown();
        }
    }
}
