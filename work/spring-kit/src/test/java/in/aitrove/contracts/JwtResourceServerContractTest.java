package in.aitrove.contracts;
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
