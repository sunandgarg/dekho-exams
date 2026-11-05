import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
public class FixedDispatchHeap {
    final int[] priorities; int size;
    FixedDispatchHeap(int capacity) {
        if (capacity < 0) throw new IllegalArgumentException("Negative capacity");
        priorities = new int[capacity];
    }
    void add(int priority) {
        if (size == priorities.length) throw new IllegalStateException("Full heap");
        int position = size++; priorities[position] = priority;
        while (position > 0) {
            int parent = (position-1)/2;
            if (priorities[parent] <= priorities[position]) break;
            swap(parent, position); position = parent;
        }
    }
    void swap(int a, int b) { int old=priorities[a]; priorities[a]=priorities[b]; priorities[b]=old; }
    int poll() {
        if (size == 0) throw new NoSuchElementException("Empty heap");
        int selected=priorities[0]; priorities[0]=priorities[--size]; int position=0;
        while (position < size/2) {
            int child=2*position+1;
            if (child+1<size && priorities[child+1]<priorities[child]) child++;
            if (priorities[position]<=priorities[child]) break;
            swap(position, child); position=child;
        }
        return selected;
    }
    public static void main(String[] args) {
        FixedDispatchHeap queue = new FixedDispatchHeap(4);
        for (int priority : new int[]{7, 4, -2, 4}) queue.add(priority);
        List<Integer> removed=new ArrayList<>();
        while (queue.size>0) removed.add(queue.poll());
        System.out.println(removed);
        try { queue.poll(); }
        catch (NoSuchElementException empty) { System.out.println("Empty rejected"); }
    }
}
