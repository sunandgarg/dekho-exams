package in.aitrove.learning;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import jakarta.validation.Validation;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.beans.factory.NoUniqueBeanDefinitionException;
import org.springframework.context.PayloadApplicationEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.aop.framework.ProxyFactory;
import org.aopalliance.intercept.MethodInterceptor;
import org.springframework.boot.context.properties.bind.Binder;
import org.springframework.boot.context.properties.source.MapConfigurationPropertySource;
import org.springframework.core.env.StandardEnvironment;
import org.springframework.core.env.MapPropertySource;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
public class CoreBoundaryTest {
    @Test void constructorWorksWithoutContainer() {
        assertEquals("csv:receipt", new ContainerContracts.ReceiptReport(new ContainerContracts.CsvExporter()).render());
    }
    @Test void contextCreatesAndReusesSingleton() {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.registerBean(ContainerContracts.Exporter.class, ContainerContracts.CsvExporter::new);
            context.registerBean(ContainerContracts.ReceiptReport.class); context.refresh();
            assertSame(context.getBean(ContainerContracts.ReceiptReport.class), context.getBean(ContainerContracts.ReceiptReport.class));
        }
    }
    @Test void qualifierSelectsArchive() {
        try (var context = new AnnotationConfigApplicationContext(QualifiedExportConfig.class)) {
            assertEquals("archive:receipt", context.getBean(ContainerContracts.ReceiptReport.class).render());
            assertThrows(NoUniqueBeanDefinitionException.class, () -> context.getBean(ContainerContracts.Exporter.class));
        }
    }
    @Test void providerResolvesFreshPrototype() {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.registerBean(ContainerContracts.ImportBuffer.class, ContainerContracts.ImportBuffer::new,
                definition -> definition.setScope(BeanDefinition.SCOPE_PROTOTYPE)); context.refresh();
            var provider = context.getBeanProvider(ContainerContracts.ImportBuffer.class);
            assertNotSame(provider.getObject(), provider.getObject());
        }
    }
    @Test void singletonDestroyedOnClose() {
        var context = new AnnotationConfigApplicationContext(); context.registerBean(ContainerContracts.ClosingChannel.class); context.refresh();
        var channel = context.getBean(ContainerContracts.ClosingChannel.class); assertFalse(channel.closed); context.close(); assertTrue(channel.closed);
    }
    @Test void ordinaryEventListenerRunsBeforeReturn() {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.refresh(); AtomicInteger events = new AtomicInteger();
            context.addApplicationListener((ApplicationListener<PayloadApplicationEvent<String>>) event -> events.incrementAndGet());
            context.publishEvent("receipt-created"); assertEquals(1, events.get());
        }
    }
    @Test void selfInvocationBypassesProxyAdvice() {
        AtomicInteger advice = new AtomicInteger(); ProxyFactory factory = new ProxyFactory(new ContainerContracts.CounterTarget());
        factory.addAdvice((MethodInterceptor) call -> { advice.incrementAndGet(); return call.proceed(); });
        ((ContainerContracts.Counter) factory.getProxy()).outer(); assertEquals(1, advice.get());
    }
    @Test void propertyBinderMapsDuration() {
        var source = new MapConfigurationPropertySource(Map.of("receipt.import.batch-size", "32", "receipt.import.timeout", "5s"));
        var config = new Binder(source).bind("receipt.import", ImportConfiguration.class).get();
        assertEquals(32, config.batchSize()); assertEquals(Duration.ofSeconds(5), config.timeout());
    }
    @Test void validationRejectsOutOfRangeBatch() {
        try (var factory = Validation.buildDefaultValidatorFactory()) {
            assertFalse(factory.getValidator().validate(new ImportConfiguration(0, Duration.ofSeconds(5))).isEmpty());
            assertTrue(factory.getValidator().validate(new ImportConfiguration(32, Duration.ofSeconds(5))).isEmpty());
        }
    }
    @Test void environmentProfileAndPropertyAreExplicit() {
        var environment = new StandardEnvironment(); environment.setActiveProfiles("test");
        environment.getPropertySources().addFirst(new MapPropertySource("fixture", Map.of("receipt.mode", "dry-run")));
        assertEquals("test", environment.getActiveProfiles()[0]); assertEquals("dry-run", environment.getRequiredProperty("receipt.mode"));
    }
    @Test void fallbackBeanBacksOffWhenUserBeanExists() {
        new ApplicationContextRunner().withUserConfiguration(FallbackExportConfig.class)
            .run(context -> assertEquals("fallback", context.getBean(ContainerContracts.Exporter.class).format()));
        new ApplicationContextRunner().withBean("custom", ContainerContracts.Exporter.class, () -> () -> "custom")
            .withUserConfiguration(FallbackExportConfig.class)
            .run(context -> { assertEquals(1, context.getBeansOfType(ContainerContracts.Exporter.class).size()); assertEquals("custom", context.getBean(ContainerContracts.Exporter.class).format()); });
    }
    @Test void cacheSeparatesTenantsAndAvoidsRepeatedLoader() {
        try (var context = new AnnotationConfigApplicationContext(ReceiptCacheBoundary.Config.class)) {
            var lookup = context.getBean(ReceiptCacheBoundary.Lookup.class);
            assertEquals("tenant-a:7", lookup.read("tenant-a", 7));
            assertEquals("tenant-a:7", lookup.read("tenant-a", 7));
            assertEquals("tenant-b:7", lookup.read("tenant-b", 7));
            var target = (ReceiptCacheBoundary.Lookup) ((org.springframework.aop.framework.Advised) lookup).getTargetSource().getTarget();
            assertEquals(2, target.calls.get());
        } catch (Exception failure) { throw new AssertionError(failure); }
    }
}
