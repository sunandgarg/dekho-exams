package in.aitrove.learning;
import java.net.URI;
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
            .POST(HttpRequest.BodyPublishers.ofString("{\"amountMinor\":125}")).build(), HttpResponse.BodyHandlers.ofString()); assertEquals(401,response.statusCode());
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
            .contentType("application/json").content("{\"amountMinor\":125}"))
            .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.status().isForbidden());
    }
    @Test void establishedUserWithCsrfCreatesReceipt() throws Exception {
        var mvc = org.springframework.test.web.servlet.setup.MockMvcBuilders.webAppContextSetup((org.springframework.web.context.WebApplicationContext) context)
            .apply(org.springframework.security.test.web.servlet.setup.SecurityMockMvcConfigurers.springSecurity()).build();
        mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post("/api/receipts")
            .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.user("local-reader"))
            .with(org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf())
            .contentType("application/json").content("{\"amountMinor\":125}"))
            .andExpect(org.springframework.test.web.servlet.result.MockMvcResultMatchers.status().isCreated());
    }
    @Test void passwordHashesUseSaltAndMatchOriginal() {
        var encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder(); var first = encoder.encode("fixture-password"); var second = encoder.encode("fixture-password");
        assertNotEquals(first, second); assertTrue(encoder.matches("fixture-password",first)); assertFalse(encoder.matches("incorrect",first));
    }
}
