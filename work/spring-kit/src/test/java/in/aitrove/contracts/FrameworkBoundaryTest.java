package in.aitrove.contracts;
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
