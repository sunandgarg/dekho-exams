package in.aitrove.contracts;

import java.io.IOException;
import java.util.UUID;

import javax.sql.DataSource;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;

public class CheckedRollbackRuleTest {
    public static class ReceiptImportService {
        private final JdbcTemplate jdbc;
        ReceiptImportService(JdbcTemplate jdbc) { this.jdbc = jdbc; }

        @Transactional
        public void uncheckedFailure() {
            jdbc.update("insert into receipt_import (receipt_id) values (?)", "R-unchecked");
            throw new IllegalStateException("reject import");
        }

        @Transactional
        public void checkedFailure() throws IOException {
            jdbc.update("insert into receipt_import (receipt_id) values (?)", "R-checked");
            throw new IOException("reject import");
        }

        @Transactional(rollbackFor = IOException.class)
        public void checkedFailureWithRule() throws IOException {
            jdbc.update("insert into receipt_import (receipt_id) values (?)", "R-explicit");
            throw new IOException("reject import");
        }
    }

    @Configuration @EnableTransactionManagement
    static class Config {
        @Bean DataSource dataSource() {
            return new DriverManagerDataSource("jdbc:h2:mem:rollback_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        }
        @Bean JdbcTemplate jdbcTemplate(DataSource dataSource) { return new JdbcTemplate(dataSource); }
        @Bean PlatformTransactionManager transactionManager(DataSource dataSource) {
            return new DataSourceTransactionManager(dataSource);
        }
        @Bean ReceiptImportService receiptImportService(JdbcTemplate jdbc) { return new ReceiptImportService(jdbc); }
    }

    @Test void checkedExceptionCommitsByDefaultUnlessRollbackRuleIsExplicit() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            var jdbc = context.getBean(JdbcTemplate.class);
            jdbc.execute("create table receipt_import (receipt_id varchar(40) primary key)");
            var service = context.getBean(ReceiptImportService.class);
            assertThrows(IllegalStateException.class, service::uncheckedFailure);
            assertEquals(0L, count(jdbc));
            assertThrows(IOException.class, service::checkedFailure);
            assertEquals(1L, count(jdbc));
            assertThrows(IOException.class, service::checkedFailureWithRule);
            assertEquals(1L, count(jdbc));
        }
    }

    private static long count(JdbcTemplate jdbc) {
        return jdbc.queryForObject("select count(*) from receipt_import", Long.class);
    }
}
