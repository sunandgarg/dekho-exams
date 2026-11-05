package in.aitrove.contracts;
import io.micrometer.core.instrument.MeterRegistry;
public class BoundedImportMetrics {
    public enum Outcome { ACCEPTED, REJECTED }
    private final MeterRegistry registry;
    public BoundedImportMetrics(MeterRegistry registry) { this.registry=registry; }
    public void record(Outcome outcome) {
        registry.counter("receipt.import.records", "outcome",outcome.name()).increment();
    }
}
