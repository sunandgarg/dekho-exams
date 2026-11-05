import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class TypedBatchTransfer {
    static void transfer(List<? extends Integer> source, List<? super Integer> destination) {
        for (Integer shipmentCount : source) {
            destination.add(shipmentCount);
        }
    }
    public static void main(String[] args) {
        List<Integer> dailyCounts = Arrays.asList(4, 7, 2);
        List<Number> report = new ArrayList<>();
        transfer(dailyCounts, report);
        System.out.println(report);
    }
}
