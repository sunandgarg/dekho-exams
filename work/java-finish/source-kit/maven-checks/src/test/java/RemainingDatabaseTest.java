import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
public class RemainingDatabaseTest {
    @Test void jdbcRollbackProbe() throws Exception {
        assertEquals("rows=0", DatabaseLessonsTest.output(() -> JdbcRollbackProbe.main(new String[0])));
    }
    @Test void receiptDatabaseProject() throws Exception {
        assertEquals("Duplicate rejected\ntotal=7\nrows=1", DatabaseLessonsTest.output(() -> ReceiptDatabaseProject.main(new String[0])));
    }
    @Test void boundValueReference() throws Exception {
        assertEquals("customer'42", DatabaseLessonsTest.output(() -> BoundValueReference.main(new String[0])));
    }
    @Test void receiptIsolationSessions() throws Exception {
        assertEquals("7\n11", DatabaseLessonsTest.output(() -> ReceiptIsolationSessions.main(new String[0])));
    }
    @Test void seedMigrationLedger() throws Exception {
        assertEquals("true\nfalse\nMigration definition changed", DatabaseLessonsTest.output(() -> SeedMigrationLedger.main(new String[0])));
    }
    @Test void pooledReceiptBoundary() throws Exception {
        assertEquals("0\npool timeout\ntrue", DatabaseLessonsTest.output(() -> PooledReceiptBoundary.main(new String[0])));
    }
}
