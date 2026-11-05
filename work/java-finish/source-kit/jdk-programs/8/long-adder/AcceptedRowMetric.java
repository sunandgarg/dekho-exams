import java.util.concurrent.atomic.LongAdder;
public class AcceptedRowMetric {
    public static void main(String[] args) throws Exception {
        LongAdder accepted = new LongAdder();
        Thread[] writers = new Thread[4];
        for (int index=0; index<writers.length; index++) {
            writers[index] = new Thread(() -> { for (int row=0; row<750; row++) accepted.increment(); });
            writers[index].start();
        }
        for (Thread writer : writers) writer.join();
        System.out.println(accepted.sum());
        System.out.println(accepted.sumThenReset());
        System.out.println(accepted.sum());
    }
}
