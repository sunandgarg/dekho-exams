import java.util.Arrays;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.ListIterator;

public class WorkflowIterator {
    public static void main(String[] args) {
        LinkedList<String> stages = new LinkedList<>(Arrays.asList("received", "failed:scan", "packed"));
        Iterator<String> cleanup = stages.iterator();
        while (cleanup.hasNext()) {
            if (cleanup.next().startsWith("failed:")) {
                cleanup.remove();
            }
        }
        ListIterator<String> editor = stages.listIterator(1);
        editor.add("quality-check");
        System.out.println(stages);
        System.out.println(editor.next());
    }
}
