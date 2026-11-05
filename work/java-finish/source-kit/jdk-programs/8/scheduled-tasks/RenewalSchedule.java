import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
public class RenewalSchedule {
    public static void main(String[] args) throws Exception {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        try {
            ScheduledFuture<String> renewal = scheduler.schedule(() -> "renewed=R-31", 0, TimeUnit.MILLISECONDS);
            System.out.println(renewal.get(2, TimeUnit.SECONDS));
        } finally {
            scheduler.shutdownNow();
            if (!scheduler.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Worker did not stop");
        }
    }
}
