import java.util.Arrays;

public class PackagePlanner {
    static int minimumPackages(int target, int[] sizes) {
        if (target < 0) throw new IllegalArgumentException("Negative target");
        for (int size : sizes) if (size <= 0) throw new IllegalArgumentException("Sizes must be positive");
        int[] cache = new int[Math.addExact(target, 1)];
        Arrays.fill(cache, -2); cache[0] = 0;
        return solve(target, sizes, cache);
    }
    static int solve(int remaining, int[] sizes, int[] cache) {
        if (cache[remaining] != -2) return cache[remaining];
        int best = Integer.MAX_VALUE;
        for (int size : sizes) {
            if (size > remaining) continue;
            int previous = solve(remaining - size, sizes, cache);
            if (previous >= 0) best = Math.min(best, previous + 1);
        }
        return cache[remaining] = best == Integer.MAX_VALUE ? -1 : best;
    }
    public static void main(String[] args) {
        System.out.println(minimumPackages(10, new int[]{3, 5}));
        System.out.println(minimumPackages(7, new int[]{3, 5}));
        System.out.println(minimumPackages(0, new int[]{3, 5}));
    }
}
