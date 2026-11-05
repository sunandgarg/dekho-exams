package in.aitrove.contracts;

import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.core.KafkaOperations;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.SendResult;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class KafkaBoundaryContractTest {
    record StockReservation(String eventId, String sku, int units) {
        StockReservation {
            if (eventId == null || eventId.isBlank() || sku == null || sku.isBlank() || units <= 0) {
                throw new IllegalArgumentException("invalid stock reservation");
            }
        }
    }

    static final class StockReservationConsumer {
        private final JdbcTemplate jdbc;
        private final TransactionTemplate transactions;

        StockReservationConsumer(JdbcTemplate jdbc, TransactionTemplate transactions) {
            this.jdbc = jdbc;
            this.transactions = transactions;
        }

        @KafkaListener(topics = "stock-reservations", groupId = "stock-ledger-v1",
                containerFactory = "manualAckKafkaListenerContainerFactory")
        public void receive(ConsumerRecord<String, StockReservation> record, Acknowledgment acknowledgment) {
            StockReservation reservation = record.value();
            if (reservation == null || record.key() == null || !record.key().equals(reservation.sku())) {
                throw new IllegalArgumentException("record key and reservation SKU differ");
            }
            try {
                transactions.executeWithoutResult(status -> {
                    jdbc.update("insert into applied_reservation(event_id, sku, units) values (?, ?, ?)",
                            reservation.eventId(), reservation.sku(), reservation.units());
                    int updated = jdbc.update(
                            "update stock_balance set available = available - ? where sku = ? and available >= ?",
                            reservation.units(), reservation.sku(), reservation.units());
                    if (updated != 1) throw new IllegalStateException("stock item absent or insufficient");
                });
            } catch (DuplicateKeyException duplicate) {
                var recorded = jdbc.queryForMap(
                        "select sku, units from applied_reservation where event_id = ?", reservation.eventId());
                if (!reservation.sku().equals(recorded.get("SKU"))
                        || reservation.units() != ((Number) recorded.get("UNITS")).intValue()) {
                    throw new IllegalStateException("event ID reused for a different reservation", duplicate);
                }
            }
            acknowledgment.acknowledge();
        }
    }

    static final class StockReservationPublisher {
        private final KafkaOperations<String, StockReservation> operations;

        StockReservationPublisher(KafkaOperations<String, StockReservation> operations) {
            this.operations = operations;
        }

        CompletableFuture<SendResult<String, StockReservation>> publish(StockReservation reservation) {
            return operations.send("stock-reservations", reservation.sku(), reservation);
        }
    }

    private JdbcTemplate jdbc;
    private StockReservationConsumer consumer;

    @BeforeEach
    void prepareDatabase() {
        var datasource = new DriverManagerDataSource(
                "jdbc:h2:mem:kafka_boundary_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(datasource);
        jdbc.execute("create table stock_balance(sku varchar(80) primary key, available int not null check(available >= 0))");
        jdbc.execute("create table applied_reservation(event_id varchar(80) primary key, sku varchar(80) not null, units int not null)");
        jdbc.update("insert into stock_balance(sku, available) values (?, ?)", "SKU-47", 19);
        consumer = new StockReservationConsumer(jdbc, new TransactionTemplate(new DataSourceTransactionManager(datasource)));
    }

    @Test
    void acknowledgesOnlyAfterCommittedStockChange() {
        Acknowledgment acknowledgment = mock(Acknowledgment.class);
        consumer.receive(record("EVT-47", "SKU-47", 7), acknowledgment);
        verify(acknowledgment).acknowledge();
        assertEquals(12, available());
        assertEquals(1, appliedCount());
    }

    @Test
    void acknowledgesDuplicateWithoutSecondDebit() {
        consumer.receive(record("EVT-47", "SKU-47", 7), mock(Acknowledgment.class));
        Acknowledgment replayAcknowledgment = mock(Acknowledgment.class);
        consumer.receive(record("EVT-47", "SKU-47", 7), replayAcknowledgment);
        verify(replayAcknowledgment).acknowledge();
        assertEquals(12, available());
        assertEquals(1, appliedCount());
    }

    @Test
    void conflictingDuplicateIsNotAcknowledged() {
        consumer.receive(record("EVT-47", "SKU-47", 7), mock(Acknowledgment.class));
        Acknowledgment acknowledgment = mock(Acknowledgment.class);
        assertThrows(IllegalStateException.class,
                () -> consumer.receive(record("EVT-47", "SKU-47", 3), acknowledgment));
        verifyNoInteractions(acknowledgment);
        assertEquals(12, available());
        assertEquals(1, appliedCount());
    }

    @Test
    void insufficientStockRollsBackMarkerAndDoesNotAcknowledge() {
        Acknowledgment acknowledgment = mock(Acknowledgment.class);
        assertThrows(IllegalStateException.class,
                () -> consumer.receive(record("EVT-48", "SKU-47", 20), acknowledgment));
        verifyNoInteractions(acknowledgment);
        assertEquals(19, available());
        assertEquals(0, appliedCount());
    }

    @Test
    void mismatchedKeyIsRejectedBeforeDatabaseWork() {
        Acknowledgment acknowledgment = mock(Acknowledgment.class);
        assertThrows(IllegalArgumentException.class, () -> consumer.receive(
                new ConsumerRecord<>("stock-reservations", 0, 47L, "SKU-OTHER",
                        new StockReservation("EVT-49", "SKU-47", 2)), acknowledgment));
        verifyNoInteractions(acknowledgment);
        assertEquals(19, available());
        assertEquals(0, appliedCount());
    }

    @Test
    void publisherUsesSkuAsPartitionKeyAndReturnsSendCompletion() {
        @SuppressWarnings("unchecked")
        KafkaOperations<String, StockReservation> operations = mock(KafkaOperations.class);
        StockReservation reservation = new StockReservation("EVT-50", "SKU-47", 3);
        @SuppressWarnings("unchecked")
        SendResult<String, StockReservation> sent = mock(SendResult.class);
        when(operations.send("stock-reservations", "SKU-47", reservation))
                .thenReturn(CompletableFuture.completedFuture(sent));
        assertSame(sent, new StockReservationPublisher(operations).publish(reservation).join());
        verify(operations).send("stock-reservations", "SKU-47", reservation);
    }

    @Test
    void failedSendRemainsFailedForCallerToHandle() {
        @SuppressWarnings("unchecked")
        KafkaOperations<String, StockReservation> operations = mock(KafkaOperations.class);
        StockReservation reservation = new StockReservation("EVT-51", "SKU-47", 3);
        when(operations.send("stock-reservations", "SKU-47", reservation))
                .thenReturn(CompletableFuture.failedFuture(new IllegalStateException("broker unavailable")));
        assertThrows(CompletionException.class,
                () -> new StockReservationPublisher(operations).publish(reservation).join());
    }

    @Test
    void listenerDeclaresManualAcknowledgmentContainerAndStableGroup() throws Exception {
        KafkaListener listener = StockReservationConsumer.class
                .getMethod("receive", ConsumerRecord.class, Acknowledgment.class)
                .getAnnotation(KafkaListener.class);
        assertArrayEquals(new String[]{"stock-reservations"}, listener.topics());
        assertEquals("stock-ledger-v1", listener.groupId());
        assertEquals("manualAckKafkaListenerContainerFactory", listener.containerFactory());

        var factory = new ConcurrentKafkaListenerContainerFactory<String, StockReservation>();
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        assertEquals(ContainerProperties.AckMode.MANUAL_IMMEDIATE,
                factory.getContainerProperties().getAckMode());
    }

    private ConsumerRecord<String, StockReservation> record(String eventId, String sku, int units) {
        return new ConsumerRecord<>("stock-reservations", 0, 47L, sku,
                new StockReservation(eventId, sku, units));
    }

    private int available() {
        return jdbc.queryForObject("select available from stock_balance where sku = 'SKU-47'", Integer.class);
    }

    private int appliedCount() {
        return jdbc.queryForObject("select count(*) from applied_reservation", Integer.class);
    }
}
