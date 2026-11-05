package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockServletContext;
import org.springframework.web.context.annotation.RequestScope;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;
import org.springframework.beans.factory.support.ScopeNotActiveException;

import static org.junit.jupiter.api.Assertions.*;

public class RequestScopeBoundaryTest {
    static class RequestTenant {
        private String name;
        void setName(String value) { name = value; }
        String name() { return name; }
    }
    record ReceiptLabel(RequestTenant tenant) {
        String text() { return tenant.name(); }
    }
    @Configuration
    static class Config {
        @Bean @RequestScope(proxyMode = ScopedProxyMode.TARGET_CLASS)
        RequestTenant requestTenant() { return new RequestTenant(); }
        @Bean ReceiptLabel receiptLabel(RequestTenant tenant) { return new ReceiptLabel(tenant); }
    }
    private String labelFor(ReceiptLabel label, String tenantName) {
        var attributes = new ServletRequestAttributes(new MockHttpServletRequest());
        RequestContextHolder.setRequestAttributes(attributes);
        try {
            label.tenant.setName(tenantName);
            return label.text();
        } finally {
            RequestContextHolder.resetRequestAttributes();
            attributes.requestCompleted();
        }
    }
    @Test void resolvesASeparateTargetPerBoundRequest() {
        try (var context = new AnnotationConfigWebApplicationContext()) {
            context.setServletContext(new MockServletContext());
            context.register(Config.class);
            context.refresh();
            var label = context.getBean(ReceiptLabel.class);
            assertEquals("tenant-east", labelFor(label, "tenant-east"));
            assertEquals("tenant-west", labelFor(label, "tenant-west"));
            assertSame(label, context.getBean(ReceiptLabel.class));
            assertThrows(ScopeNotActiveException.class, label::text);
        } finally {
            RequestContextHolder.resetRequestAttributes();
        }
    }
}
