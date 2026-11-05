package in.aitrove.contracts;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.jupiter.api.Assertions.*;

public class ConsumerDedupContractTest {
    private static void apply(JdbcTemplate jdbc, TransactionTemplate transaction, String eventId, int units) {
        transaction.executeWithoutResult(status -> {
            jdbc.update("insert into applied_event (event_id) values (?)", eventId);
            jdbc.update("update stock_balance set available = available + ? where sku = ?", units, "SKU-41");
        });
    }

    @Test void repeatedEventIdCannotApplyTheStockMutationTwice() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:consumer_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        var jdbc = new JdbcTemplate(source);
        jdbc.execute("create table applied_event (event_id varchar(40) primary key)");
        jdbc.execute("create table stock_balance (sku varchar(40) primary key, available integer not null)");
        jdbc.update("insert into stock_balance values (?, ?)", "SKU-41", 10);
        var transaction = new TransactionTemplate(new DataSourceTransactionManager(source));

        apply(jdbc, transaction, "E-41", 4);
        assertThrows(DuplicateKeyException.class, () -> apply(jdbc, transaction, "E-41", 4));
        assertEquals(14, jdbc.queryForObject("select available from stock_balance where sku = 'SKU-41'", Integer.class));
        apply(jdbc, transaction, "E-42", -2);
        assertEquals(12, jdbc.queryForObject("select available from stock_balance where sku = 'SKU-41'", Integer.class));
        assertEquals(2L, jdbc.queryForObject("select count(*) from applied_event", Long.class));
    }

    @Test void failedBusinessMutationDoesNotReserveTheEventId() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:consumer_rollback_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        var jdbc = new JdbcTemplate(source);
        jdbc.execute("create table applied_event (event_id varchar(40) primary key)");
        jdbc.execute("create table stock_balance (sku varchar(40) primary key, available integer not null)");
        var transaction = new TransactionTemplate(new DataSourceTransactionManager(source));

        assertThrows(IllegalStateException.class, () -> transaction.executeWithoutResult(status -> {
            jdbc.update("insert into applied_event (event_id) values (?)", "E-43");
            int changed = jdbc.update("update stock_balance set available = available + ? where sku = ?", 4, "MISSING-SKU");
            if (changed != 1) throw new IllegalStateException("expected one stock row");
        }));
        assertEquals(0L, jdbc.queryForObject("select count(*) from applied_event", Long.class));
    }
}
