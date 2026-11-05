import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
public class ImportAdmission {
    public static void main(String[] args) throws Exception {
        CountDownLatch release = new CountDownLatch(1);
        ThreadPoolExecutor worker = new ThreadPoolExecutor(1, 1, 0, TimeUnit.SECONDS,
            new ArrayBlockingQueue<Runnable>(1), new ThreadPoolExecutor.AbortPolicy());
        try {
            worker.execute(() -> { try { release.await(); } catch (InterruptedException stop) { Thread.currentThread().interrupt(); } });
            worker.execute(() -> {});
            try { worker.execute(() -> {}); }
            catch (RejectedExecutionException rejected) { System.out.println("capacity rejected"); }
            System.out.println("queued=" + worker.getQueue().size());
        } finally { release.countDown(); worker.shutdown(); }
        if (!worker.awaitTermination(5, TimeUnit.SECONDS)) throw new AssertionError("worker did not stop");
    }
}
