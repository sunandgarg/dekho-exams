import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class AuditBatch {
    private final List<String> eventIds = new ArrayList<>();

    public void record(String eventId) {
        if (eventId == null) throw new IllegalArgumentException("eventId");
        eventIds.add(eventId);
    }

    public List<String> snapshot() {
        return Collections.unmodifiableList(new ArrayList<>(eventIds));
    }
}
