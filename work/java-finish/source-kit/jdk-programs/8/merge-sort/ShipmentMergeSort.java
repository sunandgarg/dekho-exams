import java.util.Arrays;

public class ShipmentMergeSort {
    static void sort(int[] shipmentIds) {
        split(shipmentIds, new int[shipmentIds.length], 0, shipmentIds.length);
    }
    static void split(int[] values, int[] scratch, int from, int to) {
        if (to - from < 2) return;
        int middle = from + (to - from) / 2;
        split(values, scratch, from, middle); split(values, scratch, middle, to);
        int left = from, right = middle, output = from;
        while (left < middle && right < to) {
            scratch[output++] = values[left] <= values[right] ? values[left++] : values[right++];
        }
        while (left < middle) scratch[output++] = values[left++];
        while (right < to) scratch[output++] = values[right++];
        System.arraycopy(scratch, from, values, from, to - from);
    }
    public static void main(String[] args) {
        int[] shipmentIds = {42, 11, 42, 8, 30};
        sort(shipmentIds);
        System.out.println(Arrays.toString(shipmentIds));
        int[] empty = {}; sort(empty); System.out.println(Arrays.toString(empty));
    }
}
