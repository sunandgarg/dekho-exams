package in.aitrove.contracts;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.DependsOn;
import org.springframework.context.annotation.Lazy;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class LifecycleAndMvcDispatchContractTest {
    static final AtomicInteger constructed = new AtomicInteger();
    record ReportIndex(int version) {}

    @Configuration(proxyBeanMethods = false)
    static class LazyIndexConfig {
        @Bean @Lazy ReportIndex reportIndex() {
            constructed.incrementAndGet();
            return new ReportIndex(47);
        }
    }

    static class EagerReportService {
        final ReportIndex index;
        EagerReportService(ReportIndex index) { this.index = index; }
    }

    @Configuration(proxyBeanMethods = false)
    static class EagerConsumerConfig {
        @Bean @Lazy ReportIndex reportIndex() {
            constructed.incrementAndGet();
            return new ReportIndex(47);
        }
        @Bean EagerReportService reportService(ReportIndex index) {
            return new EagerReportService(index);
        }
    }

    @Test void lazySingletonWaitsOnlyUntilItIsRequestedOrNeededByEagerBean() {
        constructed.set(0);
        try (var lazy = new AnnotationConfigApplicationContext(LazyIndexConfig.class)) {
            assertEquals(0, constructed.get());
            assertEquals(47, lazy.getBean(ReportIndex.class).version());
            assertEquals(1, constructed.get());
        }
        constructed.set(0);
        try (var eager = new AnnotationConfigApplicationContext(EagerConsumerConfig.class)) {
            assertEquals(1, constructed.get());
            assertNotNull(eager.getBean(EagerReportService.class).index);
        }
    }

    interface PricingIndex { int rate(); }
    static class LoadedPricingIndex implements PricingIndex {
        LoadedPricingIndex() { constructed.incrementAndGet(); }
        public int rate() { return 47; }
    }
    record PricingService(PricingIndex index) {}

    @Configuration(proxyBeanMethods = false)
    static class LazyInjectionConfig {
        @Bean @Lazy PricingIndex pricingIndex() { return new LoadedPricingIndex(); }
        @Bean PricingService pricingService(@Lazy PricingIndex index) {
            return new PricingService(index);
        }
    }

    @Test void lazyInjectionProxyDelaysAnEagerServicesDependency() {
        constructed.set(0);
        try (var context = new AnnotationConfigApplicationContext(LazyInjectionConfig.class)) {
            assertEquals(0, constructed.get());
            assertEquals(47, context.getBean(PricingService.class).index().rate());
            assertEquals(1, constructed.get());
        }
    }

    static final List<String> lifecycle = new ArrayList<>();
    static class Stage {
        final String name;
        Stage(String name) { this.name = name; }
        void start() { lifecycle.add("start:" + name); }
        void stop() { lifecycle.add("stop:" + name); }
    }

    @Configuration(proxyBeanMethods = false)
    static class StageConfig {
        @Bean(initMethod = "start", destroyMethod = "stop")
        Stage registry() { return new Stage("registry"); }
        @Bean(initMethod = "start", destroyMethod = "stop")
        @DependsOn("registry")
        Stage intake() { return new Stage("intake"); }
    }

    @Test void dependsOnForcesStartupAndReverseShutdownOrder() {
        lifecycle.clear();
        try (var context = new AnnotationConfigApplicationContext(StageConfig.class)) {
            assertEquals(List.of("start:registry", "start:intake"), lifecycle);
        }
        assertEquals(List.of("start:registry", "start:intake",
                "stop:intake", "stop:registry"), lifecycle);
    }

    @RestController
    static class ExportController {
        @GetMapping(path = "/contract/receipt-export", params = "format=csv")
        String csv() { return "receipt,amount\nRC-47,4725"; }
        @GetMapping(path = "/contract/receipt-export", params = "format=json")
        String json() { return "{\"receipt\":\"RC-47\",\"amount\":4725}"; }
    }

    @Test void queryParameterConditionsSelectOneHandlerAndRejectUnknownFormat() throws Exception {
        var mvc = MockMvcBuilders.standaloneSetup(new ExportController()).build();
        mvc.perform(get("/contract/receipt-export").param("format", "csv"))
                .andExpect(status().isOk()).andExpect(content().string("receipt,amount\nRC-47,4725"));
        mvc.perform(get("/contract/receipt-export").param("format", "json"))
                .andExpect(status().isOk()).andExpect(content().string("{\"receipt\":\"RC-47\",\"amount\":4725}"));
        mvc.perform(get("/contract/receipt-export").param("format", "xml"))
                .andExpect(status().isBadRequest());
    }

    @RestController
    static class LocalErrorController {
        @GetMapping("/contract/local-conflict")
        String read() { throw new IllegalStateException("conflict"); }
        @ExceptionHandler(IllegalStateException.class)
        ResponseEntity<String> local(IllegalStateException rejected) {
            return ResponseEntity.status(HttpStatus.CONFLICT).body("receipt conflict");
        }
    }

    @RestController
    static class GlobalErrorController {
        @GetMapping("/contract/global-conflict")
        String read() { throw new IllegalStateException("conflict"); }
    }

    @RestControllerAdvice
    static class GlobalErrorAdvice {
        @ExceptionHandler(IllegalStateException.class)
        ResponseEntity<String> global(IllegalStateException rejected) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("internal failure");
        }
    }

    @Test void controllerLocalExceptionHandlerWinsBeforeGlobalAdvice() throws Exception {
        var mvc = MockMvcBuilders.standaloneSetup(
                new LocalErrorController(), new GlobalErrorController())
                .setControllerAdvice(new GlobalErrorAdvice()).build();
        mvc.perform(get("/contract/local-conflict"))
                .andExpect(status().isConflict()).andExpect(content().string("receipt conflict"));
        mvc.perform(get("/contract/global-conflict"))
                .andExpect(status().isInternalServerError()).andExpect(content().string("internal failure"));
    }

    @RestController
    static class ScopedReceiptController {
        @GetMapping("/contract/scoped-receipt")
        String read() { throw new IllegalArgumentException("invalid receipt"); }
    }

    @RestController
    static class OtherReceiptController {
        @GetMapping("/contract/other-receipt")
        String read() { throw new IllegalArgumentException("invalid receipt"); }
    }

    @RestControllerAdvice(assignableTypes = ScopedReceiptController.class)
    @Order(10)
    static class ScopedReceiptAdvice {
        @ExceptionHandler(IllegalArgumentException.class)
        ResponseEntity<String> rejected(IllegalArgumentException invalid) {
            return ResponseEntity.unprocessableEntity().body("invalid scoped receipt");
        }
    }

    @RestControllerAdvice
    @Order(20)
    static class OtherReceiptAdvice {
        @ExceptionHandler(IllegalArgumentException.class)
        ResponseEntity<String> rejected(IllegalArgumentException invalid) {
            return ResponseEntity.internalServerError().body("unclassified input");
        }
    }

    @Test void adviceSelectorOnlyHandlesItsAssignedController() throws Exception {
        var mvc = MockMvcBuilders.standaloneSetup(
                new ScopedReceiptController(), new OtherReceiptController())
                .setControllerAdvice(new ScopedReceiptAdvice(), new OtherReceiptAdvice()).build();
        mvc.perform(get("/contract/scoped-receipt"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(content().string("invalid scoped receipt"));
        mvc.perform(get("/contract/other-receipt"))
                .andExpect(status().isInternalServerError())
                .andExpect(content().string("unclassified input"));
    }

    static final List<String> runnerEvents = new ArrayList<>();
    @Configuration(proxyBeanMethods = false)
    static class RunnerConfig {
        @Bean @Order(10)
        ApplicationRunner validateBatch() {
            return arguments -> runnerEvents.add("typed:" + arguments.getOptionValues("batch.size").get(0));
        }
        @Bean @Order(20)
        CommandLineRunner inspectRawArguments() {
            return arguments -> runnerEvents.add("raw:" + arguments[1]);
        }
    }

    @Test void bootRunnersReceiveTypedAndRawArgumentsInDeclaredOrder() {
        runnerEvents.clear();
        try (var context = new SpringApplicationBuilder(RunnerConfig.class)
                .web(WebApplicationType.NONE).logStartupInfo(false)
                .run("--batch.size=47", "tenant-west")) {
            assertEquals(List.of("typed:47", "raw:tenant-west"), runnerEvents);
        }
    }

    @Configuration(proxyBeanMethods = false)
    static class UnsafeRunnerConfig {
        @Bean ApplicationRunner rejectUnsafeSettings() {
            return arguments -> { throw new IllegalStateException("unsafe batch setting"); };
        }
    }

    @Test void failingApplicationRunnerPreventsSuccessfulBootStartup() {
        RuntimeException rejected = assertThrows(RuntimeException.class, () ->
                new SpringApplicationBuilder(UnsafeRunnerConfig.class)
                        .web(WebApplicationType.NONE).logStartupInfo(false).run());
        Throwable cause = rejected;
        while (cause.getCause() != null) cause = cause.getCause();
        assertEquals("unsafe batch setting", cause.getMessage());
    }
}
