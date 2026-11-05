package in.aitrove.contracts;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.junit.jupiter.api.Assertions.*;

public class TenantReceiptWriteTest {
    static class ReceiptWriter {
        private final Map<String, String> states = new HashMap<>();

        @PreAuthorize("#p0 == authentication.name")
        public void change(String tenant, int receiptId, String next) {
            states.put(tenant + ":" + receiptId, next);
        }

        public String state(String tenant, int receiptId) {
            return states.get(tenant + ":" + receiptId);
        }
    }

    @Configuration @EnableMethodSecurity
    static class Config {
        @Bean ReceiptWriter writer() { return new ReceiptWriter(); }
    }

    @Test void managedServiceRejectsACrossTenantMutationBeforeTheMethodRuns() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            var writer = context.getBean(ReceiptWriter.class);
            SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("tenant-east", "unused", List.of()));
            writer.change("tenant-east", 7, "reviewed");
            assertThrows(AccessDeniedException.class,
                () -> writer.change("tenant-west", 7, "overwritten"));
            assertEquals("reviewed", writer.state("tenant-east", 7));
            assertNull(writer.state("tenant-west", 7));
        } finally {
            SecurityContextHolder.clearContext();
        }
    }
}
