package in.aitrove.contracts;

import java.util.UUID;

import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;

import static org.junit.jupiter.api.Assertions.*;

/** Check Boot's migration startup path separately from direct Flyway API calls. */
class BootFlywayStartupTest {
    @SpringBootConfiguration(proxyBeanMethods = false)
    @EnableAutoConfiguration
    static class MigrationApplication { }

    private String databaseUrl() {
        return "jdbc:h2:mem:boot_flyway_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1";
    }

    private ConfigurableApplicationContext start(String url, int target) {
        return new SpringApplicationBuilder(MigrationApplication.class)
            .web(WebApplicationType.NONE)
            .logStartupInfo(false)
            .properties("spring.main.banner-mode=off",
                "spring.datasource.username=sa",
                "spring.datasource.password=",
                "spring.sql.init.mode=never",
                "spring.jpa.hibernate.ddl-auto=none",
                "spring.flyway.locations=classpath:db/relay-migration",
                "spring.flyway.target=" + target)
            .run("--spring.datasource.url=" + url);
    }

    @Test void bootAppliesEachStageBeforeTheApplicationReadsRows() {
        String url = databaseUrl();
        try (var context = start(url, 2)) {
            assertNotNull(context.getBean(Flyway.class));
            var jdbc = context.getBean(JdbcTemplate.class);
            assertEquals(2, jdbc.queryForObject(
                "select count(*) from \"flyway_schema_history\" where \"version\" is not null", Integer.class));
            jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (102, 500)");
            assertEquals(2, jdbc.queryForObject(
                "select count(*) from shipment_receipt where tenant_id is null", Integer.class));
        }
        try (var context = start(url, 3)) {
            var jdbc = context.getBean(JdbcTemplate.class);
            assertEquals(3, jdbc.queryForObject(
                "select count(*) from \"flyway_schema_history\" where \"version\" is not null", Integer.class));
            assertEquals(0, jdbc.queryForObject(
                "select count(*) from shipment_receipt where tenant_id is null", Integer.class));
            assertThrows(DataIntegrityViolationException.class, () ->
                jdbc.update("insert into shipment_receipt(receipt_id, amount_minor) values (103, 900)"));
            jdbc.update("insert into shipment_receipt(receipt_id, amount_minor, tenant_id) values (104, 900, 'east')");
        }
    }

    @Test void invalidHistoryPreventsTheNextBootStartup() {
        String url = databaseUrl();
        try (var context = start(url, 3)) {
            context.getBean(JdbcTemplate.class).update(
                "update \"flyway_schema_history\" set \"checksum\" = \"checksum\" + 1 where \"version\" = '2'");
        }
        assertThrows(RuntimeException.class, () -> start(url, 3));
    }
}
