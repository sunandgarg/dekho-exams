import jdk.jfr.Event;
import jdk.jfr.Label;
import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordingFile;
import java.nio.file.*;
public class ParcelFlightRecording {
    @Label("Parcel batch")
    static class BatchEvent extends Event { int parcels; }
    public static void main(String[] args) throws Exception {
        Path artifact = Files.createTempFile("aitrove-batch-", ".jfr");
        try {
            try (Recording recording = new Recording()) {
                recording.enable(BatchEvent.class).withoutThreshold();
                recording.start();
                BatchEvent event = new BatchEvent(); event.parcels = 42; event.commit();
                recording.stop(); recording.dump(artifact);
            }
            boolean found = RecordingFile.readAllEvents(artifact).stream()
                .anyMatch(event -> event.getEventType().getName().equals(BatchEvent.class.getName()) && event.getInt("parcels") == 42);
            System.out.println("Batch event found=" + found);
        } finally { Files.deleteIfExists(artifact); }
    }
}
