import java.util.ArrayList;
import java.util.List;
import java.util.SequencedCollection;
public class ReversedRouteView {
    public static void main(String[] args) {
        SequencedCollection<String> stages = new ArrayList<>(List.of("received", "packed"));
        SequencedCollection<String> reverse = stages.reversed();
        System.out.println(stages.getFirst());
        System.out.println(reverse);
        stages.addLast("dispatched");
        System.out.println(reverse);
        System.out.println(reverse.getFirst());
    }
}
