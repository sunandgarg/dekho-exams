package in.aitrove.learning;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;
@Service
public class ReceiptStore {
    public record Receipt(long id, int amountMinor) {}
    private final Map<Long,Receipt> receipts = new LinkedHashMap<>();
    private long nextId = 1;
    public synchronized Receipt create(int amountMinor) {
        if (amountMinor <= 0) throw new IllegalArgumentException("amount");
        Receipt receipt = new Receipt(nextId++, amountMinor); receipts.put(receipt.id(), receipt); return receipt;
    }
    public synchronized Optional<Receipt> find(long id) { return Optional.ofNullable(receipts.get(id)); }
    public synchronized List<Receipt> page(int offset, int limit) {
        if (offset < 0 || limit < 1 || limit > 100) throw new IllegalArgumentException("page");
        List<Receipt> snapshot = new ArrayList<>(receipts.values());
        int start = Math.min(offset, snapshot.size());
        return List.copyOf(snapshot.subList(start, start + Math.min(limit, snapshot.size() - start)));
    }
}
