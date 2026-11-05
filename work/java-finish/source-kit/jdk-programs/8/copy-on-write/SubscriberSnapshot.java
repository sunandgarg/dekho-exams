import java.util.Arrays;
import java.util.Iterator;
import java.util.concurrent.CopyOnWriteArrayList;
public class SubscriberSnapshot {
    public static void main(String[] args) {
        CopyOnWriteArrayList<String> listeners = new CopyOnWriteArrayList<>(Arrays.asList("email", "audit"));
        Iterator<String> before = listeners.iterator();
        listeners.add("metrics");
        while (before.hasNext()) System.out.println(before.next());
        System.out.println(listeners);
        try { before.remove(); }
        catch (UnsupportedOperationException rejected) { System.out.println("Snapshot cannot remove"); }
    }
}
