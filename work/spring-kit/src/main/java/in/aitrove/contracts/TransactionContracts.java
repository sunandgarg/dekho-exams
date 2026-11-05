package in.aitrove.contracts;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.*;
import org.springframework.transaction.*;
import org.springframework.transaction.support.TransactionTemplate;
public class TransactionContracts {
    public final JdbcTemplate jdbc;
    public final PlatformTransactionManager manager;
    public TransactionContracts() {
        var data=new DriverManagerDataSource("jdbc:h2:mem:propagation_"+UUID.randomUUID()+";DB_CLOSE_DELAY=-1","sa","");
        jdbc=new JdbcTemplate(data); manager=new DataSourceTransactionManager(data);
        jdbc.execute("create table journal(id int primary key, message varchar(30))");
    }
    public TransactionTemplate transaction(int propagation) {
        var tx=new TransactionTemplate(manager);tx.setPropagationBehavior(propagation);return tx;
    }
    public void independentAuditSurvivesRollback() {
        transaction(TransactionDefinition.PROPAGATION_REQUIRED).executeWithoutResult(outer -> {
            jdbc.update("insert into journal values(1,'pending')");
            transaction(TransactionDefinition.PROPAGATION_REQUIRES_NEW).executeWithoutResult(inner ->
                jdbc.update("insert into journal values(2,'audit')"));
            outer.setRollbackOnly();
        });
    }
    public void joinedRollbackRejectsCommit() {
        transaction(TransactionDefinition.PROPAGATION_REQUIRED).executeWithoutResult(outer -> {
            jdbc.update("insert into journal values(3,'pending')");
            transaction(TransactionDefinition.PROPAGATION_REQUIRED).executeWithoutResult(inner -> inner.setRollbackOnly());
        });
    }
    public int count() { return jdbc.queryForObject("select count(*) from journal",Integer.class); }
}
