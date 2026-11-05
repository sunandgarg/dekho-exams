import java.util.*;
public class DocumentLruCache extends LinkedHashMap<String,String> {
    private final int capacity;
    DocumentLruCache(int capacity) {
        super(16,0.75f,true);
        if(capacity<1)throw new IllegalArgumentException("capacity");
        this.capacity=capacity;
    }
    protected boolean removeEldestEntry(Map.Entry<String,String> eldest){return size()>capacity;}
    public static void main(String[] args) {
        DocumentLruCache cache=new DocumentLruCache(2);
        cache.put("invoice","I");cache.put("receipt","R");cache.get("invoice");cache.put("statement","S");
        System.out.println(cache.keySet());System.out.println(cache.containsKey("receipt"));
        try{new DocumentLruCache(0);}catch(IllegalArgumentException rejected){System.out.println("capacity rejected");}
    }
}
