import java.util.ArrayList;
import java.util.List;
public class PackingCombinations {
    static void search(int[] weights, int index, int remaining,
                       List<Integer> selected, List<List<Integer>> results) {
        if (remaining == 0) { results.add(new ArrayList<>(selected)); return; }
        if (index == weights.length) return;
        if (weights[index] <= remaining) {
            selected.add(weights[index]);
            search(weights, index + 1, remaining - weights[index], selected, results);
            selected.remove(selected.size() - 1);
        }
        search(weights, index + 1, remaining, selected, results);
    }
    static List<List<Integer>> combinations(int[] weights, int target) {
        if (target < 0) throw new IllegalArgumentException("Negative target");
        for (int weight : weights) if (weight <= 0) throw new IllegalArgumentException("Positive weights required");
        List<List<Integer>> results = new ArrayList<>();
        search(weights, 0, target, new ArrayList<>(), results);
        return results;
    }
    public static void main(String[] args) {
        System.out.println(combinations(new int[]{2, 3, 5, 7}, 10));
        System.out.println(combinations(new int[]{4, 6}, 0));
    }
}
