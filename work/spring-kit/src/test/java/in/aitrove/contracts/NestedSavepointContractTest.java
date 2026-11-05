package in.aitrove.contracts;

import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.jupiter.api.Assertions.*;

public class NestedSavepointContractTest {
    @Test void nestedFailureRollsBackToSavepointWhileOuterWorkCommits() {
        var source = new DriverManagerDataSource(
            "jdbc:h2:mem:savepoint_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        var jdbc = new JdbcTemplate(source);
        jdbc.execute("create table receipt_step (step varchar(40) primary key)");
        var manager = new DataSourceTransactionManager(source);
        manager.setNestedTransactionAllowed(true);
        var outer = new TransactionTemplate(manager);
        var nested = new TransactionTemplate(manager);
        nested.setPropagationBehavior(TransactionDefinition.PROPAGATION_NESTED);

        outer.executeWithoutResult(status -> {
            jdbc.update("insert into receipt_step values (?)", "accept");
            assertThrows(IllegalStateException.class, () -> nested.executeWithoutResult(child -> {
                jdbc.update("insert into receipt_step values (?)", "temporary-check");
                throw new IllegalStateException("reject nested step");
            }));
            jdbc.update("insert into receipt_step values (?)", "record-rejection");
        });
        List<String> steps = jdbc.queryForList("select step from receipt_step order by step", String.class);
        assertEquals(List.of("accept", "record-rejection"), steps);
    }
}
