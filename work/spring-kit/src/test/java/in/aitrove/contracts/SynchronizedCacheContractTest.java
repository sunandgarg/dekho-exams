package in.aitrove.contracts;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import static org.junit.jupiter.api.Assertions.*;

public class SynchronizedCacheContractTest {
    static class ReceiptLookup {
        private final AtomicInteger loads = new AtomicInteger();
        @Cacheable(cacheNames = "receiptLookup", sync = true)
        public String find(String receiptId) {
            loads.incrementAndGet();
            return "receipt:" + receiptId;
        }
        int loadCount() { return loads.get(); }
    }

    @Configuration @EnableCaching
    static class Config {
        @Bean CacheManager cacheManager() { return new ConcurrentMapCacheManager("receiptLookup"); }
        @Bean ReceiptLookup receiptLookup() { return new ReceiptLookup(); }
    }

    @Test void concurrentCallsForOneKeyUseOneLocalLoader() throws Exception {
        try (var context = new AnnotationConfigApplicationContext(Config.class);
             var executor = Executors.newFixedThreadPool(2)) {
            var lookup = context.getBean(ReceiptLookup.class);
            var start = new CountDownLatch(1);
            var first = executor.submit(() -> { start.await(); return lookup.find("R-41"); });
            var second = executor.submit(() -> { start.await(); return lookup.find("R-41"); });
            start.countDown();
            assertEquals("receipt:R-41", first.get(3, TimeUnit.SECONDS));
            assertEquals("receipt:R-41", second.get(3, TimeUnit.SECONDS));
            assertEquals(1, lookup.loadCount());
            assertEquals("receipt:R-42", lookup.find("R-42"));
            assertEquals(2, lookup.loadCount());
        }
    }
}
