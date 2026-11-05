public class DispatchTask {
    private boolean completed;

    public void complete() {
        completed = true;
    }

    public boolean isCompleted() {
        return completed;
    }

    public static void main(String[] args) {
        DispatchTask task = new DispatchTask();
        task.complete();
        System.out.println(task.isCompleted());
    }
}
