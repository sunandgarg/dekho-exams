import java.time.LocalDate;
import java.time.format.*;
import java.util.Locale;
public class DeliveryDateInput {
    static final DateTimeFormatter INPUT = DateTimeFormatter.ofPattern("uuuu-MM-dd", Locale.ROOT)
        .withResolverStyle(ResolverStyle.STRICT);
    public static void main(String[] args) {
        System.out.println(LocalDate.parse("2024-02-29", INPUT));
        try { LocalDate.parse("2023-02-29", INPUT); }
        catch (DateTimeParseException rejected) { System.out.println("invalid day rejected"); }
    }
}
