public class WarehouseRangeTotals {
    private final int size; private final long[] tree;
    WarehouseRangeTotals(int[] quantities) {
        size = quantities.length;
        if (size == 0 || size > 1000000) throw new IllegalArgumentException("size");
        tree = new long[2 * size];
        for (int index = 0; index < size; index++) tree[size + index] = quantities[index];
        for (int node = size - 1; node > 0; node--) tree[node] = tree[2 * node] + tree[2 * node + 1];
    }
    void replace(int index, int value) {
        if (index < 0 || index >= size) throw new IndexOutOfBoundsException();
        int node = index + size; tree[node] = value;
        while ((node /= 2) > 0) tree[node] = tree[2 * node] + tree[2 * node + 1];
    }
    long sum(int start, int end) {
        if (start < 0 || end < start || end > size) throw new IndexOutOfBoundsException();
        long total = 0;
        for (int left = start + size, right = end + size; left < right; left /= 2, right /= 2) {
            if ((left & 1) != 0) total += tree[left++];
            if ((right & 1) != 0) total += tree[--right];
        }
        return total;
    }
    public static void main(String[] args) {
        WarehouseRangeTotals stock = new WarehouseRangeTotals(new int[]{3, 5, 2, 7, 4});
        System.out.println(stock.sum(1, 4));
        stock.replace(1, 9); System.out.println(stock.sum(1, 4));
        System.out.println(stock.sum(2, 2));
        try { stock.sum(4, 2); } catch (IndexOutOfBoundsException rejected) { System.out.println("range rejected"); }
    }
}
