import java.util.Collections;
import java.util.Map;
import java.util.TreeMap;

public class StockLedgerProject {
    static final class Ledger {
        private final Map<String, Integer> quantities = new TreeMap<>();
        private void validate(String item, int units) {
            if (item == null || item.trim().isEmpty() || units <= 0) {
                throw new IllegalArgumentException("Item and positive units required");
            }
        }
        void receive(String item, int units) {
            validate(item, units);
            int updated = Math.addExact(quantities.getOrDefault(item, 0), units);
            quantities.put(item, updated);
        }
        void dispatch(String item, int units) {
            validate(item, units);
            int available = quantities.getOrDefault(item, 0);
            if (units > available) throw new IllegalArgumentException("Insufficient stock");
            quantities.put(item, available - units);
        }
        Map<String, Integer> snapshot() {
            return Collections.unmodifiableMap(new TreeMap<>(quantities));
        }
    }
    public static void main(String[] args) {
        Ledger ledger = new Ledger();
        ledger.receive("packing-tape", 10); ledger.dispatch("packing-tape", 3);
        Map<String, Integer> saved = ledger.snapshot();
        try { ledger.dispatch("packing-tape", 8); }
        catch (IllegalArgumentException expected) { System.out.println("rejected"); }
        ledger.receive("packing-tape", 2);
        System.out.println("saved=" + saved);
        System.out.println("current=" + ledger.snapshot());
    }
}
