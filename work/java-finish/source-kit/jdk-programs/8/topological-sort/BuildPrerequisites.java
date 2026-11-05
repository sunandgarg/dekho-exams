import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;
public class BuildPrerequisites {
    static int[] order(int[][] dependents) {
        int[] incoming = new int[dependents.length];
        for (int[] nextTasks : dependents) {
            for (int task : nextTasks) {
                if (task < 0 || task >= incoming.length) throw new IllegalArgumentException("Unknown task");
                incoming[task]++;
            }
        }
        Queue<Integer> ready = new ArrayDeque<>();
        for (int task = 0; task < incoming.length; task++) if (incoming[task] == 0) ready.add(task);
        int[] ordered = new int[incoming.length];
        int completed = 0;
        while (!ready.isEmpty()) {
            int task = ready.remove();
            ordered[completed++] = task;
            for (int dependent : dependents[task]) {
                if (--incoming[dependent] == 0) ready.add(dependent);
            }
        }
        if (completed != incoming.length) throw new IllegalArgumentException("Prerequisite cycle");
        return ordered;
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString(order(new int[][]{{2}, {2}, {3}, {}})));
        try { order(new int[][]{{1}, {0}}); }
        catch (IllegalArgumentException rejected) { System.out.println("Cycle rejected"); }
    }
}
