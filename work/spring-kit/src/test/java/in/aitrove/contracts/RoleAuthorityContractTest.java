package in.aitrove.contracts;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;

import static org.junit.jupiter.api.Assertions.*;

public class RoleAuthorityContractTest {
    static class ReceiptEditor {
        @PreAuthorize("hasRole('EDITOR')")
        public String approve() { return "approved"; }
    }
    @Configuration @EnableMethodSecurity
    static class Config {
        @Bean ReceiptEditor editor() { return new ReceiptEditor(); }
    }

    @Test void roleRuleExpectsTheConfiguredRolePrefix() {
        try (var context = new AnnotationConfigApplicationContext(Config.class)) {
            var editor = context.getBean(ReceiptEditor.class);
            SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("reviewer", "unused",
                    List.of(new SimpleGrantedAuthority("EDITOR"))));
            assertThrows(AccessDeniedException.class, editor::approve);
            SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("reviewer", "unused",
                    List.of(new SimpleGrantedAuthority("ROLE_EDITOR"))));
            assertEquals("approved", editor.approve());
        } finally { SecurityContextHolder.clearContext(); }
    }
}
