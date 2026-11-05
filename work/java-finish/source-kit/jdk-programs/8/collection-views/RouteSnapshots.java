import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
public class RouteSnapshots {
    public static void main(String[] args) {
        List<String> routes = new ArrayList<>(Arrays.asList("North", "South"));
        List<String> live = Collections.unmodifiableList(routes);
        List<String> snapshot = Collections.unmodifiableList(new ArrayList<>(routes));
        routes.add("West");
        System.out.println("live=" + live.size());
        System.out.println("snapshot=" + snapshot.size());
        try {
            live.add("East");
        } catch (UnsupportedOperationException rejected) {
            System.out.println("Reader cannot add");
        }
    }
}
