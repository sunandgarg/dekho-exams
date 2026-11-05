import java.util.LinkedHashMap;
import java.util.Map;

public class AccessOrderedCache {
    public static void main(String[] args) {
        Map<String, String> cache = new LinkedHashMap<String, String>(4, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
                return size() > 2;
            }
        };
        cache.put("account-a", "active");
        cache.put("account-b", "paused");
        cache.get("account-a");
        cache.put("account-c", "active");
        System.out.println(cache.keySet());
        System.out.println("account-b=" + cache.containsKey("account-b"));
    }
}
