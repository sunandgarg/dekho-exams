import java.util.Arrays;
public class IntakeBoundaryChecks {
    static int[] collapseRuns(int[] shipmentCodes) {
        int[] retained = new int[shipmentCodes.length];
        int count = 0;
        for (int code : shipmentCodes) {
            if (count == 0 || retained[count - 1] != code) retained[count++] = code;
        }
        return Arrays.copyOf(retained, count);
    }
    static boolean asciiPalindrome(String text) {
        String normalized = text.replaceAll("[^A-Za-z]", "").toLowerCase(java.util.Locale.ROOT);
        int left = 0, right = normalized.length() - 1;
        while (left < right) if (normalized.charAt(left++) != normalized.charAt(right--)) return false;
        return true;
    }
    static void require(boolean condition) {
        if (!condition) throw new IllegalStateException("Exercise check failed");
    }
    public static void main(String[] args) {
        require(Arrays.equals(collapseRuns(new int[]{7, 7, 3, 7}), new int[]{7, 3, 7}));
        require(collapseRuns(new int[0]).length == 0);
        require(asciiPalindrome("Never odd or even"));
        require(!asciiPalindrome("parcel"));
        System.out.println("4 boundary checks passed");
    }
}
