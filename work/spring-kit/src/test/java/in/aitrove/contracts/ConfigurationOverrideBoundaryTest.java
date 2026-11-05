package in.aitrove.contracts;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.junit.jupiter.api.Test;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.MapPropertySource;
import org.springframework.validation.annotation.Validated;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

public class ConfigurationOverrideBoundaryTest {
    @ConfigurationProperties("import") @Validated
    public record ImportSettings(@Min(1) @Max(60) int timeoutSeconds) { }

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(ImportSettings.class)
    static class SettingsConfig { }

    @Test void selectsAndValidatesTheEffectiveTimeout() {
        new ApplicationContextRunner().withUserConfiguration(SettingsConfig.class)
            .withInitializer(context -> {
                var sources = context.getEnvironment().getPropertySources();
                sources.addLast(new MapPropertySource("packaged-defaults", Map.of("import.timeout-seconds", "8")));
                sources.addFirst(new MapPropertySource("operator-overrides", Map.of("import.timeout-seconds", "12")));
            })
            .run(context -> {
                assertNull(context.getStartupFailure());
                assertEquals(12, context.getBean(ImportSettings.class).timeoutSeconds());
            });
        new ApplicationContextRunner().withUserConfiguration(SettingsConfig.class)
            .withPropertyValues("import.timeout-seconds=70")
            .run(context -> assertNotNull(context.getStartupFailure()));
    }
}
