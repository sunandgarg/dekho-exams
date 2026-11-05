package in.aitrove.contracts;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import static org.junit.jupiter.api.Assertions.*;

/** A loopback transport fixture, separate from ReceiptApplication and any real upstream. */
class RestClientBoundaryTest {
    private HttpServer upstream;
    private ExecutorService handlers;

    @BeforeEach void startServer() throws IOException {
        upstream = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        handlers = Executors.newCachedThreadPool();
        upstream.setExecutor(handlers);
        upstream.start();
    }

    @AfterEach void stopServer() {
        upstream.stop(0);
        handlers.shutdownNow();
    }

    private RestClient client(Duration readTimeout) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofMillis(300));
        factory.setReadTimeout(readTimeout);
        return RestClient.builder()
            .requestFactory(factory)
            .baseUrl("http://127.0.0.1:" + upstream.getAddress().getPort())
            .build();
    }

    private static void reply(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.sendResponseHeaders(status, bytes.length);
        try (var response = exchange.getResponseBody()) {
            response.write(bytes);
        }
    }

    @Test void explicitFactoryReadsTheUpstreamResponse() {
        upstream.createContext("/risk/receipt-2048", exchange -> reply(exchange, 200, "approved"));
        assertEquals("approved", client(Duration.ofSeconds(1)).get()
            .uri("/risk/receipt-2048").retrieve().body(String.class));
    }

    @Test void errorStatusDoesNotTriggerAnImplicitRetry() {
        var requests = new AtomicInteger();
        upstream.createContext("/risk/receipt-2048", exchange -> {
            requests.incrementAndGet();
            reply(exchange, 503, "temporarily unavailable");
        });
        assertThrows(HttpServerErrorException.class, () -> client(Duration.ofSeconds(1)).get()
            .uri("/risk/receipt-2048").retrieve().body(String.class));
        assertEquals(1, requests.get());
    }

    @Test void readTimeoutStopsWaitingForAStalledResponse() throws InterruptedException {
        var release = new CountDownLatch(1);
        var requestReceived = new CountDownLatch(1);
        upstream.createContext("/risk/receipt-2048", exchange -> {
            requestReceived.countDown();
            try {
                release.await(2, TimeUnit.SECONDS);
                reply(exchange, 200, "late approval");
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            } catch (IOException ignored) {
                // The client may have closed its socket after the read deadline.
            }
        });
        try {
            assertThrows(ResourceAccessException.class, () -> client(Duration.ofMillis(80)).get()
                .uri("/risk/receipt-2048").retrieve().body(String.class));
            assertTrue(requestReceived.await(1, TimeUnit.SECONDS));
        } finally {
            release.countDown();
        }
    }

    @Test void aTimedOutWriteMayHaveCommittedBeforeTheCallerRetries() throws InterruptedException {
        var committedKeys = ConcurrentHashMap.<String>newKeySet();
        var writes = new AtomicInteger();
        var requests = new AtomicInteger();
        var first = new AtomicBoolean(true);
        var releaseFirst = new CountDownLatch(1);
        var firstWriteCommitted = new CountDownLatch(1);
        upstream.createContext("/remote-reservations", exchange -> {
            requests.incrementAndGet();
            String key = exchange.getRequestHeaders().getFirst("Idempotency-Key");
            if (key != null && committedKeys.add(key)) {
                writes.incrementAndGet();
                firstWriteCommitted.countDown();
            }
            try {
                if (first.compareAndSet(true, false)) releaseFirst.await(2, TimeUnit.SECONDS);
                reply(exchange, 200, "reservation-2048");
            } catch (InterruptedException ignored) {
                Thread.currentThread().interrupt();
            } catch (IOException ignored) {
                // The first response can be lost after the server changed state.
            }
        });

        RestClient caller = client(Duration.ofMillis(80));
        try {
            assertThrows(ResourceAccessException.class, () -> caller.post()
                .uri("/remote-reservations")
                .header("Idempotency-Key", "tenant-east-receipt-2048")
                .retrieve().body(String.class));
            assertTrue(firstWriteCommitted.await(1, TimeUnit.SECONDS));
            assertEquals(1, writes.get());
        } finally {
            releaseFirst.countDown();
        }
        assertEquals("reservation-2048", caller.post()
            .uri("/remote-reservations")
            .header("Idempotency-Key", "tenant-east-receipt-2048")
            .retrieve().body(String.class));
        assertEquals(2, requests.get());
        assertEquals(1, writes.get());
        assertEquals(Set.of("tenant-east-receipt-2048"), committedKeys);
    }
}
