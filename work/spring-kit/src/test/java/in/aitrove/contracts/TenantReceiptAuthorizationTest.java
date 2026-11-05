package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

public class TenantReceiptAuthorizationTest {
    static class TenantReceiptReader {
        @PreAuthorize("#p0 == authentication.name")
        public String read(String tenant, int receiptId) {
            return tenant + ":" + receiptId;
        }
    }
    @Configuration @EnableMethodSecurity
    static class Config {
        @Bean TenantReceiptReader reader() { return new TenantReceiptReader(); }
    }
    @Test void rejectsACrossTenantReadThroughTheManagedService() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            var reader = context.getBean(TenantReceiptReader.class);
            SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("tenant-east", "unused", List.of()));
            assertEquals("tenant-east:7", reader.read("tenant-east", 7));
            assertThrows(AccessDeniedException.class, () -> reader.read("tenant-west", 7));
        } finally { SecurityContextHolder.clearContext(); }
    }
}
