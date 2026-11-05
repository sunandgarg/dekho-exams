package in.aitrove.contracts;

import java.time.Duration;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

/** Child-process entry point used by RelaySettingsProcessTest, not a deployed service. */
public final class RelaySettingsProcessProbe {
    private RelaySettingsProcessProbe() { }

    @Validated
    @ConfigurationProperties("relay")
    record RelaySettings(@Min(1) @Max(100) int batchSize, @NotNull Duration timeout) { }

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(RelaySettings.class)
    static class SettingsConfig { }

    public static void main(String[] args) {
        try (var context = new SpringApplicationBuilder(SettingsConfig.class)
                .web(WebApplicationType.NONE)
                .logStartupInfo(false)
                .properties("relay.batch-size=8", "relay.timeout=2s")
                .run(args)) {
            var settings = context.getBean(RelaySettings.class);
            System.out.println("BOUND_BATCH=" + settings.batchSize());
            System.out.println("BOUND_TIMEOUT=" + settings.timeout().toMillis());
        }
    }
}
