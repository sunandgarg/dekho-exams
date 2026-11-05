import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];kit=ROOT/'work/spring-kit'
def write(name,text,test=False):
 p=kit/('src/test/java/in/aitrove/learning' if test else 'src/main/java/in/aitrove/learning')/(name+'.java');p.write_text('package in.aitrove.learning;\n'+text.strip()+'\n')
write('ContainerContracts','''import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.PayloadApplicationEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.aop.framework.ProxyFactory;
import org.aopalliance.intercept.MethodInterceptor;
public class ContainerContracts {
    public interface Exporter { String format(); }
    public static class CsvExporter implements Exporter { public String format() { return "csv"; } }
    public static class ReceiptReport {
        private final Exporter exporter;
        public ReceiptReport(Exporter exporter) { this.exporter = exporter; }
        public String render() { return exporter.format() + ":receipt"; }
    }
    public static class ImportBuffer { private final int capacity = 32; public int capacity() { return capacity; } }
    public static class ClosingChannel implements DisposableBean {
        public boolean closed; public void destroy() { closed = true; }
    }
    public interface Counter { void outer(); void inner(); }
    public static class CounterTarget implements Counter {
        public void outer() { inner(); }
        public void inner() {}
    }
    public static void main(String[] args) {
        ClosingChannel channel;
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean("csv", Exporter.class, CsvExporter::new);
            context.registerBean(ReceiptReport.class);
            context.registerBean(ImportBuffer.class, ImportBuffer::new,
                definition -> definition.setScope(BeanDefinition.SCOPE_PROTOTYPE));
            context.registerBean(ClosingChannel.class); context.refresh();
            channel = context.getBean(ClosingChannel.class);
            System.out.println(context.getBean(ReceiptReport.class).render());
            ObjectProvider<ImportBuffer> buffers = context.getBeanProvider(ImportBuffer.class);
            System.out.println("different=" + (buffers.getObject() != buffers.getObject()));
            AtomicInteger messages = new AtomicInteger();
            context.addApplicationListener((ApplicationListener<PayloadApplicationEvent<String>>) event -> messages.incrementAndGet());
            context.publishEvent("receipt-created");
            System.out.println("events=" + messages.get());
        }
        System.out.println("closed=" + channel.closed);
        AtomicInteger advised = new AtomicInteger();
        ProxyFactory factory = new ProxyFactory(new CounterTarget());
        factory.addAdvice((MethodInterceptor) invocation -> { advised.incrementAndGet(); return invocation.proceed(); });
        Counter proxy = (Counter) factory.getProxy(); proxy.outer();
        System.out.println("advised=" + advised.get());
    }
}''')
write('QualifiedExportConfig','''import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Qualifier;
@Configuration(proxyBeanMethods = false)
public class QualifiedExportConfig {
    @Bean("csv") ContainerContracts.Exporter csv() { return () -> "csv"; }
    @Bean("archive") ContainerContracts.Exporter archive() { return () -> "archive"; }
    @Bean ContainerContracts.ReceiptReport report(@Qualifier("archive") ContainerContracts.Exporter exporter) {
        return new ContainerContracts.ReceiptReport(exporter);
    }
}''')
write('ImportConfiguration','''import java.time.Duration;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotNull;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
@Validated
@ConfigurationProperties("receipt.import")
public record ImportConfiguration(@Min(1) @Max(500) int batchSize, @NotNull Duration timeout) {}''')
write('FallbackExportConfig','''import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
@Configuration(proxyBeanMethods = false)
public class FallbackExportConfig {
    @Bean @ConditionalOnMissingBean(ContainerContracts.Exporter.class)
    ContainerContracts.Exporter fallbackExporter() { return () -> "fallback"; }
}''')
write('ReceiptStore','''import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;
@Service
public class ReceiptStore {
    public record Receipt(long id, int amountMinor) {}
    private final Map<Long,Receipt> receipts = new LinkedHashMap<>();
    private long nextId = 1;
    public synchronized Receipt create(int amountMinor) {
        if (amountMinor <= 0) throw new IllegalArgumentException("amount");
        Receipt receipt = new Receipt(nextId++, amountMinor); receipts.put(receipt.id(), receipt); return receipt;
    }
    public synchronized Optional<Receipt> find(long id) { return Optional.ofNullable(receipts.get(id)); }
    public synchronized List<Receipt> page(int offset, int limit) {
        if (offset < 0 || limit < 1 || limit > 100) throw new IllegalArgumentException("page");
        List<Receipt> snapshot = new ArrayList<>(receipts.values());
        int start = Math.min(offset, snapshot.size());
        return List.copyOf(snapshot.subList(start, start + Math.min(limit, snapshot.size() - start)));
    }
}''')
write('ReceiptController','''import java.util.List;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Positive;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/receipts")
public class ReceiptController {
    public record CreateReceipt(@Positive int amountMinor) {}
    private final ReceiptStore store;
    public ReceiptController(ReceiptStore store) { this.store = store; }
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public ReceiptStore.Receipt create(@Valid @RequestBody CreateReceipt command) { return store.create(command.amountMinor()); }
    @GetMapping("/{id}") public ReceiptStore.Receipt find(@PathVariable long id) {
        return store.find(id).orElseThrow(() -> new MissingReceipt(id));
    }
    @GetMapping public List<ReceiptStore.Receipt> page(@RequestParam(defaultValue="0") int offset,
        @RequestParam(defaultValue="20") int limit) { return store.page(offset, limit); }
    public static class MissingReceipt extends RuntimeException {
        MissingReceipt(long id) { super("Receipt " + id + " was not found"); }
    }
}''')
write('ReceiptErrors','''import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
@RestControllerAdvice
public class ReceiptErrors {
    @ExceptionHandler(ReceiptController.MissingReceipt.class)
    ProblemDetail missing(ReceiptController.MissingReceipt failure) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, failure.getMessage());
    }
    @ExceptionHandler({IllegalArgumentException.class, MethodArgumentNotValidException.class})
    ProblemDetail rejected(Exception failure) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Receipt input is invalid");
    }
}''')
write('ReceiptWebConfig','''import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
@Configuration(proxyBeanMethods=false)
public class ReceiptWebConfig implements WebMvcConfigurer {
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/receipts/**").allowedOrigins("https://reader.aitrove.in")
            .allowedMethods("GET", "POST").allowCredentials(true).maxAge(600);
    }
}''')
write('ReceiptSecurity','''import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.config.Customizer;
@Configuration(proxyBeanMethods=false)
public class ReceiptSecurity {
    @Bean PasswordEncoder passwordEncoder() { return PasswordEncoderFactories.createDelegatingPasswordEncoder(); }
    @Bean InMemoryUserDetailsManager readers(PasswordEncoder encoder) {
        // Local source-kit credential only; never deploy this user store.
        return new InMemoryUserDetailsManager(User.withUsername("local-reader")
            .password(encoder.encode("local-fixture-only")).roles("READER").build());
    }
    @Bean SecurityFilterChain receiptChain(HttpSecurity http) throws Exception {
        http.cors(Customizer.withDefaults()).authorizeHttpRequests(requests -> requests
            .requestMatchers("/actuator/health").permitAll().anyRequest().authenticated())
            .httpBasic(Customizer.withDefaults());
        return http.build(); // CSRF stays enabled for this session-capable learning application.
    }
}''')
write('ReceiptApplication','''import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
@SpringBootApplication
@EnableConfigurationProperties(ImportConfiguration.class)
public class ReceiptApplication {
    public static void main(String[] args) { SpringApplication.run(ReceiptApplication.class, args); }
}''')
write('JdbcReceiptLedger','''import java.util.UUID;
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
}''')
write('AsyncReceiptWork','''import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.core.task.TaskRejectedException;
public class AsyncReceiptWork {
    public static void main(String[] args) throws Exception {
        ThreadPoolTaskExecutor workers = new ThreadPoolTaskExecutor();
        workers.setCorePoolSize(1); workers.setMaxPoolSize(1); workers.setQueueCapacity(1); workers.initialize();
        CountDownLatch release = new CountDownLatch(1);
        try {
            workers.execute(() -> { try { release.await(); } catch (InterruptedException stop) { Thread.currentThread().interrupt(); } });
            workers.execute(() -> {});
            try { workers.execute(() -> {}); }
            catch (TaskRejectedException rejected) { System.out.println("capacity rejected"); }
        } finally { release.countDown(); workers.shutdown(); }
        if (!workers.getThreadPoolExecutor().awaitTermination(5, TimeUnit.SECONDS)) throw new AssertionError("termination");
    }
}''')
write('ReceiptCacheBoundary','''import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class ReceiptCacheBoundary {
    public static class Lookup {
        final AtomicInteger calls = new AtomicInteger();
        @Cacheable(cacheNames="receipts", key="#p0 + ':' + #p1")
        public String read(String tenant, long receiptId) { calls.incrementAndGet(); return tenant + ":" + receiptId; }
    }
    @Configuration(proxyBeanMethods=false) @EnableCaching
    public static class Config {
        @Bean ConcurrentMapCacheManager caches() { return new ConcurrentMapCacheManager("receipts"); }
        @Bean Lookup lookup() { return new Lookup(); }
    }
    public static void main(String[] args) {
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(Config.class)) {
            Lookup lookup = context.getBean(Lookup.class);
            System.out.println(lookup.read("tenant-a", 7));
            System.out.println(lookup.read("tenant-a", 7));
            System.out.println(lookup.read("tenant-b", 7));
        }
    }
}''')
resources=kit/'src/main/resources';resources.mkdir(parents=True,exist_ok=True)
(resources/'application.properties').write_text('''receipt.import.batch-size=32
receipt.import.timeout=5s
spring.datasource.url=jdbc:h2:mem:receipt_application
spring.datasource.username=sa
spring.datasource.password=
management.endpoints.web.exposure.include=health,info
management.endpoint.health.show-details=never
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=10s
''')
write('CoreBoundaryTest','''import java.time.Duration;
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
}''',True)
write('ReceiptBoundaryTest','''import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
public class ReceiptBoundaryTest {
    MockMvc mvc() {
        var validator = new LocalValidatorFactoryBean(); validator.afterPropertiesSet();
        return MockMvcBuilders.standaloneSetup(new ReceiptController(new ReceiptStore()))
            .setControllerAdvice(new ReceiptErrors()).setValidator(validator).build();
    }
    @Test void createsValidReceipt() throws Exception { mvc().perform(post("/api/receipts").contentType("application/json").content("{\\"amountMinor\\":125}"))
        .andExpect(status().isCreated()).andExpect(jsonPath("$.amountMinor").value(125)); }
    @Test void rejectsZeroAmount() throws Exception { mvc().perform(post("/api/receipts").contentType("application/json").content("{\\"amountMinor\\":0}"))
        .andExpect(status().isBadRequest()).andExpect(jsonPath("$.detail").value("Receipt input is invalid")); }
    @Test void missingReceiptUsesProblemDetail() throws Exception { mvc().perform(get("/api/receipts/999"))
        .andExpect(status().isNotFound()).andExpect(content().contentTypeCompatibleWith("application/problem+json")); }
    @Test void rejectsPageSizeBeyondLimit() throws Exception { mvc().perform(get("/api/receipts").param("limit", "101")).andExpect(status().isBadRequest()); }
    @Test void emptyPageOutsideRangeIsEmpty() { var store = new ReceiptStore(); store.create(10); assertTrue(store.page(40, 20).isEmpty()); }
    @Test void returnedPageCannotMutateStore() { var store = new ReceiptStore(); store.create(10); assertThrows(UnsupportedOperationException.class, () -> store.page(0,20).clear()); }
    @Test void databaseFailureRollsBackWholeBatch() { var ledger = new JdbcReceiptLedger(); assertThrows(DataIntegrityViolationException.class, ledger::batchThatFails); assertEquals(0, ledger.count()); }
    @Test void rollbackOnlyDoesNotCommit() { var ledger = new JdbcReceiptLedger(); ledger.rollbackOnly(); assertEquals(0, ledger.count()); }
    @Test void boundInsertCommitsAndDuplicateIsRejected() { var ledger = new JdbcReceiptLedger(); ledger.add(9, 40); assertThrows(DataIntegrityViolationException.class, () -> ledger.add(9,50)); assertEquals(1, ledger.count()); }
}''',True)
write('HttpSecurityBoundaryTest','''import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
public class HttpSecurityBoundaryTest {
    static ConfigurableApplicationContext context;
    static String origin;
    static HttpClient client;
    static final String BASIC = "Basic " + Base64.getEncoder().encodeToString("local-reader:local-fixture-only".getBytes(StandardCharsets.UTF_8));
    @BeforeAll static void start() {
        context = SpringApplication.run(ReceiptApplication.class, "--server.port=0", "--spring.main.banner-mode=off");
        origin = "http://127.0.0.1:" + context.getEnvironment().getRequiredProperty("local.server.port"); client = HttpClient.newHttpClient();
    }
    @AfterAll static void close() { if (context != null) context.close(); }
    static HttpResponse<String> request(String path) throws Exception {
        return client.send(HttpRequest.newBuilder(URI.create(origin + path)).GET().build(), HttpResponse.BodyHandlers.ofString());
    }
    @Test void publicHealthIsAvailableWithoutCredentials() throws Exception {
        var response = request("/actuator/health"); assertEquals(200,response.statusCode()); assertTrue(response.body().contains("UP")); assertFalse(response.body().contains("components"));
    }
    @Test void apiRejectsAnonymousRequest() throws Exception { assertEquals(401, request("/api/receipts").statusCode()); }
    @Test void authenticatedGetWorks() throws Exception {
        var response = client.send(HttpRequest.newBuilder(URI.create(origin+"/api/receipts")).header("Authorization", BASIC).GET().build(), HttpResponse.BodyHandlers.ofString()); assertEquals(200,response.statusCode());
    }
    @Test void basicHeaderDoesNotBypassCsrf() throws Exception {
        var response = client.send(HttpRequest.newBuilder(URI.create(origin+"/api/receipts")).header("Authorization", BASIC).header("Content-Type","application/json")
            .POST(HttpRequest.BodyPublishers.ofString("{\\"amountMinor\\":125}")).build(), HttpResponse.BodyHandlers.ofString()); assertEquals(401,response.statusCode());
    }
    @Test void configuredOriginPassesCorsPreflight() throws Exception {
        var response = client.send(HttpRequest.newBuilder(URI.create(origin+"/api/receipts")).header("Origin", "https://reader.aitrove.in")
            .header("Access-Control-Request-Method", "POST").method("OPTIONS", HttpRequest.BodyPublishers.noBody()).build(), HttpResponse.BodyHandlers.ofString());
        assertEquals(200,response.statusCode()); assertEquals("https://reader.aitrove.in",response.headers().firstValue("access-control-allow-origin").orElseThrow());
    }
    @Test void unlistedOriginIsRejected() throws Exception {
        var response = client.send(HttpRequest.newBuilder(URI.create(origin+"/api/receipts")).header("Origin", "https://unlisted.invalid")
            .header("Access-Control-Request-Method", "POST").method("OPTIONS", HttpRequest.BodyPublishers.noBody()).build(), HttpResponse.BodyHandlers.ofString()); assertEquals(403,response.statusCode());
    }
    @Test void establishedUserWithoutCsrfIsForbidden() throws Exception {
        var mvc = org.springframework.test.web.servlet.setup.MockMvcBuilders.webAppContextSetup((org.springframework.web.context.WebApplicationContext) context)
            .apply(org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity()).build();
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/receipts")
            .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user("local-reader"))
            .contentType("application/json").content("{\\"amountMinor\\":125}"))
            .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.status().isForbidden());
    }
    @Test void establishedUserWithCsrfCreatesReceipt() throws Exception {
        var mvc = org.springframework.test.web.servlet.setup.MockMvcBuilders.webAppContextSetup((org.springframework.web.context.WebApplicationContext) context)
            .apply(org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity()).build();
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/receipts")
            .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user("local-reader"))
            .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf())
            .contentType("application/json").content("{\\"amountMinor\\":125}"))
            .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.status().isCreated());
    }
    @Test void passwordHashesUseSaltAndMatchOriginal() {
        var encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder(); var first = encoder.encode("fixture-password"); var second = encoder.encode("fixture-password");
        assertNotEquals(first, second); assertTrue(encoder.matches("fixture-password",first)); assertFalse(encoder.matches("incorrect",first));
    }
}''',True)
