import java.util.concurrent.atomic.AtomicInteger;
public class AdmissionGate {
    private final AtomicInteger inFlight = new AtomicInteger();
    private final int limit;
    AdmissionGate(int limit) {
        if (limit < 1) throw new IllegalArgumentException("Positive limit required");
        this.limit = limit;
    }
    boolean reserve() {
        for (;;) {
            int observed = inFlight.get();
            if (observed >= limit) return false;
            if (inFlight.compareAndSet(observed, observed + 1)) return true;
        }
    }
    void release() {
        for (;;) {
            int observed = inFlight.get();
            if (observed == 0) throw new IllegalStateException("No reservation");
            if (inFlight.compareAndSet(observed, observed - 1)) return;
        }
    }
    public static void main(String[] args) {
        AdmissionGate gate = new AdmissionGate(3);
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        System.out.println(gate.reserve());
        gate.release();
        System.out.println(gate.reserve());
    }
}
