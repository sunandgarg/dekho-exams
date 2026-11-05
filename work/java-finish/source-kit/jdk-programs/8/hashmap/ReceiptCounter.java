import java.util.HashMap;
import java.util.Map;

public class ReceiptCounter {
    public static void main(String[] args) {
        Map<String, Integer> counts = new HashMap<>();
        String[] statuses = {"paid", "declined", "paid", "pending", "paid"};
        for (String status : statuses) {
            counts.merge(status, 1, Integer::sum);
        }
        System.out.println("paid=" + counts.getOrDefault("paid", 0));
        System.out.println("refunded=" + counts.getOrDefault("refunded", 0));
        System.out.println("statuses=" + counts.size());
    }
}
