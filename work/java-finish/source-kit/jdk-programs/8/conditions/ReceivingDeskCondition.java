import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;
public class ReceivingDeskCondition {
    final ReentrantLock lock = new ReentrantLock();
    final Condition available = lock.newCondition();
    int parcels;
    void receive() {
        lock.lock();
        try { parcels++; available.signal(); }
        finally { lock.unlock(); }
    }
    boolean take(long budgetNanos) throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (parcels == 0) {
                if (budgetNanos <= 0) return false;
                budgetNanos = available.awaitNanos(budgetNanos);
            }
            parcels--; return true;
        } finally { lock.unlock(); }
    }
    public static void main(String[] args) throws Exception {
        ReceivingDeskCondition desk = new ReceivingDeskCondition();
        System.out.println(desk.take(0));
        desk.receive();
        System.out.println(desk.take(0));
        System.out.println(desk.take(0));
    }
}
