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
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.mock.web.MockServletContext;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.core.DelegatingOAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2TokenValidatorResult;
import org.springframework.security.oauth2.jose.jws.SignatureAlgorithm;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class TenantReceiptCommandFlowTest {
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

    @Configuration @EnableWebMvc @EnableWebSecurity @EnableMethodSecurity
    static class Config {
        @Bean JwtDecoder decoder() {
            var decoder = NimbusJwtDecoder.withPublicKey((RSAPublicKey) TRUSTED.getPublic()).build();
            decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
                JwtValidators.createDefaultWithIssuer(ReceiptTokenDecoder.ISSUER),
                jwt -> jwt.getAudience().contains("receipt-api")
                    ? OAuth2TokenValidatorResult.success()
                    : OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_audience")),
                jwt -> {
                    String tenant = jwt.getClaimAsString("tenant_id");
                    return tenant != null && tenant.matches("tenant-[a-z]+")
                        ? OAuth2TokenValidatorResult.success()
                        : OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_tenant"));
                }));
            return decoder;
        }

        @Bean SecurityFilterChain chain(HttpSecurity http, JwtDecoder decoder) throws Exception {
            var converter = new JwtAuthenticationConverter();
            converter.setPrincipalClaimName("tenant_id");
            return http.csrf(csrf -> csrf.disable()) // Local stateless bearer fixture; no browser session cookie.
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(requests -> requests
                    .requestMatchers("/contract/commands/**").hasAuthority("SCOPE_receipt.write")
                    .anyRequest().denyAll())
                .oauth2ResourceServer(resource -> resource.jwt(jwt ->
                    jwt.decoder(decoder).jwtAuthenticationConverter(converter))).build();
        }

        @Bean JdbcTemplate commandDatabase() {
            var source = new DriverManagerDataSource(
                "jdbc:h2:mem:tenant_command_" + UUID.randomUUID() + ";DB_CLOSE_DELAY=-1", "sa", "");
            var jdbc = new JdbcTemplate(source);
            jdbc.execute("create table receipt_state (tenant_id varchar(40), receipt_id varchar(40), state varchar(40), version int, primary key (tenant_id, receipt_id))");
            jdbc.execute("create table receipt_outbox (event_id varchar(160) primary key, tenant_id varchar(40), receipt_id varchar(40), state varchar(40))");
            jdbc.execute("create table command_dedupe (tenant_id varchar(40), request_key varchar(60), fingerprint varchar(140), response_version int, primary key (tenant_id, request_key))");
            jdbc.update("insert into receipt_state values (?, ?, ?, ?)", "tenant-east", "R-41", "new", 1);
            jdbc.update("insert into receipt_state values (?, ?, ?, ?)", "tenant-west", "R-41", "new", 1);
            return jdbc;
        }

        @Bean TransactionTemplate commandTransaction(JdbcTemplate commandDatabase) {
            return new TransactionTemplate(new DataSourceTransactionManager(commandDatabase.getDataSource()));
        }
        @Bean CommandService commandService(JdbcTemplate commandDatabase, TransactionTemplate commandTransaction) {
            return new CommandService(commandDatabase, commandTransaction);
        }
        @Bean CommandController commandController(CommandService commandService) {
            return new CommandController(commandService);
        }
    }

    record ChangeState(String state, int expectedVersion) {}
    record StoredCommand(String fingerprint, int responseVersion) {}

    static class CommandService {
        private final JdbcTemplate jdbc;
        private final TransactionTemplate transaction;

        CommandService(JdbcTemplate jdbc, TransactionTemplate transaction) {
            this.jdbc = jdbc;
            this.transaction = transaction;
        }

        @PreAuthorize("#p0 == authentication.name")
        public int change(String tenant, String receiptId, String requestKey, ChangeState command, boolean failAfterOutbox) {
            if (requestKey == null || !requestKey.matches("[A-Za-z0-9-]{1,60}"))
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid idempotency key");
            if (receiptId == null || !receiptId.matches("[A-Za-z0-9-]{1,40}"))
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid receipt ID");
            if (command == null || command.state() == null || !command.state().matches("accepted|held") || command.expectedVersion() < 1)
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid state change");

            return transaction.execute(status -> {
                String fingerprint = receiptId + ":" + command.state() + ":" + command.expectedVersion();
                List<StoredCommand> old = jdbc.query(
                    "select fingerprint, response_version from command_dedupe where tenant_id = ? and request_key = ?",
                    (row, number) -> new StoredCommand(row.getString(1), row.getInt(2)), tenant, requestKey);
                if (!old.isEmpty()) {
                    if (!old.getFirst().fingerprint().equals(fingerprint))
                        throw new ResponseStatusException(HttpStatus.CONFLICT, "Idempotency key reused for another command");
                    return old.getFirst().responseVersion();
                }

                int changed = jdbc.update("update receipt_state set state = ?, version = version + 1 where tenant_id = ? and receipt_id = ? and version = ?",
                    command.state(), tenant, receiptId, command.expectedVersion());
                if (changed != 1)
                    throw new ResponseStatusException(HttpStatus.CONFLICT, "Receipt version changed or row is absent");
                int nextVersion = command.expectedVersion() + 1;
                jdbc.update("insert into receipt_outbox values (?, ?, ?, ?)",
                    tenant + ":" + receiptId + ":" + requestKey, tenant, receiptId, command.state());
                if (failAfterOutbox) throw new IllegalStateException("Injected before transaction commit");
                jdbc.update("insert into command_dedupe values (?, ?, ?, ?)", tenant, requestKey, fingerprint, nextVersion);
                return nextVersion;
            });
        }
    }

    @RestController
    static class CommandController {
        private final CommandService service;
        CommandController(CommandService service) { this.service = service; }

        @PostMapping(path = "/contract/commands/{tenant}/{receiptId}", consumes = MediaType.APPLICATION_JSON_VALUE)
        int change(@PathVariable String tenant, @PathVariable String receiptId,
                   @RequestHeader("Idempotency-Key") String key, @RequestBody ChangeState command) {
            return service.change(tenant, receiptId, key, command, false);
        }
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
        var claims = JwtClaimsSet.builder().issuer(ReceiptTokenDecoder.ISSUER).subject("operator-41")
            .audience(List.of("receipt-api")).issuedAt(Instant.now().minusSeconds(30))
            .expiresAt(Instant.now().plusSeconds(300)).claim("scope", scope);
        if (tenant != null) claims.claim("tenant_id", tenant);
        return encoder.encode(JwtEncoderParameters.from(
            JwsHeader.with(SignatureAlgorithm.RS256).build(), claims.build())).getTokenValue();
    }

    private org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder request(
        String tenant, String key, String body, String scope) {
        return post("/contract/commands/" + tenant + "/R-41")
            .header("Authorization", "Bearer " + token("tenant-east", scope))
            .header("Idempotency-Key", key).header("X-Tenant", "tenant-west")
            .contentType(MediaType.APPLICATION_JSON).content(body);
    }

    private int count(String table) {
        return context.getBean(JdbcTemplate.class).queryForObject("select count(*) from " + table, Integer.class);
    }

    private String state(String tenant) {
        return context.getBean(JdbcTemplate.class).queryForObject(
            "select state from receipt_state where tenant_id = ? and receipt_id = ?",
            String.class, tenant, "R-41");
    }

    @Test void authorizedWriteCommitsReceiptOutboxAndReplayRecord() throws Exception {
        client.perform(request("tenant-east", "accept-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isOk()).andExpect(content().string("2"));
        assertEquals("accepted", state("tenant-east"));
        assertEquals("new", state("tenant-west"));
        assertEquals(1, count("receipt_outbox"));
        assertEquals(1, count("command_dedupe"));
    }

    @Test void replayReturnsStoredVersionWithoutSecondMutation() throws Exception {
        var accepted = request("tenant-east", "accept-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write");
        client.perform(accepted).andExpect(status().isOk());
        client.perform(request("tenant-east", "accept-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isOk()).andExpect(content().string("2"));
        assertEquals(1, count("receipt_outbox"));
        assertEquals(1, count("command_dedupe"));
        assertEquals(2, context.getBean(JdbcTemplate.class).queryForObject(
            "select version from receipt_state where tenant_id = ? and receipt_id = ?", Integer.class, "tenant-east", "R-41"));
    }

    @Test void reusedKeyWithDifferentCommandIsConflict() throws Exception {
        client.perform(request("tenant-east", "accept-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isOk());
        client.perform(request("tenant-east", "accept-41", "{\"state\":\"held\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isConflict());
        assertEquals("accepted", state("tenant-east"));
        assertEquals(1, count("receipt_outbox"));
    }

    @Test void sameKeyCannotTargetAnotherReceipt() throws Exception {
        client.perform(request("tenant-east", "accept-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isOk());
        client.perform(post("/contract/commands/tenant-east/R-42")
                .header("Authorization", "Bearer " + token("tenant-east", "receipt.write"))
                .header("Idempotency-Key", "accept-41")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"state\":\"accepted\",\"expectedVersion\":1}"))
            .andExpect(status().isConflict());
        assertEquals(1, count("receipt_outbox"));
    }

    @Test void staleVersionLeavesNoOutboxRow() throws Exception {
        client.perform(request("tenant-east", "stale-41", "{\"state\":\"accepted\",\"expectedVersion\":3}", "receipt.write"))
            .andExpect(status().isConflict());
        assertEquals("new", state("tenant-east"));
        assertEquals(0, count("receipt_outbox"));
        assertEquals(0, count("command_dedupe"));
    }

    @Test void crossTenantAndWrongScopeAreDeniedBeforeMutation() throws Exception {
        client.perform(request("tenant-west", "west-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.write"))
            .andExpect(status().isForbidden());
        client.perform(request("tenant-east", "read-41", "{\"state\":\"accepted\",\"expectedVersion\":1}", "receipt.read"))
            .andExpect(status().isForbidden());
        assertEquals("new", state("tenant-east"));
        assertEquals("new", state("tenant-west"));
        assertEquals(0, count("receipt_outbox"));
    }

    @Test void missingTenantClaimIsUnauthorizedBeforeMutation() throws Exception {
        client.perform(post("/contract/commands/tenant-east/R-41")
                .header("Authorization", "Bearer " + token(null, "receipt.write"))
                .header("Idempotency-Key", "no-tenant-41")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"state\":\"accepted\",\"expectedVersion\":1}"))
            .andExpect(status().isUnauthorized());
        assertEquals(0, count("receipt_outbox"));
    }

    @Test void failureAfterOutboxInsertRollsBackAllThreeTables() {
        SecurityContextHolder.getContext().setAuthentication(
            new UsernamePasswordAuthenticationToken("tenant-east", "unused", List.of()));
        try {
            assertThrows(IllegalStateException.class, () -> context.getBean(CommandService.class)
                .change("tenant-east", "R-41", "rollback-41", new ChangeState("accepted", 1), true));
        } finally {
            SecurityContextHolder.clearContext();
        }
        assertEquals("new", state("tenant-east"));
        assertEquals(0, count("receipt_outbox"));
        assertEquals(0, count("command_dedupe"));
    }
}
