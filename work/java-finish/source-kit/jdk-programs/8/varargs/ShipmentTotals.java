public class ShipmentTotals {
    static long total(int... shipmentCounts) {
        if (shipmentCounts == null) {
            throw new IllegalArgumentException("Counts cannot be null");
        }
        long total = 0;
        for (int count : shipmentCounts) {
            if (count < 0) throw new IllegalArgumentException("Negative count");
            total = Math.addExact(total, count);
        }
        return total;
    }
    public static void main(String[] args) {
        int[] counts = {7, 12, 4};
        System.out.println(total(counts));
        System.out.println(total());
    }
}
