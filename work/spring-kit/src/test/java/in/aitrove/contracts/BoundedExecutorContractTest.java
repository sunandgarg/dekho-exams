package in.aitrove.contracts;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;
import org.springframework.core.task.TaskRejectedException;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import static org.junit.jupiter.api.Assertions.*;

public class BoundedExecutorContractTest {
    @Test void thirdTaskIsRejectedWhileOneRunsAndOneWaits() throws Exception {
        var executor = new ThreadPoolTaskExecutor();
        executor.setThreadNamePrefix("receipt-dispatch-");
        executor.setCorePoolSize(1);
        executor.setMaxPoolSize(1);
        executor.setQueueCapacity(1);
        executor.initialize();
        var running = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        try {
            Future<?> first = executor.submit(() -> {
                running.countDown();
                try {
                    if (!release.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("test release timed out");
                } catch (InterruptedException interrupted) {
                    Thread.currentThread().interrupt();
                    throw new IllegalStateException(interrupted);
                }
            });
            assertTrue(running.await(5, TimeUnit.SECONDS));
            Future<?> second = executor.submit(() -> {});
            assertEquals(1, executor.getQueueSize());
            assertThrows(TaskRejectedException.class, () -> executor.submit(() -> {}));
            release.countDown();
            first.get(5, TimeUnit.SECONDS);
            second.get(5, TimeUnit.SECONDS);
        } finally {
            release.countDown();
            executor.shutdown();
        }
    }
}
