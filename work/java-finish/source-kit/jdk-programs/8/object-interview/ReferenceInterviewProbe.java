import java.util.ArrayList;
import java.util.List;

public class ReferenceInterviewProbe {
    static void replace(List<String> receipts) { receipts = new ArrayList<>(); }
    static void append(List<String> receipts) { receipts.add("r-72"); }
    public static void main(String[] args) {
        final List<String> receipts = new ArrayList<>();
        receipts.add("r-41");
        replace(receipts);
        append(receipts);
        System.out.println(receipts);
        System.out.println(receipts.size());
    }
}
