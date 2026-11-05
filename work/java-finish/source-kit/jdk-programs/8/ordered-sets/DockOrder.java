import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.TreeSet;
public class DockOrder {
    public static void main(String[] args) {
        LinkedHashSet<String> arrival = new LinkedHashSet<>(
            Arrays.asList("Dock-C", "Dock-A", "Dock-C", "Dock-B"));
        System.out.println(arrival);
        TreeSet<String> normalized = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);
        normalized.add("Dock-A");
        normalized.add("dock-a");
        normalized.add("Dock-C");
        System.out.println("unique=" + normalized.size());
        System.out.println("next=" + normalized.ceiling("Dock-B"));
    }
}
