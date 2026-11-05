import java.util.Arrays;
import java.util.List;
import java.util.function.Predicate;

public class AllowedContactFilter {
    public static void main(String[] args) {
        String allowedDomain = "@aitrove.in";
        Predicate<String> allowed = address -> address.endsWith(allowedDomain);
        List<String> imported = Arrays.asList("team@aitrove.in", "external@other.test");
        for (String address : imported) {
            if (allowed.test(address)) {
                System.out.println(address);
            }
        }
    }
}
