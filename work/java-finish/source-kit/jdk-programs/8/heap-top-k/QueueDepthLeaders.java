import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.PriorityQueue;
public class QueueDepthLeaders {
    static List<Integer> largest(int[] depths, int limit) {
        if (limit < 1) throw new IllegalArgumentException("Positive limit required");
        PriorityQueue<Integer> retained = new PriorityQueue<>();
        for (int depth : depths) {
            if (retained.size() < limit) retained.add(depth);
            else if (depth > retained.peek()) {
                retained.poll();
                retained.add(depth);
            }
        }
        List<Integer> ranked = new ArrayList<>(retained);
        ranked.sort(Collections.reverseOrder());
        return ranked;
    }
    public static void main(String[] args) {
        System.out.println(largest(new int[]{7, 3, 12, 8, 12, 5}, 3));
        System.out.println(largest(new int[]{4}, 3));
    }
}
