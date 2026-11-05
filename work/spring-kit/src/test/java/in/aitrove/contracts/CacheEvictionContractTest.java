package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.context.annotation.*;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.cache.CacheManager;
public class CacheEvictionContractTest {
    @Configuration @EnableCaching static class Config {
        @Bean CacheManager cacheManager(){return new ConcurrentMapCacheManager("contractReceipts");}
        @Bean ReceiptCacheEdits receipts(){return new ReceiptCacheEdits();}
    }
    @Test void proxiedEditEvictsOnlyTheMatchingTenantKey(){
        try(var context=new AnnotationConfigApplicationContext(Config.class)) {
            var service=context.getBean(ReceiptCacheEdits.class);
            var first=new ReceiptCacheEdits.Key("tenant-a",7);var second=new ReceiptCacheEdits.Key("tenant-b",7);
            service.replace(first,"a-original");service.replace(second,"b-original");
            assertEquals("a-original",service.read(first));assertEquals("b-original",service.read(second));
            service.replace(first,"a-new");assertEquals("a-new",service.read(first));assertEquals("b-original",service.read(second));
        }
    }
}
