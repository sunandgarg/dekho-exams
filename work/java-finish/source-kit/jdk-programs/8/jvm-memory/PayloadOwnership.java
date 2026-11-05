import java.util.Arrays;

public class PayloadOwnership {
    static final class PayloadStore {
        private final byte[] payload;
        PayloadStore(byte[] payload) { this.payload = Arrays.copyOf(payload, payload.length); }
        byte[] snapshot() { return Arrays.copyOf(payload, payload.length); }
    }
    public static void main(String[] args) {
        byte[] imported = {10, 20, 30};
        PayloadStore store = new PayloadStore(imported);
        imported[0] = 99;
        byte[] reader = store.snapshot();
        reader[1] = 88;
        System.out.println(Arrays.toString(store.snapshot()));
    }
}
