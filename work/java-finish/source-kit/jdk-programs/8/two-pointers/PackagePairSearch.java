import java.util.Arrays;
public class PackagePairSearch {
    static int[] pair(int[] sortedWeights, long target) {
        int left = 0;
        int right = sortedWeights.length - 1;
        while (left < right) {
            long total = (long) sortedWeights[left] + sortedWeights[right];
            if (total == target) return new int[]{sortedWeights[left], sortedWeights[right]};
            if (total < target) left++;
            else right--;
        }
        return new int[0];
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString(pair(new int[]{2, 5, 8, 11, 15}, 16)));
        System.out.println(Arrays.toString(pair(new int[]{4}, 8)));
    }
}
