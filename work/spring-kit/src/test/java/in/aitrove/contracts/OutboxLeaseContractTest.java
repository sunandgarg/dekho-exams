package in.aitrove.contracts;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.junit.jupiter.api.Assertions.*;

public class OutboxLeaseContractTest {
    private static int claim(JdbcTemplate jdbc, String workerToken, long now, long leaseUntil) {
        return jdbc.update("""
            update delivery_outbox set claim_token = ?, lease_until = ?
            where event_id = 'E-41' and delivered = false
              and (claim_token is null or lease_until <= ?)
            """, workerToken, leaseUntil, now);
    }

    @Test void expiredLeaseCanBeReclaimedButOldWorkerCannotAcknowledge() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:lease_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        var jdbc = new JdbcTemplate(source);
        jdbc.execute("create table delivery_outbox (event_id varchar(40) primary key, claim_token varchar(40), lease_until bigint, delivered boolean not null)");
        jdbc.update("insert into delivery_outbox values (?, null, null, false)", "E-41");

        assertEquals(1, claim(jdbc, "worker-A", 100, 200));
        assertEquals(0, claim(jdbc, "worker-B", 150, 250));
        assertEquals(1, claim(jdbc, "worker-B", 200, 300));
        assertEquals(0, jdbc.update("update delivery_outbox set delivered = true where event_id = ? and claim_token = ? and delivered = false", "E-41", "worker-A"));
        assertEquals(1, jdbc.update("update delivery_outbox set delivered = true where event_id = ? and claim_token = ? and delivered = false", "E-41", "worker-B"));
        assertEquals(0, claim(jdbc, "worker-C", 400, 500));
        assertTrue(jdbc.queryForObject("select delivered from delivery_outbox where event_id = 'E-41'", Boolean.class));
    }
}
