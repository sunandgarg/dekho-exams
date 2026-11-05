import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
public class RequestContextCleanup {
    static final ThreadLocal<String> REQUEST = new ThreadLocal<>();
    public static void main(String[] args) throws Exception {
        ExecutorService worker = Executors.newSingleThreadExecutor();
        try {
            System.out.println(worker.submit(() -> {
                REQUEST.set("receipt-71");
                try { return REQUEST.get(); }
                finally { REQUEST.remove(); }
            }).get());
            System.out.println(worker.submit(() -> REQUEST.get()).get());
        } finally { worker.shutdownNow(); }
    }
}
