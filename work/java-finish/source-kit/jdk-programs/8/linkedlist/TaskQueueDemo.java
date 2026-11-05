import java.util.LinkedList;

public class TaskQueueDemo {
    public static void main(String[] args) {
        LinkedList<String> pendingTasks = new LinkedList<>();
        pendingTasks.addLast("Validate invoice");
        pendingTasks.addLast("Send receipt");
        pendingTasks.addFirst("Check account");
        System.out.println(pendingTasks);
        System.out.println(pendingTasks.pollFirst());
        System.out.println(pendingTasks.peekFirst());
        System.out.println(pendingTasks.size());
    }
}
