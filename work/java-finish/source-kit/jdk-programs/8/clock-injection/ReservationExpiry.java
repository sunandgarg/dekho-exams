import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
public class ReservationExpiry {
    private final Clock clock;
    ReservationExpiry(Clock clock) { this.clock = clock; }
    boolean expired(Instant deadline) { return !clock.instant().isBefore(deadline); }
    public static void main(String[] args) {
        Instant deadline = Instant.parse("2026-01-12T12:00:00Z");
        Clock boundary = Clock.fixed(deadline, ZoneOffset.UTC);
        System.out.println(new ReservationExpiry(Clock.offset(boundary, Duration.ofSeconds(-1))).expired(deadline));
        System.out.println(new ReservationExpiry(boundary).expired(deadline));
    }
}
