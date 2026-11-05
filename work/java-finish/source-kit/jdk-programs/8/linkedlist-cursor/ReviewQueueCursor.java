import java.util.*;
public class ReviewQueueCursor {
    public static void main(String[] args) {
        LinkedList<String> queue = new LinkedList<>(Arrays.asList("Read", "Code", "Ship"));
        ListIterator<String> cursor = queue.listIterator();
        cursor.next(); cursor.add("Test"); cursor.next(); cursor.remove();
        System.out.println(queue);
        cursor.add("Audit");
        try { cursor.remove(); }
        catch (IllegalStateException rejected) { System.out.println("cursor state rejected"); }
    }
}
