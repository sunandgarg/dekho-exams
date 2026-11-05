import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1];kit=ROOT/'work/spring-kit'
p=kit/'pom.xml';s=p.read_text()
for group,artifact in [('org.springframework.data','spring-data-jpa'),('org.springframework','spring-webflux'),('org.springframework.security','spring-security-oauth2-resource-server'),('org.springframework.security','spring-security-oauth2-jose')]:
 if '<artifactId>'+artifact+'</artifactId>' not in s:s=s.replace('</dependencies>','<dependency><groupId>'+group+'</groupId><artifactId>'+artifact+'</artifactId></dependency></dependencies>')
p.write_text(s)
def write(name,source,test=False):
 d=kit/('src/test/java/in/aitrove/contracts' if test else 'src/main/java/in/aitrove/contracts');d.mkdir(parents=True,exist_ok=True);(d/(name+'.java')).write_text(source)
write('StockRepository','''package in.aitrove.contracts;
import java.util.*;
import org.springframework.data.jpa.repository.JpaRepository;
public interface StockRepository extends JpaRepository<JpaContracts.StockAccount,Long> {
    List<JpaContracts.StockAccount> findByAvailableGreaterThanOrderByIdAsc(int minimum);
    interface StockSummary {Long getId();int getAvailable();}
    List<StockSummary> findSummaryByAvailableGreaterThanOrderByIdAsc(int minimum);
    List<StockSummary> findTop2ByIdGreaterThanOrderByIdAsc(long afterId);
}
''')
write('RepositoryContracts','''package in.aitrove.contracts;
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
''')
write('ReceiptLabelAutoConfiguration','''package in.aitrove.contracts;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
@AutoConfiguration
public class ReceiptLabelAutoConfiguration {
    public record ReceiptLabel(String prefix) {public String render(long id){return prefix+":"+id;}}
    @Bean @ConditionalOnMissingBean
    public ReceiptLabel receiptLabel(){return new ReceiptLabel("Receipt");}
}
''')
meta=kit/'src/main/resources/META-INF/spring';meta.mkdir(parents=True,exist_ok=True);(meta/'org.springframework.boot.autoconfigure.AutoConfiguration.imports').write_text('in.aitrove.contracts.ReceiptLabelAutoConfiguration\n')
write('ReactiveReceiptController','''package in.aitrove.contracts;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.http.*;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Flux;
@RestController
public class ReactiveReceiptController {
    public final AtomicBoolean cancelled=new AtomicBoolean();
    @GetMapping(value="/contract/events",produces=MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> events(@RequestParam(defaultValue="3") int count) {
        if(count<1 || count>5)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"count must be 1..5");
        return Flux.range(1,count).delayElements(Duration.ofMillis(10))
            .map(index->ServerSentEvent.<String>builder("R"+index).id(Integer.toString(index)).event("receipt").build())
            .doOnCancel(()->cancelled.set(true));
    }
}
''')
write('ReceiptCacheEdits','''package in.aitrove.contracts;
import java.util.concurrent.*;
import org.springframework.cache.annotation.*;
public class ReceiptCacheEdits {
    public record Key(String tenant,long id) {}
    private final ConcurrentMap<Key,String> data=new ConcurrentHashMap<>();
    @Cacheable(cacheNames="contractReceipts",key="#key")
    public String read(Key key){return data.getOrDefault(key,"missing");}
    @CacheEvict(cacheNames="contractReceipts",key="#key")
    public void replace(Key key,String value){data.put(key,value);}
}
''')
write('RepositoryQueryTest','''package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
public class RepositoryQueryTest {
    @Test void derivedPredicateUsesMappedPropertyAndOrder() {
        try(var kit=new RepositoryContracts()) {
            kit.transaction.executeWithoutResult(status->kit.stocks.findById(2L).orElseThrow().available=30);
            assertEquals(List.of(1L,3L),kit.stocks.findByAvailableGreaterThanOrderByIdAsc(50).stream().map(account->account.id).toList());
            assertTrue(kit.stocks.findByAvailableGreaterThanOrderByIdAsc(100).isEmpty());
        }
    }
    @Test void projectionReadsValuesWithoutCreatingAFullEntity() {
        try(var kit=new RepositoryContracts()) {
            kit.data.statistics().clear();
            var summaries=kit.stocks.findSummaryByAvailableGreaterThanOrderByIdAsc(50);
            assertEquals(3,summaries.size());assertEquals(100,summaries.get(0).getAvailable());assertEquals(1L,summaries.get(0).getId());
            assertEquals(0,kit.data.statistics().getEntityLoadCount());
            assertEquals(1,kit.data.statistics().getPrepareStatementCount());
        }
    }
    @Test void cursorKeepsIdOrderAndMovesPastThePreviousLastId() {
        try(var kit=new RepositoryContracts()) {
            var first=kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(0);
            assertEquals(List.of(1L,2L),first.stream().map(StockRepository.StockSummary::getId).toList());
            var next=kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(2);
            assertEquals(List.of(3L),next.stream().map(StockRepository.StockSummary::getId).toList());
            assertTrue(kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(3).isEmpty());
        }
    }
}
''',True)
write('AutoConfigurationContractTest','''package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.boot.context.annotation.ImportCandidates;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.*;
public class AutoConfigurationContractTest {
    ApplicationContextRunner runner(){return new ApplicationContextRunner().withConfiguration(AutoConfigurations.of(ReceiptLabelAutoConfiguration.class));}
    @Test void defaultBeanRendersLabel(){runner().run(context->assertEquals("Receipt:7",context.getBean(ReceiptLabelAutoConfiguration.ReceiptLabel.class).render(7)));}
    @Configuration static class UserLabel {
        @Bean ReceiptLabelAutoConfiguration.ReceiptLabel label(){return new ReceiptLabelAutoConfiguration.ReceiptLabel("Invoice");}
    }
    @Test void userBeanMakesDefaultBackOff(){runner().withUserConfiguration(UserLabel.class).run(context->{
        assertEquals(1,context.getBeansOfType(ReceiptLabelAutoConfiguration.ReceiptLabel.class).size());
        assertEquals("Invoice:7",context.getBean(ReceiptLabelAutoConfiguration.ReceiptLabel.class).render(7));});}
    @Test void importsResourceRegistersTheConfiguration(){assertTrue(ImportCandidates.load(AutoConfiguration.class,getClass().getClassLoader()).getCandidates().contains(ReceiptLabelAutoConfiguration.class.getName()));}
}
''',True)
write('ReactiveHttpContractTest','''package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.http.MediaType;
import reactor.test.StepVerifier;
import java.time.Duration;
public class ReactiveHttpContractTest {
    WebTestClient client(ReactiveReceiptController controller){return WebTestClient.bindToController(controller).build();}
    @Test void emitsOrderedSseEventsAndCompletes(){
        var result=client(new ReactiveReceiptController()).get().uri("/contract/events?count=3").exchange()
            .expectStatus().isOk().expectHeader().contentTypeCompatibleWith(MediaType.TEXT_EVENT_STREAM)
            .returnResult(new ParameterizedTypeReference<ServerSentEvent<String>>(){});
        StepVerifier.create(result.getResponseBody()).expectNextMatches(event->event.id().equals("1")&&event.data().equals("R1"))
            .expectNextMatches(event->event.id().equals("2")&&event.data().equals("R2"))
            .expectNextMatches(event->event.id().equals("3")&&event.data().equals("R3"))
            .expectComplete().verify(Duration.ofSeconds(3));
    }
    @Test void rejectsCountBeforeSuccessfulStreamHeaders(){client(new ReactiveReceiptController()).get().uri("/contract/events?count=0").exchange().expectStatus().isBadRequest();}
    @Test void downstreamCancellationReachesTheControllerSequence(){
        var controller=new ReactiveReceiptController();
        var result=client(controller).get().uri("/contract/events?count=5").exchange().expectStatus().isOk()
            .returnResult(new ParameterizedTypeReference<ServerSentEvent<String>>(){});
        StepVerifier.create(result.getResponseBody()).expectNextCount(1).thenCancel().verify(Duration.ofSeconds(3));
        assertTrue(controller.cancelled.get());
    }
}
''',True)
write('CacheEvictionContractTest','''package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.context.annotation.*;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.concurrent.ConcurrentMapCacheManager;
import org.springframework.cache.CacheManager;
public class CacheEvictionContractTest {
    @Configuration @EnableCaching static class Config {
        @Bean CacheManager cacheManager(){return new ConcurrentMapCacheManager("contractReceipts");}
        @Bean ReceiptCacheEdits receipts(){return new ReceiptCacheEdits();}
    }
    @Test void proxiedEditEvictsOnlyTheMatchingTenantKey(){
        try(var context=new AnnotationConfigApplicationContext(Config.class)) {
            var service=context.getBean(ReceiptCacheEdits.class);
            var first=new ReceiptCacheEdits.Key("tenant-a",7);var second=new ReceiptCacheEdits.Key("tenant-b",7);
            service.replace(first,"a-original");service.replace(second,"b-original");
            assertEquals("a-original",service.read(first));assertEquals("b-original",service.read(second));
            service.replace(first,"a-new");assertEquals("a-new",service.read(first));assertEquals("b-original",service.read(second));
        }
    }
}
''',True)
print('Wrote repository, Boot import, reactive HTTP and cache fixtures')
write('ReceiptTokenDecoder','''package in.aitrove.contracts;
import java.security.interfaces.RSAPublicKey;
import java.util.List;
import org.springframework.security.oauth2.core.*;
import org.springframework.security.oauth2.jwt.*;
public final class ReceiptTokenDecoder {
    public static final String ISSUER="https://issuer.fixture.invalid";
    public static JwtDecoder create(RSAPublicKey publicKey) {
        NimbusJwtDecoder decoder=NimbusJwtDecoder.withPublicKey(publicKey).build();
        var audience=new JwtClaimValidator<List<String>>("aud",values->values!=null&&values.contains("receipt-api"));
        decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(JwtValidators.createDefaultWithIssuer(ISSUER),audience));
        return decoder;
    }
}
''')
write('JwtResourceServerContractTest','''package in.aitrove.contracts;
import java.security.*;
import java.security.interfaces.*;
import java.time.Instant;
import java.util.List;
import com.nimbusds.jose.jwk.*;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import org.junit.jupiter.api.*;
import org.springframework.context.annotation.*;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.mock.web.MockServletContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.bind.annotation.*;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.test.web.servlet.*;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
public class JwtResourceServerContractTest {
    static KeyPair keys(){try {var generator=KeyPairGenerator.getInstance("RSA");generator.initialize(2048);return generator.generateKeyPair();}catch(GeneralSecurityException failure){throw new IllegalStateException(failure);}}
    static final KeyPair TRUSTED=keys();
    @Configuration @EnableWebSecurity @EnableWebMvc static class Config {
        @Bean JwtDecoder decoder(){return ReceiptTokenDecoder.create((RSAPublicKey)TRUSTED.getPublic());}
        @Bean SecurityFilterChain chain(HttpSecurity http,JwtDecoder decoder) throws Exception {
            return http.sessionManagement(session->session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(requests->requests.requestMatchers("/contract/secure").hasAuthority("SCOPE_receipt.read").anyRequest().denyAll())
                .oauth2ResourceServer(resource->resource.jwt(jwt->jwt.decoder(decoder))).build();
        }
        @Bean SecureReceipt controller(){return new SecureReceipt();}
    }
    @RestController static class SecureReceipt {@GetMapping("/contract/secure") String read(){return "receipt:7";}}
    AnnotationConfigWebApplicationContext context;MockMvc client;
    @BeforeEach void start(){context=new AnnotationConfigWebApplicationContext();context.setServletContext(new MockServletContext());context.register(Config.class);context.refresh();client=MockMvcBuilders.webAppContextSetup(context).apply(springSecurity()).build();}
    @AfterEach void close(){context.close();}
    String token(KeyPair signer,String issuer,String audience,String scope,Instant expiry) {
        var key=new com.nimbusds.jose.jwk.RSAKey.Builder((RSAPublicKey)signer.getPublic()).privateKey((RSAPrivateKey)signer.getPrivate()).build();
        var encoder=new NimbusJwtEncoder(new ImmutableJWKSet<>(new JWKSet(key)));
        var claims=JwtClaimsSet.builder().issuer(issuer).subject("local-reader").audience(List.of(audience))
            .issuedAt(Instant.now().minusSeconds(1200)).expiresAt(expiry).claim("scope",scope).build();
        return encoder.encode(JwtEncoderParameters.from(JwsHeader.with(org.springframework.security.oauth2.jose.jws.SignatureAlgorithm.RS256).build(),claims)).getTokenValue();
    }
    ResultActions request(KeyPair signer,String issuer,String audience,String scope,Instant expiry) throws Exception {
        return client.perform(get("/contract/secure").header("Authorization","Bearer "+token(signer,issuer,audience,scope,expiry)));
    }
    @Test void trustedTokenWithScopeReachesTheEndpoint() throws Exception {request(TRUSTED,ReceiptTokenDecoder.ISSUER,"receipt-api","receipt.read",Instant.now().plusSeconds(300)).andExpect(status().isOk()).andExpect(content().string("receipt:7"));}
    @Test void missingTokenIsUnauthorized() throws Exception {client.perform(get("/contract/secure")).andExpect(status().isUnauthorized());}
    @Test void wrongScopeIsForbidden() throws Exception {request(TRUSTED,ReceiptTokenDecoder.ISSUER,"receipt-api","receipt.write",Instant.now().plusSeconds(300)).andExpect(status().isForbidden());}
    @Test void expiredTokenIsUnauthorized() throws Exception {request(TRUSTED,ReceiptTokenDecoder.ISSUER,"receipt-api","receipt.read",Instant.now().minusSeconds(600)).andExpect(status().isUnauthorized());}
    @Test void wrongIssuerIsUnauthorized() throws Exception {request(TRUSTED,"https://other.fixture.invalid","receipt-api","receipt.read",Instant.now().plusSeconds(300)).andExpect(status().isUnauthorized());}
    @Test void wrongAudienceIsUnauthorized() throws Exception {request(TRUSTED,ReceiptTokenDecoder.ISSUER,"another-api","receipt.read",Instant.now().plusSeconds(300)).andExpect(status().isUnauthorized());}
    @Test void untrustedSignatureIsUnauthorized() throws Exception {request(keys(),ReceiptTokenDecoder.ISSUER,"receipt-api","receipt.read",Instant.now().plusSeconds(300)).andExpect(status().isUnauthorized());}
}
''',True)
