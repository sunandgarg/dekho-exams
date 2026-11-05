package in.aitrove.contracts;
import java.util.concurrent.*;
import org.springframework.cache.annotation.*;
public class ReceiptCacheEdits {
    public record Key(String tenant,long id) {}
    private final ConcurrentMap<Key,String> data=new ConcurrentHashMap<>();
    @Cacheable(cacheNames="contractReceipts",key="#key")
    public String read(Key key){return data.getOrDefault(key,"missing");}
    @CacheEvict(cacheNames="contractReceipts",key="#key")
    public void replace(Key key,String value){data.put(key,value);}
}
