package in.aitrove.contracts;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

import static org.junit.jupiter.api.Assertions.*;

/** A small H2 expand/backfill/contract exercise, not a Flyway deployment. */
class SchemaEvolutionContractTest {
    private JdbcTemplate jdbc;

    @BeforeEach void database() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:migration_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(source);
        jdbc.execute("create table shipment_receipt (receipt_id bigint primary key, amount_minor int not null)");
        jdbc.update("insert into shipment_receipt values (101, 700)");
    }

    @Test void nullableExpansionAcceptsOldWriterAndBackfillPreservesRows() {
        jdbc.execute("alter table shipment_receipt add column tenant_id varchar(40)");
        jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (102, 500)");
        assertEquals(2, jdbc.queryForObject("select count(*) from shipment_receipt", Integer.class));
        jdbc.update("update shipment_receipt set tenant_id = 'legacy' where tenant_id is null");
        assertEquals(2, jdbc.queryForObject(
            "select count(*) from shipment_receipt where tenant_id = 'legacy'", Integer.class));
    }

    @Test void contractRejectsOldWriterOnlyAfterBackfill() {
        jdbc.execute("alter table shipment_receipt add column tenant_id varchar(40)");
        jdbc.update("update shipment_receipt set tenant_id = 'legacy' where tenant_id is null");
        jdbc.execute("alter table shipment_receipt alter column tenant_id set not null");
        assertThrows(DataIntegrityViolationException.class, () ->
            jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (102, 500)"));
        jdbc.update("insert into shipment_receipt(receipt_id, amount_minor, tenant_id) values (103, 900, 'east')");
        assertEquals(2, jdbc.queryForObject("select count(*) from shipment_receipt", Integer.class));
        assertEquals("east", jdbc.queryForObject(
            "select tenant_id from shipment_receipt where receipt_id = 103", String.class));
    }
}
