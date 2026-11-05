import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;

public class LinkedListChecks {
    public static void main(String[] args) {
        LinkedList<Integer> retries = new LinkedList<>(Arrays.asList(2, 5, 2));
        boolean removed = retries.remove(Integer.valueOf(2));
        if (!removed || !retries.equals(Arrays.asList(5, 2))) {
            throw new AssertionError("Remove first matching value");
        }
        LinkedList<String> jobs = new LinkedList<>(Arrays.asList("done:1", "pending:2"));
        Iterator<String> cursor = jobs.iterator();
        while (cursor.hasNext()) {
            if (cursor.next().startsWith("done:")) cursor.remove();
        }
        if (!jobs.equals(Arrays.asList("pending:2"))) {
            throw new AssertionError("Remove completed jobs");
        }
        LinkedList<String> emptyQueue = new LinkedList<>();
        if (emptyQueue.pollFirst() != null) throw new AssertionError("Empty queue");
        System.out.println("3 checks passed");
    }
}
