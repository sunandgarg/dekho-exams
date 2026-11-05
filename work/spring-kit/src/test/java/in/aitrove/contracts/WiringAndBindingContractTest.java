package in.aitrove.contracts;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.core.annotation.Order;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.InitBinder;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class WiringAndBindingContractTest {
    interface DispatchGateway { String route(); }
    record DispatchPlanner(DispatchGateway defaultGateway, DispatchGateway fallbackGateway) {}

    @Configuration(proxyBeanMethods = false)
    static class GatewayConfig {
        @Bean @Primary DispatchGateway regionalGateway() { return () -> "regional"; }
        @Bean DispatchGateway fallbackGateway() { return () -> "fallback"; }
        @Bean DispatchPlanner dispatchPlanner(
                DispatchGateway defaultGateway,
                @Qualifier("fallbackGateway") DispatchGateway fallbackGateway) {
            return new DispatchPlanner(defaultGateway, fallbackGateway);
        }
    }

    @Test void primarySetsDefaultWhileQualifierSelectsAnExplicitGateway() {
        try (var context = new AnnotationConfigApplicationContext(GatewayConfig.class)) {
            var planner = context.getBean(DispatchPlanner.class);
            assertEquals("regional", planner.defaultGateway().route());
            assertEquals("fallback", planner.fallbackGateway().route());
        }
    }

    record RetryPolicy(int maxAttempts) {}
    record DeliveryClient(RetryPolicy policy) {}

    @Configuration
    static class ProxiedPolicyConfig {
        @Bean RetryPolicy retryPolicy() { return new RetryPolicy(4); }
        @Bean DeliveryClient deliveryClient() { return new DeliveryClient(retryPolicy()); }
    }

    @Configuration(proxyBeanMethods = false)
    static class PlainPolicyConfig {
        @Bean RetryPolicy retryPolicy() { return new RetryPolicy(4); }
        @Bean DeliveryClient deliveryClient() { return new DeliveryClient(retryPolicy()); }
    }

    @Test void directBeanMethodCallChangesIdentityWithoutConfigurationProxy() {
        try (var proxied = new AnnotationConfigApplicationContext(ProxiedPolicyConfig.class);
             var plain = new AnnotationConfigApplicationContext(PlainPolicyConfig.class)) {
            assertSame(proxied.getBean(RetryPolicy.class), proxied.getBean(DeliveryClient.class).policy());
            assertNotSame(plain.getBean(RetryPolicy.class), plain.getBean(DeliveryClient.class).policy());
        }
    }

    interface ReceiptCheck { String name(); }
    record ReceiptPipeline(List<ReceiptCheck> checks) {}

    @Configuration(proxyBeanMethods = false)
    static class CheckConfig {
        @Bean @Order(20) ReceiptCheck stockCheck() { return () -> "stock"; }
        @Bean @Order(10) ReceiptCheck ownershipCheck() { return () -> "ownership"; }
        @Bean ReceiptPipeline receiptPipeline(List<ReceiptCheck> checks) { return new ReceiptPipeline(checks); }
    }

    @Test void orderedListInjectionDoesNotDependOnDeclarationOrder() {
        try (var context = new AnnotationConfigApplicationContext(CheckConfig.class)) {
            assertEquals(List.of("ownership", "stock"), context.getBean(ReceiptPipeline.class)
                    .checks().stream().map(ReceiptCheck::name).toList());
        }
    }

    public static class DispatchPreference {
        private String region;
        private boolean canApprove;
        public String getRegion() { return region; }
        public void setRegion(String region) { this.region = region; }
        public boolean isCanApprove() { return canApprove; }
        public void setCanApprove(boolean canApprove) { this.canApprove = canApprove; }
    }

    @RestController
    static class PreferenceController {
        @InitBinder("dispatchPreference")
        void allowedInput(WebDataBinder binder) { binder.setAllowedFields("region"); }

        @PostMapping("/contract/dispatch-preference")
        String update(@ModelAttribute DispatchPreference dispatchPreference) {
            return dispatchPreference.getRegion() + ":" + dispatchPreference.isCanApprove();
        }
    }

    @Test void formBindingIgnoresAnUnapprovedPrivilegeField() throws Exception {
        var mvc = MockMvcBuilders.standaloneSetup(new PreferenceController()).build();
        mvc.perform(post("/contract/dispatch-preference")
                .param("region", "WEST").param("canApprove", "true"))
                .andExpect(status().isOk())
                .andExpect(content().string("WEST:false"));
    }
}
