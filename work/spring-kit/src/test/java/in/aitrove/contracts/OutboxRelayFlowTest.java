package in.aitrove.contracts;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.jupiter.api.Assertions.*;

/** A deterministic, single-process delivery model. No broker or background scheduler runs here. */
class OutboxRelayFlowTest {
    private JdbcTemplate jdbc;
    private TransactionTemplate transactions;

    @BeforeEach void database() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:relay_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        transactions = new TransactionTemplate(new DataSourceTransactionManager(source));
        jdbc.execute("create table shipment_request (request_id varchar(40) primary key)");
        jdbc.execute("""
            create table delivery_outbox (
                event_id varchar(40) primary key, sku varchar(40) not null, units int not null,
                status varchar(12) not null, claim_token varchar(40), lease_until bigint,
                next_attempt_at bigint not null, failures int not null)
            """);
        jdbc.execute("create table applied_event (event_id varchar(40) primary key)");
        jdbc.execute("create table stock_balance (sku varchar(40) primary key, available int not null)");
        jdbc.update("insert into stock_balance values (?, ?)", "SKU-17", 10);
    }

    private void accept(String eventId, String sku, int units, boolean abort) {
        transactions.executeWithoutResult(status -> {
            jdbc.update("insert into shipment_request values (?)", "REQUEST-" + eventId);
            jdbc.update("insert into delivery_outbox values (?, ?, ?, 'PENDING', null, null, 0, 0)",
                eventId, sku, units);
            if (abort) throw new IllegalStateException("simulate producer rollback");
        });
    }

    private boolean claim(String eventId, String token, long now, long leaseLength) {
        return jdbc.update("""
            update delivery_outbox set claim_token = ?, lease_until = ?
            where event_id = ? and status = 'PENDING' and next_attempt_at <= ?
              and (claim_token is null or lease_until <= ?)
            """, token, now + leaseLength, eventId, now, now) == 1;
    }

    private boolean acknowledge(String eventId, String token, long now) {
        return jdbc.update("""
            update delivery_outbox set status = 'DELIVERED', claim_token = null, lease_until = null
            where event_id = ? and status = 'PENDING' and claim_token = ? and lease_until > ?
            """, eventId, token, now) == 1;
    }

    private boolean fail(String eventId, String token, long now, int limit) {
        return jdbc.update("""
            update delivery_outbox set failures = failures + 1,
                status = case when failures + 1 >= ? then 'DEAD' else 'PENDING' end,
                next_attempt_at = ? + case when failures = 0 then 10
                    when failures = 1 then 20 else 40 end,
                claim_token = null, lease_until = null
            where event_id = ? and status = 'PENDING' and claim_token = ? and lease_until > ?
            """, limit, now, eventId, token, now) == 1;
    }

    private boolean consume(String eventId) {
        try {
            transactions.executeWithoutResult(status -> {
                jdbc.update("insert into applied_event values (?)", eventId);
                int changed = jdbc.update("""
                    update stock_balance set available = available - (
                        select units from delivery_outbox where event_id = ?)
                    where sku = (select sku from delivery_outbox where event_id = ?)
                    """, eventId, eventId);
                if (changed != 1) throw new IllegalStateException("unknown stock item");
            });
            return true;
        } catch (DuplicateKeyException duplicate) {
            return false;
        }
    }

    private int count(String table) {
        return jdbc.queryForObject("select count(*) from " + table, Integer.class);
    }

    @Test void acceptedEventIsConsumedAndAcknowledged() {
        accept("EVENT-21", "SKU-17", 3, false);
        assertEquals(1, count("shipment_request"));
        assertTrue(claim("EVENT-21", "worker-A", 100, 50));
        assertTrue(consume("EVENT-21"));
        assertTrue(acknowledge("EVENT-21", "worker-A", 110));
        assertEquals(7, jdbc.queryForObject("select available from stock_balance where sku = 'SKU-17'", Integer.class));
        assertEquals("DELIVERED", jdbc.queryForObject("select status from delivery_outbox where event_id = 'EVENT-21'", String.class));
        assertFalse(claim("EVENT-21", "worker-B", 200, 50));
    }

    @Test void producerRollbackLeavesNeitherCommandNorEvent() {
        assertThrows(IllegalStateException.class, () -> accept("EVENT-22", "SKU-17", 2, true));
        assertEquals(0, count("shipment_request"));
        assertEquals(0, count("delivery_outbox"));
    }

    @Test void duplicateDeliveryChangesStockOnce() {
        accept("EVENT-23", "SKU-17", 2, false);
        assertTrue(consume("EVENT-23"));
        assertFalse(consume("EVENT-23"));
        assertEquals(8, jdbc.queryForObject("select available from stock_balance where sku = 'SKU-17'", Integer.class));
        assertEquals(1, count("applied_event"));
    }

    @Test void failedConsumerMutationRollsBackItsEventReservation() {
        accept("EVENT-24", "UNKNOWN", 2, false);
        assertThrows(IllegalStateException.class, () -> consume("EVENT-24"));
        assertEquals(0, count("applied_event"));
        jdbc.update("insert into stock_balance values (?, ?)", "UNKNOWN", 5);
        assertTrue(consume("EVENT-24"));
        assertEquals(3, jdbc.queryForObject("select available from stock_balance where sku = 'UNKNOWN'", Integer.class));
    }

    @Test void failureWaitsForBoundedRetryDueTime() {
        accept("EVENT-25", "SKU-17", 1, false);
        assertTrue(claim("EVENT-25", "worker-A", 100, 50));
        assertTrue(fail("EVENT-25", "worker-A", 101, 3));
        assertFalse(claim("EVENT-25", "worker-B", 110, 50));
        assertTrue(claim("EVENT-25", "worker-B", 111, 50));
        assertTrue(fail("EVENT-25", "worker-B", 112, 3));
        assertFalse(claim("EVENT-25", "worker-C", 131, 50));
        assertTrue(claim("EVENT-25", "worker-C", 132, 50));
        assertEquals(2, jdbc.queryForObject("select failures from delivery_outbox where event_id = 'EVENT-25'", Integer.class));
    }

    @Test void retryBudgetMovesPoisonEventOutOfPendingClaims() {
        accept("EVENT-26", "SKU-17", 1, false);
        for (int attempt = 0; attempt < 3; attempt++) {
            long now = 100 + attempt * 100L;
            String token = "worker-" + attempt;
            assertTrue(claim("EVENT-26", token, now, 50));
            assertTrue(fail("EVENT-26", token, now + 1, 3));
        }
        assertEquals("DEAD", jdbc.queryForObject("select status from delivery_outbox where event_id = 'EVENT-26'", String.class));
        assertFalse(claim("EVENT-26", "worker-late", 1000, 50));
        assertEquals(10, jdbc.queryForObject("select available from stock_balance where sku = 'SKU-17'", Integer.class));
    }

    @Test void expiredLeaseRejectsStaleAcknowledgementAfterReclaim() {
        accept("EVENT-27", "SKU-17", 1, false);
        assertTrue(claim("EVENT-27", "worker-A", 100, 20));
        assertFalse(acknowledge("EVENT-27", "worker-A", 120));
        assertTrue(claim("EVENT-27", "worker-B", 120, 20));
        assertFalse(acknowledge("EVENT-27", "worker-A", 121));
        assertTrue(acknowledge("EVENT-27", "worker-B", 121));
    }
}
