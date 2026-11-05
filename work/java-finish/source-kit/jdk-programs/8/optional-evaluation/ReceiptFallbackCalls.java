import java.util.Optional;
public class ReceiptFallbackCalls {
    static int calls;
    static String loadArchive() { calls++; return "archive"; }
    public static void main(String[] args) {
        Optional<String> receipt = Optional.of("cached");
        System.out.println(receipt.orElse(loadArchive()));
        System.out.println(calls);
        System.out.println(receipt.orElseGet(ReceiptFallbackCalls::loadArchive));
        System.out.println(calls);
        System.out.println(Optional.<String>empty().orElseGet(ReceiptFallbackCalls::loadArchive));
        System.out.println(calls);
    }
}
