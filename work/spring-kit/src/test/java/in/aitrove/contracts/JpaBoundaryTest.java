package in.aitrove.contracts;
import org.junit.jupiter.api.*;
import jakarta.persistence.*;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import static org.junit.jupiter.api.Assertions.*;
public class JpaBoundaryTest {
    JpaContracts kit;
    @BeforeEach void open() {kit=new JpaContracts();kit.seed();}
    @AfterEach void close() {kit.close();}
    @Test void managedMutationFlushesOnCommit() {
        var tx=new TransactionTemplate(new JpaTransactionManager(kit.factory));
        tx.executeWithoutResult(status -> {
            EntityManager manager=org.springframework.orm.jpa.EntityManagerFactoryUtils.getTransactionalEntityManager(kit.factory);
            manager.find(JpaContracts.StockAccount.class,1L).available=80;
        });
        try (var manager=kit.factory.createEntityManager()) {assertEquals(80,manager.find(JpaContracts.StockAccount.class,1L).available);}
    }
    @Test void detachedMutationDoesNotWriteItself() {
        JpaContracts.StockAccount detached;
        try (var manager=kit.factory.createEntityManager()) {detached=manager.find(JpaContracts.StockAccount.class,1L);}
        detached.available=7;
        try (var manager=kit.factory.createEntityManager()) {assertEquals(100,manager.find(JpaContracts.StockAccount.class,1L).available);}
    }
    @Test void staleVersionRejectsSecondWriter() {
        try (var first=kit.factory.createEntityManager();var second=kit.factory.createEntityManager()) {
            var original=first.find(JpaContracts.StockAccount.class,1L);
            var stale=second.find(JpaContracts.StockAccount.class,1L);
            first.getTransaction().begin();original.available=90;first.getTransaction().commit();
            second.getTransaction().begin();stale.available=70;
            assertThrows(OptimisticLockException.class,second::flush);
            second.getTransaction().rollback();
        }
    }
    @Test void lazyTraversalCountsOneQueryPerDistinctAccount() {
        kit.statistics().clear();
        try (var manager=kit.factory.createEntityManager()) {
            var lines=manager.createQuery("select line from StockLine line order by line.id",JpaContracts.StockLine.class).getResultList();
            assertEquals(0,lines.get(0).account.available); // direct field access does not initialize a proxy
            int total=0;for(var line:lines)total+=line.account.getAvailable();
            assertEquals(300,total);assertEquals(4,kit.statistics().getPrepareStatementCount());
        }
    }
    @Test void fetchJoinLoadsAccountsInOneStatement() {
        kit.statistics().clear();
        try(var manager=kit.factory.createEntityManager()) {
            var lines=manager.createQuery("select line from StockLine line join fetch line.account order by line.id",JpaContracts.StockLine.class).getResultList();
            int total=0;for(var line:lines)total+=line.account.getAvailable();
            assertEquals(300,total);assertEquals(1,kit.statistics().getPrepareStatementCount());
        }
    }
}
