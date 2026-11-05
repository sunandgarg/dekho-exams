public class InvoiceMethodContract {
    static long totalCents(int[] lineAmounts) {
        if (lineAmounts == null) throw new IllegalArgumentException("Missing amounts");
        long total = 0L;
        for (int amount : lineAmounts) {
            if (amount < 0) throw new IllegalArgumentException("Negative line amount");
            total = Math.addExact(total, amount);
        }
        return total;
    }
    public static void main(String[] args) {
        System.out.println(totalCents(new int[] {1250, 0, 750}));
        System.out.println(totalCents(new int[0]));
    }
}
