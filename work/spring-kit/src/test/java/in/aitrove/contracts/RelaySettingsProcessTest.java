package in.aitrove.contracts;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import static org.junit.jupiter.api.Assertions.*;

/** Launch a real child JVM so environment binding is not a manual PropertySource simulation. */
class RelaySettingsProcessTest {
    @TempDir Path temporaryDirectory;

    private record Result(int exitCode, String output) { }

    private Result run(Map<String, String> environment, Path workingDirectory, String... arguments)
            throws IOException, InterruptedException {
        var command = new ArrayList<String>();
        command.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        command.add("-cp");
        command.add(System.getProperty("java.class.path"));
        command.add(RelaySettingsProcessProbe.class.getName());
        command.addAll(java.util.List.of(arguments));
        var builder = new ProcessBuilder(command)
            .directory(workingDirectory.toFile())
            .redirectErrorStream(true);
        builder.environment().remove("RELAY_BATCHSIZE");
        builder.environment().remove("RELAY_TIMEOUT");
        builder.environment().remove("RELAY_BATCH_SIZE");
        builder.environment().putAll(environment);
        var process = builder.start();
        boolean completed = process.waitFor(20, TimeUnit.SECONDS);
        if (!completed) {
            process.destroyForcibly();
            fail("Child Boot process did not finish within 20 seconds");
        }
        return new Result(process.exitValue(),
            new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }

    @Test void actualEnvironmentBindsTheCanonicalRelayKeys() throws Exception {
        Result result = run(Map.of("RELAY_BATCHSIZE", "29", "RELAY_TIMEOUT", "750ms"),
            temporaryDirectory);
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=29"), result.output());
        assertTrue(result.output().contains("BOUND_TIMEOUT=750"), result.output());
    }

    @Test void commandLineWinsOverTheProcessEnvironment() throws Exception {
        Result result = run(Map.of("RELAY_BATCHSIZE", "29"), temporaryDirectory,
            "--relay.batch-size=31");
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=31"), result.output());
    }

    @Test void invalidEnvironmentValuePreventsStartup() throws Exception {
        Result result = run(Map.of("RELAY_BATCHSIZE", "0"), temporaryDirectory);
        assertNotEquals(0, result.exitCode(), result.output());
        assertFalse(result.output().contains("BOUND_BATCH="), result.output());
    }

    @Test void relativeImportUsesItsDeclaringFileOutsideTheWorkingDirectory() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path launch = Files.createDirectory(temporaryDirectory.resolve("launch"));
        Files.createDirectory(config.resolve("relay"));
        Files.writeString(config.resolve("application.properties"),
            "relay.batch-size=17\nrelay.timeout=750ms\nspring.config.import=relay/worker.properties\n");
        Files.writeString(config.resolve("relay/worker.properties"), "relay.batch-size=29\n");
        Result result = run(Map.of(), launch,
            "--spring.config.additional-location=" + config.toUri());
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=29"), result.output());
        assertTrue(result.output().contains("BOUND_TIMEOUT=750"), result.output());
    }

    @Test void missingRequiredRelativeImportStopsTheChildProcess() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=relay/missing.properties\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertNotEquals(0, result.exitCode(), result.output());
        assertFalse(result.output().contains("BOUND_BATCH="), result.output());
    }

    @Test void secondRelativeImportUsesTheIntermediateFilesDirectory() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path launch = Files.createDirectory(temporaryDirectory.resolve("launch"));
        Path relay = Files.createDirectory(config.resolve("relay"));
        Path overrides = Files.createDirectory(relay.resolve("overrides"));
        Files.writeString(config.resolve("application.properties"),
            "relay.batch-size=11\nrelay.timeout=1s\nspring.config.import=relay/worker.properties\n");
        Files.writeString(relay.resolve("worker.properties"),
            "relay.batch-size=17\nspring.config.import=overrides/late.properties\n");
        Files.writeString(overrides.resolve("late.properties"), "relay.batch-size=37\n");
        Result result = run(Map.of(), launch,
            "--spring.config.additional-location=" + config.toUri());
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=37"), result.output());
        assertTrue(result.output().contains("BOUND_TIMEOUT=1000"), result.output());
    }

    @Test void missingSecondRelativeImportStopsTheChildProcess() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path relay = Files.createDirectory(config.resolve("relay"));
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=relay/worker.properties\n");
        Files.writeString(relay.resolve("worker.properties"),
            "spring.config.import=overrides/missing.properties\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertNotEquals(0, result.exitCode(), result.output());
        assertFalse(result.output().contains("BOUND_BATCH="), result.output());
    }

    @Test void fileTreeImportBindsValuesWithoutPrintingASecret() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path tree = Files.createDirectory(temporaryDirectory.resolve("mounted-values"));
        Path relay = Files.createDirectory(tree.resolve("relay"));
        Files.writeString(relay.resolve("batch-size"), "41\n");
        Files.writeString(relay.resolve("timeout"), "1500ms\n");
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=configtree:" + tree.toAbsolutePath() + "/\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=41"), result.output());
        assertTrue(result.output().contains("BOUND_TIMEOUT=1500"), result.output());
    }

    @Test void environmentValueOverridesTheImportedFileTree() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path tree = Files.createDirectory(temporaryDirectory.resolve("mounted-values"));
        Path relay = Files.createDirectory(tree.resolve("relay"));
        Files.writeString(relay.resolve("batch-size"), "41\n");
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=configtree:" + tree.toAbsolutePath() + "/\n");
        Result result = run(Map.of("RELAY_BATCHSIZE", "44"), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=44"), result.output());
    }

    @Test void missingRequiredFileTreeStopsStartup() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path absentTree = temporaryDirectory.resolve("absent-values");
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=configtree:" + absentTree.toAbsolutePath() + "/\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertNotEquals(0, result.exitCode(), result.output());
        assertFalse(result.output().contains("BOUND_BATCH="), result.output());
    }

    @Test void invalidValueInFileTreeFailsValidation() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path tree = Files.createDirectory(temporaryDirectory.resolve("mounted-values"));
        Path relay = Files.createDirectory(tree.resolve("relay"));
        Files.writeString(relay.resolve("batch-size"), "0\n");
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=configtree:" + tree.toAbsolutePath() + "/\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertNotEquals(0, result.exitCode(), result.output());
        assertFalse(result.output().contains("BOUND_BATCH="), result.output());
    }

    @Test void extensionlessPropertiesFileNeedsAnExtensionHint() throws Exception {
        Path config = Files.createDirectory(temporaryDirectory.resolve("config"));
        Path values = Files.writeString(temporaryDirectory.resolve("relay-values"),
            "relay.batch-size=47\nrelay.timeout=2s\n");
        Files.writeString(config.resolve("application.properties"),
            "spring.config.import=" + values.toUri() + "[.properties]\n");
        Result result = run(Map.of(), temporaryDirectory,
            "--spring.config.additional-location=" + config.toUri());
        assertEquals(0, result.exitCode(), result.output());
        assertTrue(result.output().contains("BOUND_BATCH=47"), result.output());
        assertTrue(result.output().contains("BOUND_TIMEOUT=2000"), result.output());
    }
}
