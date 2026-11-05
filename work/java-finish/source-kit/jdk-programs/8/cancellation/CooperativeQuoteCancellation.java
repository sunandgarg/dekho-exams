import java.util.concurrent.*;
public class CooperativeQuoteCancellation {
    public static void main(String[] args) throws Exception {
        ExecutorService workers = Executors.newSingleThreadExecutor();
        CountDownLatch entered = new CountDownLatch(1), exited = new CountDownLatch(1);
        CountDownLatch neverReleased = new CountDownLatch(1);
        try {
            Future<?> task = workers.submit(() -> {
                entered.countDown();
                try { neverReleased.await(); }
                catch (InterruptedException cancelled) { Thread.currentThread().interrupt(); }
                finally { exited.countDown(); }
            });
            if (!entered.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("Not admitted");
            System.out.println(task.cancel(true));
            if (!exited.await(2, TimeUnit.SECONDS)) throw new IllegalStateException("Worker did not exit");
            System.out.println(task.isCancelled());
            System.out.println("Worker exited");
        } finally {
            workers.shutdownNow();
            if (!workers.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Pool did not stop");
        }
    }
}
