import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public class ShipmentReportOrder {
    static final class Shipment {
        final int zone;
        final int sequence;
        Shipment(int zone, int sequence) { this.zone = zone; this.sequence = sequence; }
        public String toString() { return zone + ":" + sequence; }
    }
    public static void main(String[] args) {
        List<Shipment> imported = Arrays.asList(new Shipment(2, 7), new Shipment(1, 9), new Shipment(1, 3));
        List<Shipment> sorted = new ArrayList<>(imported);
        sorted.sort(Comparator.comparingInt((Shipment shipment) -> shipment.zone)
                .thenComparingInt(shipment -> shipment.sequence));
        System.out.println(sorted);
        System.out.println(imported);
    }
}
