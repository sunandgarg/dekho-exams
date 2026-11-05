package in.aitrove.learning;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class ReceiptCacheBoundary {
    public static class Lookup {
        final AtomicInteger calls = new AtomicInteger();
        @Cacheable(cacheNames="receipts", key="#p0 + ':' + #p1")
        public String read(String tenant, long receiptId) { calls.incrementAndGet(); return tenant + ":" + receiptId; }
    }
    @Configuration(proxyBeanMethods=false) @EnableCaching
    public static class Config {
        @Bean ConcurrentMapCacheManager caches() { return new ConcurrentMapCacheManager("receipts"); }
        @Bean Lookup lookup() { return new Lookup(); }
    }
    public static void main(String[] args) {
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(Config.class)) {
            Lookup lookup = context.getBean(Lookup.class);
            System.out.println(lookup.read("tenant-a", 7));
            System.out.println(lookup.read("tenant-a", 7));
            System.out.println(lookup.read("tenant-b", 7));
        }
    }
}
