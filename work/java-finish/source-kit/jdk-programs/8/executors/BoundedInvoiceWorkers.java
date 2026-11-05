import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public class BoundedInvoiceWorkers {
    public static void main(String[] args) throws Exception {
        ThreadPoolExecutor workers = new ThreadPoolExecutor(
                2, 2, 0L, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<Runnable>(4), new ThreadPoolExecutor.AbortPolicy());
        try {
            Future<Integer> invoiceTotal = workers.submit(() -> 17 + 23);
            System.out.println(invoiceTotal.get());
        } finally {
            workers.shutdown();
            try {
                if (!workers.awaitTermination(2, TimeUnit.SECONDS)) workers.shutdownNow();
            } catch (InterruptedException cancelledWait) {
                workers.shutdownNow();
                Thread.currentThread().interrupt();
            }
        }
    }
}
