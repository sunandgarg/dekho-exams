import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class DeliveryArgumentOwnership {
    static void appendThenRebind(List<String> events) {
        events.add("packed");
        events = new ArrayList<>();
        events.add("local-only");
    }
    public static void main(String[] args) {
        List<String> deliveryEvents = new ArrayList<>(Arrays.asList("received"));
        appendThenRebind(deliveryEvents);
        System.out.println(deliveryEvents);
    }
}
