import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;
public class DeliveryDistances {
    static class Road {
        final int depot, minutes;
        Road(int depot, int minutes) {
            if (minutes < 0) throw new IllegalArgumentException("Negative travel time");
            this.depot = depot; this.minutes = minutes;
        }
    }
    static class Candidate {
        final int depot;
        final long minutes;
        Candidate(int depot, long minutes) { this.depot = depot; this.minutes = minutes; }
    }
    static long[] shortest(List<List<Road>> roads, int source) {
        if (source < 0 || source >= roads.size()) throw new IllegalArgumentException("Unknown source");
        long[] distance = new long[roads.size()];
        Arrays.fill(distance, Long.MAX_VALUE);
        distance[source] = 0;
        PriorityQueue<Candidate> pending = new PriorityQueue<>(Comparator.comparingLong(c -> c.minutes));
        pending.add(new Candidate(source, 0));
        while (!pending.isEmpty()) {
            Candidate current = pending.poll();
            if (current.minutes != distance[current.depot]) continue;
            for (Road road : roads.get(current.depot)) {
                if (road.depot < 0 || road.depot >= roads.size()) throw new IllegalArgumentException("Unknown destination");
                if (current.minutes > Long.MAX_VALUE - road.minutes) throw new ArithmeticException("Distance overflow");
                long improved = current.minutes + road.minutes;
                if (improved < distance[road.depot]) {
                    distance[road.depot] = improved;
                    pending.add(new Candidate(road.depot, improved));
                }
            }
        }
        return distance;
    }
    public static void main(String[] args) {
        List<List<Road>> roads = new ArrayList<>();
        for (int depot = 0; depot < 4; depot++) roads.add(new ArrayList<>());
        roads.get(0).add(new Road(1, 4)); roads.get(0).add(new Road(2, 10));
        roads.get(1).add(new Road(2, 3)); roads.get(1).add(new Road(3, 12));
        roads.get(2).add(new Road(3, 1));
        System.out.println(Arrays.toString(shortest(roads, 0)));
    }
}
