public class BusiestHours {
    static long maximum(int[] hourlyParcels, int width) {
        if (width < 1 || width > hourlyParcels.length) {
            throw new IllegalArgumentException("Invalid window width");
        }
        long total = 0;
        for (int hour = 0; hour < width; hour++) total += hourlyParcels[hour];
        long best = total;
        for (int hour = width; hour < hourlyParcels.length; hour++) {
            total -= hourlyParcels[hour - width];
            total += hourlyParcels[hour];
            best = Math.max(best, total);
        }
        return best;
    }
    public static void main(String[] args) {
        System.out.println("peak=" + maximum(new int[]{4, 2, 7, 1, 6, 3}, 3));
        System.out.println("negative=" + maximum(new int[]{-8, -3, -6}, 2));
    }
}
