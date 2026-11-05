package in.aitrove.contracts;

import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.junit.jupiter.api.Assertions.*;

/** Separate H2 connections race on one conditional claim; target-database behavior is untested. */
class ConcurrentOutboxLeaseTest {
    private JdbcTemplate jdbc;

    @BeforeEach void database() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:claim_race_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        jdbc.execute("""
            create table lease_event (
                event_id varchar(40) primary key, claim_token varchar(40), lease_until bigint,
                state varchar(12) not null)
            """);
        jdbc.update("insert into lease_event values ('EVENT-81', null, null, 'PENDING')");
    }

    private int claim(String token, long now, long until) {
        return jdbc.update("""
            update lease_event set claim_token = ?, lease_until = ?
            where event_id = 'EVENT-81' and state = 'PENDING'
              and (claim_token is null or lease_until <= ?)
            """, token, until, now);
    }

    private int renew(String token, long now, long until) {
        return jdbc.update("""
            update lease_event set lease_until = ?
            where event_id = 'EVENT-81' and state = 'PENDING' and claim_token = ?
              and lease_until > ? and lease_until < ?
            """, until, token, now, until);
    }

    @Test void twoConcurrentConnectionsYieldOneCurrentClaim() throws Exception {
        var ready = new CountDownLatch(2);
        var start = new CountDownLatch(1);
        var pool = Executors.newFixedThreadPool(2);
        try {
            var first = pool.submit(() -> {
                ready.countDown();
                if (!start.await(3, TimeUnit.SECONDS)) throw new IllegalStateException("start timeout");
                return claim("worker-A", 100, 200);
            });
            var second = pool.submit(() -> {
                ready.countDown();
                if (!start.await(3, TimeUnit.SECONDS)) throw new IllegalStateException("start timeout");
                return claim("worker-B", 100, 200);
            });
            assertTrue(ready.await(3, TimeUnit.SECONDS));
            start.countDown();
            assertEquals(1, first.get(5, TimeUnit.SECONDS) + second.get(5, TimeUnit.SECONDS));
            String owner = jdbc.queryForObject(
                "select claim_token from lease_event where event_id = 'EVENT-81'", String.class);
            assertTrue(owner.equals("worker-A") || owner.equals("worker-B"));
        } finally {
            start.countDown();
            pool.shutdownNow();
        }
    }

    @Test void renewalRequiresCurrentUnexpiredTokenAndLongerDeadline() {
        assertEquals(1, claim("worker-A", 100, 150));
        assertEquals(0, renew("worker-B", 120, 200));
        assertEquals(0, renew("worker-A", 120, 140));
        assertEquals(1, renew("worker-A", 120, 200));
        assertEquals(0, claim("worker-B", 160, 260));
        assertEquals(0, renew("worker-A", 200, 250));
        assertEquals(1, claim("worker-B", 200, 260));
        assertEquals(0, renew("worker-A", 210, 300));
        assertEquals(1, renew("worker-B", 210, 300));
        assertEquals(300L, jdbc.queryForObject(
            "select lease_until from lease_event where event_id = 'EVENT-81'", Long.class));
    }
}
