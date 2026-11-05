import java.util.concurrent.ConcurrentSkipListMap;
import java.util.concurrent.ConcurrentNavigableMap;
public class DueJobBoard {
    public static void main(String[] args) {
        ConcurrentSkipListMap<Integer, String> jobs = new ConcurrentSkipListMap<>();
        jobs.put(30, "dispatch-30"); jobs.put(10, "dispatch-10"); jobs.put(20, "dispatch-20");
        System.out.println(jobs.ceilingKey(15));
        ConcurrentNavigableMap<Integer, String> early = jobs.headMap(25, false);
        System.out.println(early.keySet());
        System.out.println(jobs.remove(20, "dispatch-20"));
        System.out.println(early.keySet());
    }
}
