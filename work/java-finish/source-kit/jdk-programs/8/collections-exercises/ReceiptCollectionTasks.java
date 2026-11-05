import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ReceiptCollectionTasks {
    static Map<String, Integer> counts(List<String> states) {
        Map<String, Integer> result = new LinkedHashMap<>();
        for (String state : states) {
            if (state == null || state.trim().isEmpty()) throw new IllegalArgumentException("State required");
            result.merge(state, 1, Integer::sum);
        }
        return result;
    }
    static int duplicates(List<String> ids) {
        Set<String> seen = new HashSet<>();
        int duplicates = 0;
        for (String id : ids) {
            if (id == null) throw new IllegalArgumentException("ID required");
            if (!seen.add(id)) duplicates++;
        }
        return duplicates;
    }
    public static void main(String[] args) {
        System.out.println(counts(Arrays.asList("paid", "pending", "paid", "declined", "pending")));
        System.out.println(duplicates(Arrays.asList("r-8", "r-9", "r-8", "r-8")));
    }
}
