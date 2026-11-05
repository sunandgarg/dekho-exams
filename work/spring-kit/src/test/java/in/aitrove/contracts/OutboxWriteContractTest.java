package in.aitrove.contracts;

import java.util.UUID;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.jupiter.api.Assertions.*;

public class OutboxWriteContractTest {
    private static JdbcTemplate database() {
        DataSource source = new DriverManagerDataSource(
            "jdbc:h2:mem:outbox_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        return new JdbcTemplate(source);
    }

    @Test void receiptAndOutboxRowCommitOrRollBackTogether() {
        var jdbc = database();
        jdbc.execute("create table receipt (id varchar(40) primary key, state varchar(30) not null)");
        jdbc.execute("create table outbox (id varchar(40) primary key, receipt_id varchar(40) not null, state varchar(20) not null)");
        var transaction = new TransactionTemplate(new DataSourceTransactionManager(jdbc.getDataSource()));

        assertThrows(IllegalStateException.class, () -> transaction.executeWithoutResult(status -> {
            jdbc.update("insert into receipt values (?, ?)", "R-41", "accepted");
            jdbc.update("insert into outbox values (?, ?, ?)", "E-41", "R-41", "pending");
            throw new IllegalStateException("reject before commit");
        }));
        assertEquals(0L, jdbc.queryForObject("select count(*) from receipt", Long.class));
        assertEquals(0L, jdbc.queryForObject("select count(*) from outbox", Long.class));

        transaction.executeWithoutResult(status -> {
            jdbc.update("insert into receipt values (?, ?)", "R-41", "accepted");
            jdbc.update("insert into outbox values (?, ?, ?)", "E-41", "R-41", "pending");
        });
        assertEquals(1L, jdbc.queryForObject("select count(*) from receipt", Long.class));
        assertEquals(1L, jdbc.queryForObject("select count(*) from outbox", Long.class));
        assertEquals(1, jdbc.update("update outbox set state = 'claimed' where id = ? and state = 'pending'", "E-41"));
        assertEquals(0, jdbc.update("update outbox set state = 'claimed' where id = ? and state = 'pending'", "E-41"));
    }
}
