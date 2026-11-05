import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;

public class DelhiAppointmentTime {
    public static void main(String[] args) {
        LocalDateTime appointment = LocalDateTime.of(2026, 10, 5, 9, 30);
        ZonedDateTime zoned = appointment.atZone(ZoneId.of("Asia/Kolkata"));
        Instant instant = zoned.toInstant();
        System.out.println(zoned);
        System.out.println(instant);
    }
}
