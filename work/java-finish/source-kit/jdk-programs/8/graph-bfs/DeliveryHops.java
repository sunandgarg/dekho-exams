import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

public class DeliveryHops {
    static int[] distances(int[][] routes, int source) {
        if (source < 0 || source >= routes.length) throw new IllegalArgumentException("Invalid source");
        int[] distance = new int[routes.length];
        Arrays.fill(distance, -1);
        Deque<Integer> pending = new ArrayDeque<>();
        distance[source] = 0; pending.addLast(source);
        while (!pending.isEmpty()) {
            int depot = pending.removeFirst();
            for (int next : routes[depot]) {
                if (next < 0 || next >= routes.length) throw new IllegalArgumentException("Invalid route");
                if (distance[next] == -1) {
                    distance[next] = distance[depot] + 1;
                    pending.addLast(next);
                }
            }
        }
        return distance;
    }
    public static void main(String[] args) {
        int[][] routes = {{1, 2}, {3}, {3}, {0}, {}};
        System.out.println(Arrays.toString(distances(routes, 0)));
    }
}
