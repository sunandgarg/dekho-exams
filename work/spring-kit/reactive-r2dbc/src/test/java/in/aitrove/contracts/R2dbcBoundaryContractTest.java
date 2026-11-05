package in.aitrove.contracts;

import java.util.UUID;

import io.r2dbc.spi.ConnectionFactories;
import io.r2dbc.spi.ConnectionFactory;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.r2dbc.connection.R2dbcTransactionManager;
import org.springframework.r2dbc.core.DatabaseClient;
import org.springframework.transaction.reactive.TransactionalOperator;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.junit.jupiter.api.Assertions.*;

class R2dbcBoundaryContractTest {
    private DatabaseClient database;
    private TransactionalOperator transactions;

    @BeforeEach
    void prepareDatabase() {
        ConnectionFactory connections = ConnectionFactories.get(
                "r2dbc:h2:mem:///reactive_receipts_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1");
        database = DatabaseClient.create(connections);
        transactions = TransactionalOperator.create(new R2dbcTransactionManager(connections));
        database.sql("create table stock_balance(sku varchar(80) primary key, tenant varchar(80) not null, available int not null check(available >= 0), version int not null)")
                .then().block();
        database.sql("create table applied_reservation(event_id varchar(80) primary key)").then().block();
        database.sql("insert into stock_balance(sku, tenant, available, version) values (:sku, :tenant, :available, :version)")
                .bind("sku", "SKU-47").bind("tenant", "north")
                .bind("available", 19).bind("version", 3).then().block();
    }

    @Test
    void sqlPublisherDoesNotRunBeforeSubscription() {
        Mono<Long> debit = database.sql(
                "update stock_balance set available = available - :units where sku = :sku and available >= :units")
                .bind("units", 7).bind("sku", "SKU-47").fetch().rowsUpdated();
        assertEquals(19, available());
        StepVerifier.create(debit).expectNext(1L).verifyComplete();
        assertEquals(12, available());
    }

    @Test
    void boundIdentifierIsDataRatherThanSql() {
        Mono<Integer> found = database.sql("select available from stock_balance where sku = :sku")
                .bind("sku", "SKU-47' or '1'='1")
                .map((row, metadata) -> row.get("available", Integer.class)).one();
        StepVerifier.create(found).verifyComplete();
        assertEquals(19, available());
    }

    @Test
    void transactionRollsBackMarkerAfterRejectedDebit() {
        Mono<Void> command = reserve("EVT-48", "north", "SKU-47", 20, 3);
        StepVerifier.create(command).expectError(IllegalStateException.class).verify();
        assertEquals(19, available());
        assertEquals(0, appliedCount());
    }

    @Test
    void transactionCommitsMarkerAndVersionedDebitTogether() {
        StepVerifier.create(reserve("EVT-47", "north", "SKU-47", 7, 3)).verifyComplete();
        assertEquals(12, available());
        assertEquals(4, version());
        assertEquals(1, appliedCount());
    }

    @Test
    void staleVersionRollsBackEventMarker() {
        StepVerifier.create(reserve("EVT-49", "north", "SKU-47", 2, 2))
                .expectError(IllegalStateException.class).verify();
        assertEquals(19, available());
        assertEquals(0, appliedCount());
    }

    @Test
    void wrongTenantRollsBackEventMarker() {
        StepVerifier.create(reserve("EVT-50", "south", "SKU-47", 2, 3))
                .expectError(IllegalStateException.class).verify();
        assertEquals(19, available());
        assertEquals(0, appliedCount());
    }

    private Mono<Void> reserve(String eventId, String tenant, String sku, int units, int expectedVersion) {
        if (units <= 0) return Mono.error(new IllegalArgumentException("units must be positive"));
        return database.sql("insert into applied_reservation(event_id) values (:eventId)")
                .bind("eventId", eventId).fetch().rowsUpdated()
                .then(database.sql("update stock_balance set available = available - :units, version = version + 1 "
                        + "where sku = :sku and tenant = :tenant and version = :expectedVersion and available >= :units")
                        .bind("units", units).bind("sku", sku).bind("tenant", tenant)
                        .bind("expectedVersion", expectedVersion).fetch().rowsUpdated())
                .flatMap(changed -> changed == 1 ? Mono.<Void>empty()
                        : Mono.error(new IllegalStateException("reservation rejected")))
                .as(transactions::transactional);
    }

    private int available() {
        return database.sql("select available from stock_balance where sku = :sku")
                .bind("sku", "SKU-47")
                .map((row, metadata) -> row.get("available", Integer.class)).one().block();
    }

    private int version() {
        return database.sql("select version from stock_balance where sku = :sku")
                .bind("sku", "SKU-47")
                .map((row, metadata) -> row.get("version", Integer.class)).one().block();
    }

    private int appliedCount() {
        return database.sql("select count(*) as events from applied_reservation")
                .map((row, metadata) -> row.get("events", Long.class)).one().block().intValue();
    }
}
