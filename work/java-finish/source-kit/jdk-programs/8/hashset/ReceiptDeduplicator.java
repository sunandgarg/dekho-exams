import java.util.HashSet;
import java.util.Set;

public class ReceiptDeduplicator {
    public static void main(String[] args) {
        String[] importedIds = {" rcpt-41 ", "rcpt-82", "rcpt-41", ""};
        Set<String> acceptedIds = new HashSet<>();
        int duplicates = 0;
        int rejected = 0;
        for (String rawId : importedIds) {
            String receiptId = rawId.trim();
            if (receiptId.isEmpty()) {
                rejected++;
            } else if (!acceptedIds.add(receiptId)) {
                duplicates++;
            }
        }
        System.out.println("accepted=" + acceptedIds.size());
        System.out.println("duplicates=" + duplicates);
        System.out.println("rejected=" + rejected);
    }
}
