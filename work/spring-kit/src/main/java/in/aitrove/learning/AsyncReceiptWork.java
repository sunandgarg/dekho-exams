package in.aitrove.learning;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.core.task.TaskRejectedException;
public class AsyncReceiptWork {
    public static void main(String[] args) throws Exception {
        ThreadPoolTaskExecutor workers = new ThreadPoolTaskExecutor();
        workers.setCorePoolSize(1); workers.setMaxPoolSize(1); workers.setQueueCapacity(1); workers.initialize();
        CountDownLatch release = new CountDownLatch(1);
        try {
            workers.execute(() -> { try { release.await(); } catch (InterruptedException stop) { Thread.currentThread().interrupt(); } });
            workers.execute(() -> {});
            try { workers.execute(() -> {}); }
            catch (TaskRejectedException rejected) { System.out.println("capacity rejected"); }
        } finally { release.countDown(); workers.shutdown(); }
        if (!workers.getThreadPoolExecutor().awaitTermination(5, TimeUnit.SECONDS)) throw new AssertionError("termination");
    }
}
