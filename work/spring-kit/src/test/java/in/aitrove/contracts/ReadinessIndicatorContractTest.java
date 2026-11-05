package in.aitrove.contracts;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.BooleanSupplier;

import org.junit.jupiter.api.Test;
import org.springframework.boot.health.contributor.Health;
import org.springframework.boot.health.contributor.HealthIndicator;
import org.springframework.boot.health.contributor.Status;

import static org.junit.jupiter.api.Assertions.*;

public class ReadinessIndicatorContractTest {
    static class ReceiptStoreIndicator implements HealthIndicator {
        private final BooleanSupplier available;
        ReceiptStoreIndicator(BooleanSupplier available) { this.available = available; }
        @Override public Health health() {
            return available.getAsBoolean() ? Health.up().build() : Health.down().build();
        }
    }

    @Test void localDependencyStateChangesTheIndicatorResult() {
        var available = new AtomicBoolean(true);
        var indicator = new ReceiptStoreIndicator(available::get);
        assertEquals(Status.UP, indicator.health().getStatus());
        available.set(false);
        assertEquals(Status.DOWN, indicator.health().getStatus());
    }
}
