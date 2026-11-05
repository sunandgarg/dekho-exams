package in.aitrove.contracts;

import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.jupiter.api.Assertions.*;

/** A local scheduled poller with a fake transport, not a broker integration test. */
class ScheduledOutboxPollerTest {
    private JdbcTemplate jdbc;
    private TransactionTemplate transactions;

    @BeforeEach void database() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:scheduled_relay_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        transactions = new TransactionTemplate(new DataSourceTransactionManager(source));
        jdbc.execute("""
            create table scheduled_outbox (
                event_id varchar(40) primary key, units int not null,
                state varchar(12) not null, claim_token varchar(40), lease_until bigint,
                next_due bigint not null, failures int not null)
            """);
        jdbc.execute("create table applied_event (event_id varchar(40) primary key)");
        jdbc.execute("create table stock_balance (sku varchar(40) primary key, available int not null)");
        jdbc.update("insert into stock_balance values ('SKU-29', 10)");
    }

    private void enqueue(String eventId, int units) {
        jdbc.update("insert into scheduled_outbox values (?, ?, 'PENDING', null, null, 0, 0)",
            eventId, units);
    }

    private void consumeLocally(String eventId) {
        try {
            transactions.executeWithoutResult(status -> {
                jdbc.update("insert into applied_event values (?)", eventId);
                int changed = jdbc.update("""
                    update stock_balance set available = available -
                        (select units from scheduled_outbox where event_id = ?)
                    where sku = 'SKU-29'
                    """, eventId);
                if (changed != 1) throw new IllegalStateException("missing stock row");
            });
        } catch (DuplicateKeyException alreadyApplied) {
            // The event was committed before the relay lost its acknowledgement.
        }
    }

    private final class Poller {
        private final Consumer<String> transport;
        private final Runnable onDelivered;

        Poller(Consumer<String> transport, Runnable onDelivered) {
            this.transport = transport;
            this.onDelivered = onDelivered;
        }

        int runBatch(int limit) {
            if (limit < 1) throw new IllegalArgumentException("limit must be positive");
            long now = System.currentTimeMillis();
            var due = jdbc.queryForList("""
                select event_id from scheduled_outbox
                where state = 'PENDING' and next_due <= ?
                  and (claim_token is null or lease_until <= ?)
                order by event_id limit ?
                """, String.class, now, now, limit);
            int processed = 0;
            for (String eventId : due) {
                String token = UUID.randomUUID().toString();
                long claimTime = System.currentTimeMillis();
                int claimed = jdbc.update("""
                    update scheduled_outbox set claim_token = ?, lease_until = ?
                    where event_id = ? and state = 'PENDING' and next_due <= ?
                      and (claim_token is null or lease_until <= ?)
                    """, token, claimTime + 1000, eventId, claimTime, claimTime);
                if (claimed == 0) continue;
                processed++;
                try {
                    transport.accept(eventId);
                    int acknowledged = jdbc.update("""
                        update scheduled_outbox set state = 'DELIVERED', claim_token = null, lease_until = null
                        where event_id = ? and state = 'PENDING' and claim_token = ? and lease_until > ?
                        """, eventId, token, System.currentTimeMillis());
                    if (acknowledged == 1) onDelivered.run();
                } catch (RuntimeException transportFailure) {
                    jdbc.update("""
                        update scheduled_outbox set failures = failures + 1, next_due = ?,
                            claim_token = null, lease_until = null
                        where event_id = ? and state = 'PENDING' and claim_token = ?
                          and lease_until > ?
                        """, System.currentTimeMillis() + 80, eventId, token,
                        System.currentTimeMillis());
                }
            }
            return processed;
        }
    }

    @Test void scheduledWorkerConsumesCommittedRowAndStops() throws InterruptedException {
        enqueue("EVENT-41", 3);
        var delivered = new CountDownLatch(1);
        var scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(1);
        scheduler.setThreadNamePrefix("aitrove-relay-test-");
        scheduler.initialize();
        try {
            var future = scheduler.scheduleWithFixedDelay(
                () -> new Poller(this::consumeLocally, delivered::countDown).runBatch(1),
                Duration.ofMillis(20));
            assertTrue(delivered.await(3, TimeUnit.SECONDS));
            future.cancel(false);
            assertTrue(future.isCancelled());
        } finally {
            scheduler.shutdown();
        }
        assertEquals("DELIVERED", jdbc.queryForObject(
            "select state from scheduled_outbox where event_id = 'EVENT-41'", String.class));
        assertEquals(7, jdbc.queryForObject(
            "select available from stock_balance where sku = 'SKU-29'", Integer.class));
    }

    @Test void failedTransportWaitsThenRetriesSameEvent() throws InterruptedException {
        enqueue("EVENT-42", 2);
        var attempts = new AtomicInteger();
        var delivered = new CountDownLatch(1);
        var scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(1);
        scheduler.initialize();
        try {
            var future = scheduler.scheduleWithFixedDelay(() -> new Poller(eventId -> {
                if (attempts.incrementAndGet() == 1) throw new IllegalStateException("fake transport down");
                consumeLocally(eventId);
            }, delivered::countDown).runBatch(1), Duration.ofMillis(20));
            assertTrue(delivered.await(3, TimeUnit.SECONDS));
            future.cancel(false);
        } finally {
            scheduler.shutdown();
        }
        assertEquals(2, attempts.get());
        assertEquals(1, jdbc.queryForObject(
            "select failures from scheduled_outbox where event_id = 'EVENT-42'", Integer.class));
        assertEquals("DELIVERED", jdbc.queryForObject(
            "select state from scheduled_outbox where event_id = 'EVENT-42'", String.class));
        assertEquals(8, jdbc.queryForObject(
            "select available from stock_balance where sku = 'SKU-29'", Integer.class));
    }

    @Test void onePollProcessesOnlyItsBatchBudget() {
        enqueue("EVENT-51", 1);
        enqueue("EVENT-52", 1);
        enqueue("EVENT-53", 1);
        var poller = new Poller(this::consumeLocally, () -> {});
        assertEquals(2, poller.runBatch(2));
        assertEquals(2, jdbc.queryForObject(
            "select count(*) from scheduled_outbox where state = 'DELIVERED'", Integer.class));
        assertEquals(1, jdbc.queryForObject(
            "select count(*) from scheduled_outbox where state = 'PENDING'", Integer.class));
        assertEquals(1, poller.runBatch(2));
        assertEquals(7, jdbc.queryForObject(
            "select available from stock_balance where sku = 'SKU-29'", Integer.class));
    }

    @Test void redeliveryAfterLostAcknowledgementDoesNotRepeatStockMutation() {
        enqueue("EVENT-61", 4);
        consumeLocally("EVENT-61");
        assertEquals(1, new Poller(this::consumeLocally, () -> {}).runBatch(1));
        assertEquals("DELIVERED", jdbc.queryForObject(
            "select state from scheduled_outbox where event_id = 'EVENT-61'", String.class));
        assertEquals(6, jdbc.queryForObject(
            "select available from stock_balance where sku = 'SKU-29'", Integer.class));
        assertEquals(1, jdbc.queryForObject("select count(*) from applied_event", Integer.class));
    }
}
