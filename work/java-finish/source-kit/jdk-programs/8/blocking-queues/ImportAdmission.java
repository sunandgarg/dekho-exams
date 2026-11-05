import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
public class ImportAdmission {
    public static void main(String[] args) {
        BlockingQueue<String> jobs = new ArrayBlockingQueue<>(2);
        System.out.println(jobs.offer("manifest-41"));
        System.out.println(jobs.offer("manifest-42"));
        System.out.println(jobs.offer("manifest-43"));
        System.out.println("processing=" + jobs.poll());
        System.out.println(jobs.offer("manifest-43"));
        System.out.println("queued=" + jobs.size());
    }
}
