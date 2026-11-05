import java.util.ArrayDeque;
import java.util.Deque;

public class TaskDequeDemo {
    public static void main(String[] args) {
        Deque<String> pendingTasks = new ArrayDeque<>();
        pendingTasks.addLast("Validate invoice");
        pendingTasks.addLast("Send receipt");
        System.out.println(pendingTasks.pollFirst());
        System.out.println(pendingTasks.pollFirst());
        System.out.println(pendingTasks.pollFirst());
    }
}
