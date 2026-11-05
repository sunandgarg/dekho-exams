import java.util.concurrent.locks.ReentrantLock;
public class StockReservations {
    private final ReentrantLock lock = new ReentrantLock();
    private int available = 12;
    private int reserved;
    boolean reserve(int quantity) {
        if (quantity <= 0) throw new IllegalArgumentException("Positive quantity required");
        lock.lock();
        try {
            if (quantity > available) return false;
            available -= quantity;
            reserved += quantity;
            return true;
        } finally {
            lock.unlock();
        }
    }
    String snapshot() {
        lock.lock();
        try {
            return "available=" + available + ", reserved=" + reserved;
        } finally {
            lock.unlock();
        }
    }
    public static void main(String[] args) {
        StockReservations stock = new StockReservations();
        System.out.println(stock.reserve(5));
        System.out.println(stock.reserve(20));
        System.out.println(stock.snapshot());
    }
}
