package in.aitrove.contracts;
import org.springframework.data.jpa.repository.support.JpaRepositoryFactory;
import org.springframework.orm.jpa.*;
import org.springframework.transaction.support.TransactionTemplate;
public class RepositoryContracts implements AutoCloseable {
    public final JpaContracts data=new JpaContracts();
    public final StockRepository stocks;
    public final TransactionTemplate transaction;
    public RepositoryContracts() {
        data.seed();
        stocks=new JpaRepositoryFactory(SharedEntityManagerCreator.createSharedEntityManager(data.factory)).getRepository(StockRepository.class);
        transaction=new TransactionTemplate(new JpaTransactionManager(data.factory));
    }
    public void close(){data.close();}
}
