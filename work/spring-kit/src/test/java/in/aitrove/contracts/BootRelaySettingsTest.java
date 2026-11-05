package in.aitrove.contracts;

import java.time.Duration;
import java.nio.file.Files;
import java.nio.file.Path;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import org.springframework.validation.annotation.Validated;

import static org.junit.jupiter.api.Assertions.*;

/** Start a small Boot context to check actual command-line and default binding. */
class BootRelaySettingsTest {
    @TempDir Path configDirectory;
    @Validated
    @ConfigurationProperties("relay")
    record RelaySettings(@Min(1) @Max(100) int batchSize, @NotNull Duration timeout) { }

    @Configuration(proxyBeanMethods = false)
    @EnableConfigurationProperties(RelaySettings.class)
    static class SettingsConfig { }

    private SpringApplicationBuilder app() {
        return new SpringApplicationBuilder(SettingsConfig.class)
            .web(WebApplicationType.NONE)
            .logStartupInfo(false)
            .properties("relay.batch-size=8", "relay.timeout=2s");
    }

    @Test void commandLineOverridesPackagedDefaults() {
        try (var context = app().run("--relay.batch-size=12")) {
            var settings = context.getBean(RelaySettings.class);
            assertEquals(12, settings.batchSize());
            assertEquals(Duration.ofSeconds(2), settings.timeout());
        }
    }

    @Test void explicitDurationUnitBindsWithoutGuessingMilliseconds() {
        try (var context = app().run("--relay.timeout=450ms")) {
            assertEquals(Duration.ofMillis(450), context.getBean(RelaySettings.class).timeout());
        }
    }

    @Test void invalidEffectiveBatchSizePreventsStartup() {
        assertThrows(RuntimeException.class, () -> app().run("--relay.batch-size=0"));
    }

    @Test void additionalPropertiesFileOverridesPackagedDefaults() throws Exception {
        Files.writeString(configDirectory.resolve("application.properties"),
            "relay.batch-size=17\nrelay.timeout=750ms\n");
        try (var context = app().run("--spring.config.additional-location=" + configDirectory.toUri())) {
            var settings = context.getBean(RelaySettings.class);
            assertEquals(17, settings.batchSize());
            assertEquals(Duration.ofMillis(750), settings.timeout());
        }
    }

    @Test void commandLineOverridesAdditionalPropertiesFile() throws Exception {
        Files.writeString(configDirectory.resolve("application.properties"),
            "relay.batch-size=17\nrelay.timeout=750ms\n");
        try (var context = app().run("--spring.config.additional-location=" + configDirectory.toUri(),
                                     "--relay.batch-size=23")) {
            var settings = context.getBean(RelaySettings.class);
            assertEquals(23, settings.batchSize());
            assertEquals(Duration.ofMillis(750), settings.timeout());
        }
    }

    @Test void activeProfileLoadsItsFileOverTheBaseFile() throws Exception {
        Files.writeString(configDirectory.resolve("application.properties"),
            "relay.batch-size=17\nrelay.timeout=750ms\n");
        Files.writeString(configDirectory.resolve("application-review.properties"),
            "relay.batch-size=29\n");
        try (var context = app().run("--spring.config.additional-location=" + configDirectory.toUri(),
                                     "--spring.profiles.active=review")) {
            var settings = context.getBean(RelaySettings.class);
            assertEquals(29, settings.batchSize());
            assertEquals(Duration.ofMillis(750), settings.timeout());
        }
    }

    @Test void requiredImportFailsBeforeAWorkerCanStart() {
        String missing = configDirectory.resolve("missing.properties").toUri().toString();
        assertThrows(RuntimeException.class, () -> app().run("--spring.config.import=" + missing));
    }

    @Test void optionalMissingImportKeepsTheDeclaredDefaults() {
        String missing = configDirectory.resolve("missing.properties").toUri().toString();
        try (var context = app().run("--spring.config.import=optional:" + missing)) {
            var settings = context.getBean(RelaySettings.class);
            assertEquals(8, settings.batchSize());
            assertEquals(Duration.ofSeconds(2), settings.timeout());
        }
    }
}
