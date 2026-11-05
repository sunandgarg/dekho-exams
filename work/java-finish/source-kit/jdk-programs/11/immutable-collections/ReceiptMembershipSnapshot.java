import java.util.ArrayList;
import java.util.List;
public class ReceiptMembershipSnapshot {
    public static void main(String[] args) {
        List<StringBuilder> drafts = new ArrayList<>();
        drafts.add(new StringBuilder("pending"));
        List<StringBuilder> exported = List.copyOf(drafts);
        drafts.add(new StringBuilder("received"));
        drafts.get(0).append(":reviewed");
        System.out.println(exported.size());
        System.out.println(exported.get(0));
        try { exported.add(new StringBuilder("late")); }
        catch (UnsupportedOperationException rejected) { System.out.println("Membership fixed"); }
        try { List.of("ready", null); }
        catch (NullPointerException rejected) { System.out.println("Null rejected"); }
    }
}
