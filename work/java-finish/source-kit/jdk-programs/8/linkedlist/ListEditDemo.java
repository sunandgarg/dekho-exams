import java.util.Arrays;
import java.util.LinkedList;
import java.util.ListIterator;

public class ListEditDemo {
    public static void main(String[] args) {
        LinkedList<String> stages = new LinkedList<>(
            Arrays.asList("Received", "Packed", "Dispatched"));
        ListIterator<String> cursor = stages.listIterator();
        while (cursor.hasNext()) {
            if ("Packed".equals(cursor.next())) {
                cursor.add("Quality checked");
                break;
            }
        }
        System.out.println(stages);
    }
}
