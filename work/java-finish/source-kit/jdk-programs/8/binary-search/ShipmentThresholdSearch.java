public class ShipmentThresholdSearch {
    static int lowerBound(int[] thresholds, int target) {
        int low = 0;
        int high = thresholds.length;
        while (low < high) {
            int middle = low + (high - low) / 2;
            if (thresholds[middle] < target) low = middle + 1;
            else high = middle;
        }
        return low;
    }
    public static void main(String[] args) {
        int[] thresholds = {10, 20, 20, 35, 80};
        System.out.println(lowerBound(thresholds, 20));
        System.out.println(lowerBound(thresholds, 22));
        System.out.println(lowerBound(thresholds, 90));
        System.out.println(lowerBound(new int[0], 20));
    }
}
