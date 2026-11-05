import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

public class Utf8InvoiceBatch {
    public static void main(String[] args) throws Exception {
        Path batch = Files.createTempFile("aitrove-invoices-", ".txt");
        try {
            Files.write(batch, Arrays.asList("1041", "1042", "1043"), StandardCharsets.UTF_8);
            int records = 0;
            try (BufferedReader reader = Files.newBufferedReader(batch, StandardCharsets.UTF_8)) {
                String line;
                while ((line = reader.readLine()) != null) {
                    Integer.parseInt(line);
                    records++;
                }
            }
            System.out.println("records=" + records);
        } finally {
            Files.deleteIfExists(batch);
        }
    }
}
