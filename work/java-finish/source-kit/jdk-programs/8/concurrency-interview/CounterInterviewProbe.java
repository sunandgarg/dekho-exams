import java.util.concurrent.atomic.AtomicInteger;

public class CounterInterviewProbe {
    public static void main(String[] args) throws InterruptedException {
        AtomicInteger accepted = new AtomicInteger();
        Runnable worker = () -> {
            for (int receipt = 0; receipt < 1000; receipt++) accepted.incrementAndGet();
        };
        Thread first = new Thread(worker); Thread second = new Thread(worker);
        first.start(); second.start(); first.join(); second.join();
        System.out.println(accepted.get());
    }
}
