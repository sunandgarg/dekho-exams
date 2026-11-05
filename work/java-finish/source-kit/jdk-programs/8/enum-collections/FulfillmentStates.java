import java.util.EnumMap;
import java.util.EnumSet;
public class FulfillmentStates {
    enum Stage { RECEIVED, PACKED, DISPATCHED }
    public static void main(String[] args) {
        EnumMap<Stage, Integer> counts = new EnumMap<>(Stage.class);
        for (Stage stage : new Stage[]{Stage.RECEIVED, Stage.PACKED, Stage.PACKED}) {
            counts.merge(stage, 1, Integer::sum);
        }
        EnumSet<Stage> review = EnumSet.of(Stage.RECEIVED, Stage.PACKED);
        System.out.println(counts);
        System.out.println("dispatched=" + counts.getOrDefault(Stage.DISPATCHED, 0));
        EnumSet<Stage> accepted = EnumSet.copyOf(review);
        accepted.remove(Stage.RECEIVED);
        System.out.println(accepted);
    }
}
