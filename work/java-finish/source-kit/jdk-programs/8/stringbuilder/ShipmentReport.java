public class ShipmentReport {
    static String render(int[] shipmentIds, int maxUnits) {
        StringBuilder report = new StringBuilder(Math.min(maxUnits, 64));
        for (int shipmentId : shipmentIds) {
            String line = "shipment=" + shipmentId + "\n";
            if (line.length() > maxUnits - report.length()) {
                throw new IllegalArgumentException("Report exceeds text budget");
            }
            report.append(line);
        }
        return report.toString();
    }
    public static void main(String[] args) {
        System.out.print(render(new int[]{418, 509}, 64));
    }
}
