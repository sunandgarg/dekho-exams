import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
public class ManifestImport {
    static Map<String, Integer> read(Path input) throws IOException {
        Map<String, Integer> totals = new LinkedHashMap<>();
        int lineNumber = 0;
        for (String line : Files.readAllLines(input, StandardCharsets.UTF_8)) {
            lineNumber++;
            String[] fields = line.split(",", -1);
            if (fields.length != 2 || fields[0].trim().isEmpty()) {
                throw new IllegalArgumentException("Malformed line " + lineNumber);
            }
            String depot = fields[0].trim();
            int count = Integer.parseInt(fields[1].trim());
            if (count <= 0) throw new IllegalArgumentException("Invalid count at line " + lineNumber);
            totals.merge(depot, count, Math::addExact);
        }
        return totals;
    }
    public static void main(String[] args) throws IOException {
        Path input = Files.createTempFile("aitrove-manifest-", ".txt");
        try {
            Files.write(input, Arrays.asList("DL-01,4", "PN-02,3", "DL-01,6"), StandardCharsets.UTF_8);
            System.out.println(read(input));
            Files.write(input, Arrays.asList("DL-01,4", "PN-02,-3"), StandardCharsets.UTF_8);
            try { read(input); }
            catch (IllegalArgumentException rejected) { System.out.println("Invalid batch rejected"); }
        } finally {
            Files.deleteIfExists(input);
        }
    }
}
