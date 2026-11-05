package in.aitrove.contracts;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.EnableAsync;

import static org.junit.jupiter.api.Assertions.*;

public class AsyncFailureContractTest {
    static class ReceiptDispatcher {
        @Async
        public CompletableFuture<String> deliver(String receiptId) {
            return CompletableFuture.failedFuture(new IllegalStateException("broker unavailable: " + receiptId));
        }
    }

    @Configuration @EnableAsync
    static class Config {
        @Bean ReceiptDispatcher dispatcher() { return new ReceiptDispatcher(); }
    }

    @Test void failureIsObservedThroughTheReturnedFuture() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            var dispatcher = context.getBean(ReceiptDispatcher.class);
            CompletionException failure = assertThrows(CompletionException.class,
                () -> dispatcher.deliver("R-41").join());
            assertInstanceOf(IllegalStateException.class, failure.getCause());
        }
    }
}
