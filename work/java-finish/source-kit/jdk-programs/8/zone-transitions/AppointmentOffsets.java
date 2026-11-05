import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
public class AppointmentOffsets {
    public static void main(String[] args) {
        ZoneId zone = ZoneId.of("Europe/Paris");
        LocalDateTime gap = LocalDateTime.parse("2024-03-31T02:30:00");
        LocalDateTime overlap = LocalDateTime.parse("2024-10-27T02:30:00");
        System.out.println("gap offsets=" + zone.getRules().getValidOffsets(gap).size());
        List<ZoneOffset> offsets = zone.getRules().getValidOffsets(overlap);
        System.out.println("overlap offsets=" + offsets.size());
        for (ZoneOffset offset : offsets) System.out.println(overlap.toInstant(offset));
    }
}
