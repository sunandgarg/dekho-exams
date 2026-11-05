import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;

public class IteratorCleanupDemo {
    public static void main(String[] args) {
        LinkedList<String> jobs = new LinkedList<>(
            Arrays.asList("done:1", "pending:2", "done:3"));
        Iterator<String> cursor = jobs.iterator();
        while (cursor.hasNext()) {
            if (cursor.next().startsWith("done:")) {
                cursor.remove();
            }
        }
        System.out.println(jobs);
    }
}
