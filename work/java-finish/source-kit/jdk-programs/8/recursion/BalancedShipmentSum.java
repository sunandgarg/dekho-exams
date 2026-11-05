public class BalancedShipmentSum {
    static long sum(int[] counts, int from, int to) {
        if (from == to) return 0L;
        if (to - from == 1) return counts[from];
        int middle = from + (to - from) / 2;
        return sum(counts, from, middle) + sum(counts, middle, to);
    }
    public static void main(String[] args) {
        int[] dailyCounts = {12, 8, 0, 15, 3};
        System.out.println(sum(dailyCounts, 0, dailyCounts.length));
        System.out.println(sum(new int[0], 0, 0));
    }
}
