import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

public class ShipmentKeyLookup {
    static final class ShipmentKey {
        private final String carrier;
        private final String tracking;
        ShipmentKey(String carrier, String tracking) {
            this.carrier = Objects.requireNonNull(carrier);
            this.tracking = Objects.requireNonNull(tracking);
        }
        @Override
        public boolean equals(Object candidate) {
            if (this == candidate) return true;
            if (!(candidate instanceof ShipmentKey)) return false;
            ShipmentKey other = (ShipmentKey) candidate;
            return carrier.equals(other.carrier) && tracking.equals(other.tracking);
        }
        @Override
        public int hashCode() {
            return 31 * carrier.hashCode() + tracking.hashCode();
        }
    }
    public static void main(String[] args) {
        Map<ShipmentKey, String> state = new HashMap<>();
        state.put(new ShipmentKey("DX", "track-309"), "in-transit");
        System.out.println(state.get(new ShipmentKey("DX", "track-309")));
        System.out.println(state.size());
    }
}
