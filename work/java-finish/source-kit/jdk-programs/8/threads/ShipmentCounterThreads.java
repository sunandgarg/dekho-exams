public class ShipmentCounterThreads {
    static final class Counter {
        private int completed;
        synchronized void increment() { completed++; }
        synchronized int value() { return completed; }
    }
    public static void main(String[] args) throws InterruptedException {
        Counter counter = new Counter();
        Runnable batch = () -> {
            for (int shipment = 0; shipment < 1000; shipment++) counter.increment();
        };
        Thread first = new Thread(batch, "shipment-first");
        Thread second = new Thread(batch, "shipment-second");
        first.start();
        second.start();
        first.join();
        second.join();
        System.out.println(counter.value());
    }
}
