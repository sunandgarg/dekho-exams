import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

public class DatabaseLessonsTest {
    interface CheckedRun { void run() throws Exception; }
    static String output(CheckedRun program) throws Exception {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        PrintStream original = System.out;
        try (PrintStream capture = new PrintStream(buffer, true, StandardCharsets.UTF_8)) {
            System.setOut(capture); program.run();
        } finally { System.setOut(original); }
        return buffer.toString(StandardCharsets.UTF_8).replace("\r\n", "\n").trim();
    }
    @Test void boundQuoteRemainsData() throws Exception {
        assertEquals("paid\nnull", output(() -> ReceiptLookup.main(new String[0])));
    }
    @Test void failedCreditRollsBackDebit() throws Exception {
        assertEquals("failed transfer rolled back\nnorth=7\nsouth=5", output(() -> StockTransfer.main(new String[0])));
    }
}
