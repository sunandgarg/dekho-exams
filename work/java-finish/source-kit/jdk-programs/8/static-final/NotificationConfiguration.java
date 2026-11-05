import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class NotificationConfiguration {
    static final int MAX_ATTEMPTS = 3;
    static final class Settings {
        private final List<String> channels;
        Settings(List<String> channels) {
            this.channels = Collections.unmodifiableList(new ArrayList<>(channels));
        }
        List<String> channels() { return channels; }
    }
    public static void main(String[] args) {
        List<String> requested = new ArrayList<>(Arrays.asList("email"));
        Settings settings = new Settings(requested);
        requested.add("sms");
        System.out.println(settings.channels());
        System.out.println(MAX_ATTEMPTS);
    }
}
