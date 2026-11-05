package in.aitrove.learning;
import java.util.UUID;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
public class JdbcReceiptLedger {
    private final JdbcTemplate jdbc;
    private final TransactionTemplate transactions;
    public JdbcReceiptLedger() {
        DriverManagerDataSource database = new DriverManagerDataSource(
            "jdbc:h2:mem:ledger_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
        jdbc = new JdbcTemplate(database);
        transactions = new TransactionTemplate(new DataSourceTransactionManager(database));
        jdbc.execute("create table receipt (id bigint primary key, amount_minor int check(amount_minor > 0))");
    }
    public void add(long id, int amount) { jdbc.update("insert into receipt(id,amount_minor) values (?,?)", id, amount); }
    public int count() { return jdbc.queryForObject("select count(*) from receipt", Integer.class); }
    public void batchThatFails() {
        transactions.executeWithoutResult(status -> { add(1, 40); add(2, -7); });
    }
    public void rollbackOnly() {
        transactions.executeWithoutResult(status -> { add(3, 60); status.setRollbackOnly(); });
    }
    public static void main(String[] args) {
        JdbcReceiptLedger ledger = new JdbcReceiptLedger();
        try { ledger.batchThatFails(); } catch (org.springframework.dao.DataIntegrityViolationException rejected) {
            System.out.println("constraint rejected");
        }
        System.out.println("after failure=" + ledger.count());
        ledger.rollbackOnly(); System.out.println("after rollback=" + ledger.count());
        ledger.add(4, 80); System.out.println("after commit=" + ledger.count());
    }
}
