import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
public class DepotRequestCounts {
    public static void main(String[] args) throws Exception {
        ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();
        ExecutorService workers = Executors.newFixedThreadPool(2);
        try {
            Runnable batch = () -> {
                for (int request = 0; request < 400; request++) {
                    counts.merge("DL-01", 1, Integer::sum);
                }
            };
            Future<?> first = workers.submit(batch);
            Future<?> second = workers.submit(batch);
            first.get();
            second.get();
            System.out.println("accepted=" + counts.get("DL-01"));
        } finally {
            workers.shutdown();
        }
    }
}
