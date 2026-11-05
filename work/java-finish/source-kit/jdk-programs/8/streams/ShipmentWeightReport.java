import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class ShipmentWeightReport {
    public static void main(String[] args) {
        List<Integer> weights = Arrays.asList(12, -1, 8, 42, 5);
        long acceptedTotal = weights.stream()
                .filter(weight -> weight > 0 && weight <= 30)
                .mapToLong(Integer::longValue)
                .sum();
        List<Integer> accepted = weights.stream()
                .filter(weight -> weight > 0 && weight <= 30)
                .collect(Collectors.toList());
        System.out.println("total=" + acceptedTotal);
        System.out.println(accepted);
    }
}
