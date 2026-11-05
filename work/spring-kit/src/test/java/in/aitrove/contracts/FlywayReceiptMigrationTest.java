package in.aitrove.contracts;

import java.util.UUID;

import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.exception.FlywayValidateException;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.junit.jupiter.api.Assertions.*;

/** Run committed, ordered migration files against an isolated H2 database. */
class FlywayReceiptMigrationTest {
    private final DriverManagerDataSource source = new DriverManagerDataSource(
        "jdbc:h2:mem:flyway_receipts_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
    private final JdbcTemplate jdbc = new JdbcTemplate(source);

    private Flyway migrationAt(String version) {
        return Flyway.configure().dataSource(source)
            .locations("classpath:db/relay-migration").target(version).load();
    }

    @Test void orderedFilesPreserveTheOldWriterUntilContract() {
        assertEquals(1, migrationAt("1").migrate().migrationsExecuted);
        assertEquals(1, jdbc.queryForObject("select count(*) from shipment_receipt", Integer.class));

        assertEquals(1, migrationAt("2").migrate().migrationsExecuted);
        jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (102, 500)");
        assertEquals(2, jdbc.queryForObject(
            "select count(*) from shipment_receipt where tenant_id is null", Integer.class));

        assertEquals(1, migrationAt("3").migrate().migrationsExecuted);
        assertEquals(0, jdbc.queryForObject(
            "select count(*) from shipment_receipt where tenant_id is null", Integer.class));
        assertThrows(DataIntegrityViolationException.class, () ->
            jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (103, 900)"));
        jdbc.update("insert into shipment_receipt(receipt_id, amount_minor, tenant_id) values (104, 900, 'east')");
        assertEquals(3, jdbc.queryForObject(
            "select count(*) from \"flyway_schema_history\" where \"success\" = true and \"version\" is not null", Integer.class));
        assertEquals(0, migrationAt("3").migrate().migrationsExecuted);
        migrationAt("3").validate();
    }

    @Test void changedRecordedChecksumFailsValidation() {
        migrationAt("3").migrate();
        jdbc.update("update \"flyway_schema_history\" set \"checksum\" = \"checksum\" + 1 where \"version\" = '2'");
        assertThrows(FlywayValidateException.class, () -> migrationAt("3").validate());
    }
}
