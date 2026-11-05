import java.util.Arrays;
import java.util.LinkedList;

public class RemovalTrapDemo {
    public static void main(String[] args) {
        LinkedList<Integer> retryCodes = new LinkedList<>(
            Arrays.asList(7, 11, 7));
        retryCodes.remove(1);
        System.out.println(retryCodes);
        retryCodes.remove(Integer.valueOf(7));
        System.out.println(retryCodes);
    }
}
