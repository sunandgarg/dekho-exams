import java.util.Comparator;
import java.util.TreeSet;
public class DispatchJobOrdering {
    static final class Job {
        final String id; final int priority;
        Job(String id, int priority) { this.id=id; this.priority=priority; }
    }
    public static void main(String[] args) {
        Comparator<Job> priorityOnly = Comparator.comparingInt(job -> job.priority);
        TreeSet<Job> merged = new TreeSet<>(priorityOnly);
        merged.add(new Job("D-11", 3)); merged.add(new Job("D-12", 3));
        TreeSet<Job> distinct = new TreeSet<>(priorityOnly.thenComparing(job -> job.id));
        distinct.addAll(merged); distinct.add(new Job("D-12", 3));
        System.out.println(merged.size());
        System.out.println(distinct.size());
        System.out.println(Integer.compare(Integer.MIN_VALUE, Integer.MAX_VALUE));
    }
}
