package in.aitrove.contracts;

import java.security.GeneralSecurityException;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.mock.web.MockServletContext;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class JwtTenantBoundaryTest {
    private static final KeyPair TRUSTED = keys();

    private static KeyPair keys() {
        try {
            var generator = KeyPairGenerator.getInstance("RSA");
            generator.initialize(2048);
            return generator.generateKeyPair();
        } catch (GeneralSecurityException failure) {
            throw new IllegalStateException(failure);
        }
    }

    @Configuration @EnableWebSecurity @EnableWebMvc @EnableMethodSecurity
    static class Config {
        @Bean JwtDecoder decoder() {
            var decoder = NimbusJwtDecoder.withPublicKey((RSAPublicKey) TRUSTED.getPublic()).build();
            decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
                JwtValidators.createDefaultWithIssuer(ReceiptTokenDecoder.ISSUER),
                jwt -> jwt.getAudience().contains("receipt-api")
                    ? org.springframework.security.oauth2.core.OAuth2TokenValidatorResult.success()
                    : org.springframework.security.oauth2.core.OAuth2TokenValidatorResult.failure(
                        new org.springframework.security.oauth2.core.OAuth2Error("invalid_audience")),
                jwt -> {
                    String tenant = jwt.getClaimAsString("tenant_id");
                    return tenant != null && tenant.matches("tenant-[a-z]+")
                        ? org.springframework.security.oauth2.core.OAuth2TokenValidatorResult.success()
                        : org.springframework.security.oauth2.core.OAuth2TokenValidatorResult.failure(
                            new org.springframework.security.oauth2.core.OAuth2Error("invalid_tenant"));
                }));
            return decoder;
        }

        @Bean SecurityFilterChain chain(HttpSecurity http, JwtDecoder decoder) throws Exception {
            var converter = new JwtAuthenticationConverter();
            converter.setPrincipalClaimName("tenant_id");
            return http.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(requests -> requests
                    .requestMatchers("/contract/tenant/**").hasAuthority("SCOPE_receipt.read")
                    .anyRequest().denyAll())
                .oauth2ResourceServer(resource -> resource.jwt(jwt ->
                    jwt.decoder(decoder).jwtAuthenticationConverter(converter))).build();
        }

        @Bean JdbcTemplate receiptDb() {
            var source = new DriverManagerDataSource(
                "jdbc:h2:mem:jwt_tenant_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
            var jdbc = new JdbcTemplate(source);
            jdbc.execute("create table tenant_receipt (receipt_id varchar(40), tenant_id varchar(40), state varchar(40), primary key (receipt_id, tenant_id))");
            jdbc.update("insert into tenant_receipt values (?, ?, ?)", "R-41", "tenant-east", "accepted");
            jdbc.update("insert into tenant_receipt values (?, ?, ?)", "R-41", "tenant-west", "held");
            return jdbc;
        }
        @Bean TenantReceiptReader reader(JdbcTemplate receiptDb) { return new TenantReceiptReader(receiptDb); }
        @Bean TenantController controller(TenantReceiptReader reader) { return new TenantController(reader); }
    }

    static class TenantReceiptReader {
        private final JdbcTemplate jdbc;
        TenantReceiptReader(JdbcTemplate jdbc) { this.jdbc = jdbc; }
        @PreAuthorize("#p0 == authentication.name")
        public String read(String tenant) {
            String state = jdbc.queryForObject(
                "select state from tenant_receipt where receipt_id = ? and tenant_id = ?",
                String.class, "R-41", tenant);
            return tenant + ":" + state;
        }
    }

    @RestController
    static class TenantController {
        private final TenantReceiptReader reader;
        TenantController(TenantReceiptReader reader) { this.reader = reader; }
        @GetMapping("/contract/tenant/{tenant}")
        String read(@PathVariable String tenant) { return reader.read(tenant); }
    }

    private AnnotationConfigWebApplicationContext context;
    private MockMvc client;

    @BeforeEach void start() {
        context = new AnnotationConfigWebApplicationContext();
        context.setServletContext(new MockServletContext());
        context.register(Config.class);
        context.refresh();
        client = MockMvcBuilders.webAppContextSetup(context).apply(springSecurity()).build();
    }

    @AfterEach void close() { context.close(); }

    private String token(String tenant, String scope) {
        var key = new RSAKey.Builder((RSAPublicKey) TRUSTED.getPublic())
            .privateKey((RSAPrivateKey) TRUSTED.getPrivate()).build();
        var encoder = new NimbusJwtEncoder(new ImmutableJWKSet<>(new JWKSet(key)));
        var claims = JwtClaimsSet.builder().issuer(ReceiptTokenDecoder.ISSUER).subject("reviewer-41")
            .audience(List.of("receipt-api")).issuedAt(Instant.now().minusSeconds(30))
            .expiresAt(Instant.now().plusSeconds(300)).claim("scope", scope);
        if (tenant != null) claims.claim("tenant_id", tenant);
        return encoder.encode(JwtEncoderParameters.from(
            JwsHeader.with(org.springframework.security.oauth2.jose.jws.SignatureAlgorithm.RS256).build(),
            claims.build())).getTokenValue();
    }

    @Test void trustedTenantClaimPassesTheMatchingServiceRule() throws Exception {
        client.perform(get("/contract/tenant/tenant-east")
                .header("Authorization", "Bearer " + token("tenant-east", "receipt.read"))
                .header("X-Tenant", "tenant-west"))
            .andExpect(status().isOk()).andExpect(content().string("tenant-east:accepted"));
    }

    @Test void anotherTenantIsForbiddenAfterAuthentication() throws Exception {
        client.perform(get("/contract/tenant/tenant-west")
                .header("Authorization", "Bearer " + token("tenant-east", "receipt.read"))
                .header("X-Tenant", "tenant-west"))
            .andExpect(status().isForbidden());
    }

    @Test void scopedQueryExcludesRowsForOtherTenantValues() {
        var jdbc = context.getBean(JdbcTemplate.class);
        String sql = "select state from tenant_receipt where receipt_id = ? and tenant_id = ?";
        org.junit.jupiter.api.Assertions.assertEquals(List.of("accepted"),
            jdbc.queryForList(sql, String.class, "R-41", "tenant-east"));
        org.junit.jupiter.api.Assertions.assertEquals(List.of("held"),
            jdbc.queryForList(sql, String.class, "R-41", "tenant-west"));
        org.junit.jupiter.api.Assertions.assertTrue(
            jdbc.queryForList(sql, String.class, "R-41", "tenant-north").isEmpty());
    }

    @Test void wrongScopeIsForbiddenBeforeTheService() throws Exception {
        client.perform(get("/contract/tenant/tenant-east")
                .header("Authorization", "Bearer " + token("tenant-east", "receipt.write")))
            .andExpect(status().isForbidden());
    }

    @Test void missingTenantClaimIsRejectedByTheDecoder() throws Exception {
        client.perform(get("/contract/tenant/tenant-east")
                .header("Authorization", "Bearer " + token(null, "receipt.read")))
            .andExpect(status().isUnauthorized());
    }
}
