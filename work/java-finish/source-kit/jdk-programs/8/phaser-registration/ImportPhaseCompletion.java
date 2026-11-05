import java.util.concurrent.Phaser;
import java.util.concurrent.atomic.AtomicInteger;
public class ImportPhaseCompletion {
    public static void main(String[] args) throws Exception {
        Phaser phase = new Phaser(3);
        AtomicInteger completed = new AtomicInteger();
        Runnable task = () -> { try { completed.incrementAndGet(); } finally { phase.arriveAndDeregister(); } };
        Thread first = new Thread(task), second = new Thread(task);
        first.start(); second.start();
        phase.arriveAndAwaitAdvance();
        first.join(); second.join();
        System.out.println("completed=" + completed.get());
        System.out.println("remaining=" + phase.getRegisteredParties());
        phase.arriveAndDeregister();
        System.out.println("terminated=" + phase.isTerminated());
    }
}
