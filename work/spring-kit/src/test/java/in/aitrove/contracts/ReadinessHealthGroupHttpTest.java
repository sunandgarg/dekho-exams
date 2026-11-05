package in.aitrove.contracts;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.atomic.AtomicBoolean;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.health.contributor.Health;
import org.springframework.boot.health.contributor.HealthIndicator;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import in.aitrove.learning.ReceiptApplication;

import static org.junit.jupiter.api.Assertions.*;

public class ReadinessHealthGroupHttpTest {
    private static final AtomicBoolean IMPORT_STORE_AVAILABLE = new AtomicBoolean(true);
    private static ConfigurableApplicationContext context;
    private static HttpClient client;
    private static String origin;

    @Configuration(proxyBeanMethods = false)
    static class TestHealth {
        @Bean("importStoreHealthIndicator") HealthIndicator importStore() {
            return () -> IMPORT_STORE_AVAILABLE.get() ? Health.up().build() : Health.down().build();
        }
    }

    @BeforeAll static void start() {
        context = new SpringApplication(ReceiptApplication.class, TestHealth.class).run(
            "--server.port=0", "--spring.main.banner-mode=off",
            "--management.endpoint.health.probes.enabled=true",
            "--management.endpoint.health.group.readiness.include=readinessState,importStore");
        origin = "http://127.0.0.1:" + context.getEnvironment().getRequiredProperty("local.server.port");
        client = HttpClient.newHttpClient();
    }

    @AfterAll static void close() { if (context != null) context.close(); }

    private static HttpResponse<String> get(String path) throws Exception {
        return client.send(HttpRequest.newBuilder(URI.create(origin + path)).GET().build(),
            HttpResponse.BodyHandlers.ofString());
    }

    @Test void failedImportStoreWithdrawsReadinessWithoutChangingLiveness() throws Exception {
        try {
            IMPORT_STORE_AVAILABLE.set(true);
            var ready = get("/actuator/health/readiness");
            assertEquals(200, ready.statusCode());
            assertTrue(ready.body().contains("UP"));

            IMPORT_STORE_AVAILABLE.set(false);
            var blocked = get("/actuator/health/readiness");
            assertEquals(503, blocked.statusCode());
            assertTrue(blocked.body().contains("DOWN"));
            assertEquals(200, get("/actuator/health/liveness").statusCode());
            assertEquals(401, get("/api/receipts").statusCode());
        } finally {
            IMPORT_STORE_AVAILABLE.set(true);
        }
    }
}
