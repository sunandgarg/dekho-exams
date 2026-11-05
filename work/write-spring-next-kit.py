import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];kit=ROOT/'work/spring-kit'
pom=kit/'pom.xml';text=pom.read_text()
deps=[('org.springframework','spring-orm'),('org.hibernate.orm','hibernate-core'),('io.projectreactor','reactor-core'),('io.projectreactor','reactor-test')]
for group,artifact in deps:
 if '<artifactId>'+artifact+'</artifactId>' not in text:
  text=text.replace('</dependencies>','<dependency><groupId>'+group+'</groupId><artifactId>'+artifact+'</artifactId>'+('<scope>test</scope>' if artifact=='reactor-test' else '')+'</dependency></dependencies>')
pom.write_text(text)
def write(name,text,test=False):
 dest=kit/('src/test/java/in/aitrove/contracts' if test else 'src/main/java/in/aitrove/contracts');dest.mkdir(parents=True,exist_ok=True);(dest/(name+'.java')).write_text(text)
write('JpaContracts','''package in.aitrove.contracts;
import jakarta.persistence.*;
import java.util.UUID;
import org.hibernate.SessionFactory;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import java.util.Properties;
public class JpaContracts implements AutoCloseable {
    @Entity(name="StockAccount") @Table(name="stock_account")
    public static class StockAccount {
        @Id public Long id;
        @Version public Long version;
        public int available;
        protected StockAccount() {}
        public int getAvailable() {return available;}
        public StockAccount(long id,int available) { this.id=id; this.available=available; }
    }
    @Entity(name="StockLine") @Table(name="stock_line")
    public static class StockLine {
        @Id public Long id;
        @ManyToOne(fetch=FetchType.LAZY,optional=false) @JoinColumn(name="account_id")
        public StockAccount account;
        public int units;
        protected StockLine() {}
        public StockLine(long id,StockAccount account,int units) { this.id=id;this.account=account;this.units=units; }
    }
    public final EntityManagerFactory factory;
    public JpaContracts() {
        var builder=new LocalContainerEntityManagerFactoryBean();
        builder.setDataSource(new DriverManagerDataSource("jdbc:h2:mem:jpa_"+UUID.randomUUID()+";DB_CLOSE_DELAY=-1","sa",""));
        builder.setPackagesToScan("in.aitrove.contracts");
        builder.setJpaVendorAdapter(new HibernateJpaVendorAdapter());
        Properties settings=new Properties();
        settings.put("hibernate.hbm2ddl.auto","create-drop");
        settings.put("hibernate.generate_statistics","true");
        builder.setJpaProperties(settings); builder.afterPropertiesSet();
        factory=builder.getObject();
    }
    public void seed() {
        try (EntityManager manager=factory.createEntityManager()) {
            manager.getTransaction().begin();
            for (long id=1;id<=3;id++) {
                StockAccount account=new StockAccount(id,100);
                manager.persist(account); manager.persist(new StockLine(id,account,10));
            }
            manager.getTransaction().commit();
        }
    }
    public org.hibernate.stat.Statistics statistics() { return factory.unwrap(SessionFactory.class).getStatistics(); }
    public void close() { factory.close(); }
}
''')
write('TransactionContracts','''package in.aitrove.contracts;
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
''')
write('CommitEvents','''package in.aitrove.contracts;
import java.util.ArrayList;
import java.util.List;
import org.springframework.transaction.event.*;
public class CommitEvents {
    public record ImportedReceipt(int id) {}
    public final List<Integer> committed=new ArrayList<>();
    @TransactionalEventListener(phase=TransactionPhase.AFTER_COMMIT)
    public void committed(ImportedReceipt event) { committed.add(event.id()); }
}
''')
write('AuthorizedReceiptRead','''package in.aitrove.contracts;
import org.springframework.security.access.prepost.PreAuthorize;
public class AuthorizedReceiptRead {
    @PreAuthorize("hasAuthority('receipt:read')")
    public String receipt(long id) { return "receipt:"+id; }
}
''')
write('BoundedImportMetrics','''package in.aitrove.contracts;
import io.micrometer.core.instrument.MeterRegistry;
public class BoundedImportMetrics {
    public enum Outcome { ACCEPTED, REJECTED }
    private final MeterRegistry registry;
    public BoundedImportMetrics(MeterRegistry registry) { this.registry=registry; }
    public void record(Outcome outcome) {
        registry.counter("receipt.import.records", "outcome",outcome.name()).increment();
    }
}
''')
write('ReactiveReceiptDemand','''package in.aitrove.contracts;
import reactor.core.publisher.Flux;
import java.util.concurrent.atomic.AtomicBoolean;
public class ReactiveReceiptDemand {
    public static Flux<Integer> records(AtomicBoolean cancelled) {
        return Flux.range(1,5).doOnCancel(() -> cancelled.set(true));
    }
}
''')
write('JpaBoundaryTest','''package in.aitrove.contracts;
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
''',True)
write('FrameworkBoundaryTest','''package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.context.annotation.*;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.support.TransactionTemplate;
import reactor.test.StepVerifier;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
public class FrameworkBoundaryTest {
    @Test void requiresNewAuditSurvivesOuterRollback() {
        var ledger=new TransactionContracts();ledger.independentAuditSurvivesRollback();
        assertEquals(1,ledger.count());assertEquals("audit",ledger.jdbc.queryForObject("select message from journal",String.class));
    }
    @Test void requiredInnerRollbackRejectsOuterCommit() {
        var ledger=new TransactionContracts();assertThrows(UnexpectedRollbackException.class,ledger::joinedRollbackRejectsCommit);assertEquals(0,ledger.count());
    }
    @Configuration @EnableTransactionManagement
    public static class EventConfig {
        @Bean TransactionContracts ledger(){return new TransactionContracts();}
        @Bean PlatformTransactionManager transactionManager(TransactionContracts ledger){return ledger.manager;}
        @Bean CommitEvents listener(){return new CommitEvents();}
    }
    @Test void afterCommitDoesNotRunOnRollbackOrWithoutTransaction() {
        try(var context=new AnnotationConfigApplicationContext(EventConfig.class)) {
            var events=context.getBean(CommitEvents.class);
            var tx=new TransactionTemplate(context.getBean(PlatformTransactionManager.class));
            context.publishEvent(new CommitEvents.ImportedReceipt(1));assertTrue(events.committed.isEmpty());
            tx.executeWithoutResult(status->{context.publishEvent(new CommitEvents.ImportedReceipt(2));status.setRollbackOnly();});
            assertTrue(events.committed.isEmpty());
            tx.executeWithoutResult(status->context.publishEvent(new CommitEvents.ImportedReceipt(3)));
            assertEquals(List.of(3),events.committed);
        }
    }
    @Configuration @EnableMethodSecurity
    public static class AuthorizationConfig {
        @Bean AuthorizedReceiptRead reader(){return new AuthorizedReceiptRead();}
    }
    @Test void methodProxyChecksAuthorityAndDirectObjectDoesNot() {
        try(var context=new AnnotationConfigApplicationContext(AuthorizationConfig.class)) {
            var reader=context.getBean(AuthorizedReceiptRead.class);
            SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("reader","unused",List.of(new SimpleGrantedAuthority("receipt:read"))));
            assertEquals("receipt:7",reader.receipt(7));
            SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken("viewer","unused",List.of()));
            assertThrows(AccessDeniedException.class,()->reader.receipt(7));
            assertEquals("receipt:7",new AuthorizedReceiptRead().receipt(7));
        } finally {SecurityContextHolder.clearContext();}
    }
    @Test void enumOutcomeBoundsMeterIdentities() {
        var registry=new SimpleMeterRegistry();
        try {
            var metrics=new BoundedImportMetrics(registry);
            for(int i=0;i<100;i++)metrics.record(BoundedImportMetrics.Outcome.ACCEPTED);
            metrics.record(BoundedImportMetrics.Outcome.REJECTED);
            assertEquals(2,registry.getMeters().size());
            assertEquals(100,registry.get("receipt.import.records").tag("outcome","ACCEPTED").counter().count());
        } finally {registry.close();}
    }
    @Test void demandGatesValuesAndCancelStopsSubscription() {
        var cancelled=new AtomicBoolean();
        StepVerifier.create(ReactiveReceiptDemand.records(cancelled),0)
            .thenRequest(2).expectNext(1,2).thenCancel().verify(java.time.Duration.ofSeconds(2));
        assertTrue(cancelled.get());
    }
    @Test void completeDemandReceivesAllValues() {
        StepVerifier.create(ReactiveReceiptDemand.records(new AtomicBoolean()),0)
            .thenRequest(5).expectNext(1,2,3,4,5).verifyComplete();
    }
}
''',True)
print('Added isolated Spring/JPA/Reactor source and 12 boundary tests')
