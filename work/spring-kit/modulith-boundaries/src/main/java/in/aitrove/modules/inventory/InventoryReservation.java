package in.aitrove.modules.inventory;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

@Service
public final class InventoryReservation implements InventoryQueries {
    private final ConcurrentHashMap<String, Integer> available = new ConcurrentHashMap<>();
    private final ApplicationEventPublisher publisher;

    public InventoryReservation(ApplicationEventPublisher publisher) {
        this.publisher = publisher;
    }

    public boolean reserve(String receiptId, int units) {
        if (receiptId == null || receiptId.isBlank() || units <= 0) return false;
        AtomicBoolean accepted = new AtomicBoolean();
        int remaining = available.compute(receiptId, (key, current) -> {
            int before = current == null ? 47 : current;
            if (units > before) return before;
            accepted.set(true);
            return before - units;
        });
        if (!accepted.get()) return false;
        publisher.publishEvent(new ReceiptReserved(receiptId, units, remaining));
        return true;
    }

    public int availableUnits(String receiptId) {
        return available.getOrDefault(receiptId, 47);
    }
}
