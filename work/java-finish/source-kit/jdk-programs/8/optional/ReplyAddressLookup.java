import java.util.Optional;

public class ReplyAddressLookup {
    static Optional<String> configuredAddress(String rawAddress) {
        return Optional.ofNullable(rawAddress)
                .map(String::trim)
                .filter(address -> !address.isEmpty());
    }
    static String fallbackAddress() {
        System.out.println("fallback evaluated");
        return "support@aitrove.in";
    }
    public static void main(String[] args) {
        System.out.println(configuredAddress(" team@aitrove.in ").orElseGet(ReplyAddressLookup::fallbackAddress));
        System.out.println(configuredAddress(" ").orElseGet(ReplyAddressLookup::fallbackAddress));
    }
}
