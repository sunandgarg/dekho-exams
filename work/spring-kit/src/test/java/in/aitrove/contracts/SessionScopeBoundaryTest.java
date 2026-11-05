package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ScopedProxyMode;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.mock.web.MockServletContext;
import org.springframework.web.context.annotation.SessionScope;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;
import org.springframework.web.context.support.AnnotationConfigWebApplicationContext;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class SessionScopeBoundaryTest {
    static class ReviewCounter {
        private int viewed;
        int next() { return ++viewed; }
    }
    record ReviewService(ReviewCounter counter) {
        int view() { return counter.next(); }
    }
    @Configuration
    static class Config {
        @Bean @SessionScope(proxyMode = ScopedProxyMode.TARGET_CLASS)
        ReviewCounter reviewCounter() { return new ReviewCounter(); }
        @Bean ReviewService reviewService(ReviewCounter counter) { return new ReviewService(counter); }
    }
    private int viewInSession(ReviewService service, MockHttpSession session) {
        var request = new MockHttpServletRequest();
        request.setSession(session);
        var attributes = new ServletRequestAttributes(request);
        RequestContextHolder.setRequestAttributes(attributes);
        try { return service.view(); }
        finally {
            RequestContextHolder.resetRequestAttributes();
            attributes.requestCompleted();
        }
    }
    @Test void retainsStateAcrossRequestsButNotAcrossSessions() {
        try (var context = new AnnotationConfigWebApplicationContext()) {
            context.setServletContext(new MockServletContext());
            context.register(Config.class);
            context.refresh();
            var service = context.getBean(ReviewService.class);
            var first = new MockHttpSession();
            var second = new MockHttpSession();
            assertEquals(1, viewInSession(service, first));
            assertEquals(2, viewInSession(service, first));
            assertEquals(1, viewInSession(service, second));
        } finally { RequestContextHolder.resetRequestAttributes(); }
    }
}
