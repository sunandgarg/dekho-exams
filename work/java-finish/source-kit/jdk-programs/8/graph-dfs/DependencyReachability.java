import java.util.ArrayDeque;
import java.util.Deque;

public class DependencyReachability {
    static int reachable(int[][] dependencies, int source) {
        if (source < 0 || source >= dependencies.length) throw new IllegalArgumentException("Invalid source");
        boolean[] discovered = new boolean[dependencies.length];
        Deque<Integer> pending = new ArrayDeque<>();
        pending.push(source); discovered[source] = true;
        int count = 0;
        while (!pending.isEmpty()) {
            int module = pending.pop(); count++;
            for (int next : dependencies[module]) {
                if (next < 0 || next >= dependencies.length) throw new IllegalArgumentException("Invalid edge");
                if (!discovered[next]) { discovered[next] = true; pending.push(next); }
            }
        }
        return count;
    }
    public static void main(String[] args) {
        int[][] dependencies = {{1}, {2}, {0, 3}, {}, {}};
        System.out.println(reachable(dependencies, 0));
    }
}
