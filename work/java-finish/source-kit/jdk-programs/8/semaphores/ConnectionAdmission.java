import java.util.concurrent.Semaphore;
public class ConnectionAdmission {
    public static void main(String[] args) {
        Semaphore permits = new Semaphore(2);
        boolean first = permits.tryAcquire();
        boolean second = permits.tryAcquire();
        System.out.println(first);
        System.out.println(second);
        System.out.println(permits.tryAcquire());
        if (first) permits.release();
        if (second) permits.release();
        System.out.println(permits.availablePermits());
    }
}
