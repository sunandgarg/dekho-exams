import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

public class QuantityPricing {
    public static void main(String[] args) {
        NavigableMap<Integer, Integer> centsPerUnit = new TreeMap<>();
        centsPerUnit.put(1, 240);
        centsPerUnit.put(10, 220);
        centsPerUnit.put(50, 195);
        int quantity = 24;
        Map.Entry<Integer, Integer> price = centsPerUnit.floorEntry(quantity);
        if (price == null) {
            throw new IllegalArgumentException("Quantity must meet a threshold");
        }
        System.out.println("unitCents=" + price.getValue());
        System.out.println("thresholds=" + centsPerUnit.subMap(10, true, 50, false).keySet());
    }
}
