import java.util.Arrays;
public class VoucherMinimum {
    static int minimum(int[] denominations, int target) {
        if (target < 0 || target > 1000000 || denominations.length == 0) throw new IllegalArgumentException("target or coins");
        for (int coin : denominations) if (coin <= 0) throw new IllegalArgumentException("coin");
        int missing = target + 1;
        int[] best = new int[target + 1]; Arrays.fill(best, missing); best[0] = 0;
        for (int amount = 1; amount <= target; amount++) {
            for (int coin : denominations) if (coin <= amount && best[amount - coin] != missing)
                best[amount] = Math.min(best[amount], best[amount - coin] + 1);
        }
        return best[target] == missing ? -1 : best[target];
    }
    public static void main(String[] args) {
        System.out.println(minimum(new int[]{3, 5}, 11));
        System.out.println(minimum(new int[]{3, 5}, 4));
        System.out.println(minimum(new int[]{3, 5}, 0));
        try { minimum(new int[]{0, 5}, 9); } catch (IllegalArgumentException rejected) { System.out.println("coin rejected"); }
    }
}
