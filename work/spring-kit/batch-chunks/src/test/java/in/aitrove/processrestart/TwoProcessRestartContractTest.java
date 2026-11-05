package in.aitrove.processrestart;

import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Duration;
import java.sql.DriverManager;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

class TwoProcessRestartContractTest {
    @TempDir Path temporaryDirectory;

    @Test
    void failedProcessLeavesCommittedChunkForSecondJvmWithSameIdentity() throws Exception {
        String databaseUrl = databaseUrl();
        String first = launch(databaseUrl, "fail", "MANIFEST-263");
        String second = launch(databaseUrl, "resume", "MANIFEST-263");
        assertTrue(first.contains("RESULT status=FAILED rows=2 ids=1,2"), first);
        assertTrue(second.contains("RESULT status=COMPLETED rows=4 ids=1,2,3,4"), second);
        assertEquals(instance(first), instance(second));
        assertEquals(1, count(databaseUrl, "BATCH_JOB_INSTANCE"));
        assertEquals(2, count(databaseUrl, "BATCH_JOB_EXECUTION"));
    }

    @Test
    void abruptDeathLeavesRunningExecutionUntilExplicitRecovery() throws Exception {
        String databaseUrl = databaseUrl();
        String manifestId = "MANIFEST-347";
        Path marker = temporaryDirectory.resolve("first-chunk-committed.marker");
        Process worker = process(databaseUrl, "pause", manifestId, marker.toString());
        try {
            long deadline = System.nanoTime() + Duration.ofSeconds(30).toNanos();
            while (!Files.exists(marker) && worker.isAlive() && System.nanoTime() < deadline) {
                Thread.sleep(25);
            }
            assertTrue(Files.exists(marker), Files.readString(temporaryDirectory.resolve("batch-pause.log")));
        } finally {
            worker.destroyForcibly();
            assertTrue(worker.waitFor(10, TimeUnit.SECONDS));
        }
        assertFalse(worker.isAlive());
        assertEquals(2, count(databaseUrl, "receipt_import"));
        assertEquals("STARTED", storedStatus(databaseUrl));

        String blocked = launch(databaseUrl, "probe", manifestId);
        assertTrue(blocked.contains("BLOCKED_RUNNING manifest=" + manifestId), blocked);
        String recovered = launch(databaseUrl, "recover", manifestId, "CONFIRMED_DEAD");
        assertTrue(recovered.contains("RESULT status=COMPLETED rows=4 ids=1,2,3,4"), recovered);
        assertEquals(4, count(databaseUrl, "receipt_import"));
        assertEquals(1, count(databaseUrl, "BATCH_JOB_INSTANCE"));
        assertEquals(2, count(databaseUrl, "BATCH_JOB_EXECUTION"));
    }

    @Test
    void changedInputRejectsRestartBeforeImport() throws Exception {
        String databaseUrl = databaseUrl();
        String first = launch(databaseUrl, "fail", "MANIFEST-421");
        assertTrue(first.contains("RESULT status=FAILED rows=2 ids=1,2"), first);
        try (var connection = DriverManager.getConnection(databaseUrl);
             var update = connection.prepareStatement("UPDATE receipt_source SET units = ? WHERE id = ?")) {
            update.setInt(1, 82);
            update.setInt(2, 4);
            assertEquals(1, update.executeUpdate());
        }
        RunResult rejected = run(databaseUrl, "resume", "MANIFEST-421");
        assertTrue(rejected.exitCode() != 0, rejected.output());
        assertTrue(rejected.output().contains("source changed for manifest MANIFEST-421"), rejected.output());
        assertEquals(2, count(databaseUrl, "receipt_import"));
        assertEquals(1, count(databaseUrl, "BATCH_JOB_EXECUTION"));
    }

    private String databaseUrl() {
        return "jdbc:h2:file:" + temporaryDirectory.resolve("durable-receipts") +
            ";DB_CLOSE_ON_EXIT=FALSE;WRITE_DELAY=0";
    }

    private int count(String databaseUrl, String table) throws Exception {
        try (var connection = DriverManager.getConnection(databaseUrl);
             var query = connection.prepareStatement("SELECT COUNT(*) FROM " + table);
             var result = query.executeQuery()) {
            assertTrue(result.next());
            return result.getInt(1);
        }
    }

    private String storedStatus(String databaseUrl) throws Exception {
        try (var connection = DriverManager.getConnection(databaseUrl);
             var query = connection.prepareStatement("SELECT STATUS FROM BATCH_JOB_EXECUTION ORDER BY JOB_EXECUTION_ID DESC LIMIT 1");
             var result = query.executeQuery()) {
            assertTrue(result.next());
            return result.getString(1);
        }
    }

    private String launch(String databaseUrl, String mode, String manifestId, String... option) throws Exception {
        RunResult result = run(databaseUrl, mode, manifestId, option);
        assertEquals(0, result.exitCode(), result.output());
        return result.output();
    }

    private RunResult run(String databaseUrl, String mode, String manifestId, String... option) throws Exception {
        Process process = process(databaseUrl, mode, manifestId, option);
        boolean finished = process.waitFor(Duration.ofSeconds(45).toMillis(), TimeUnit.MILLISECONDS);
        if (!finished) {
            process.destroyForcibly();
            throw new AssertionError("child batch process exceeded 45 seconds");
        }
        String output = Files.readString(temporaryDirectory.resolve("batch-" + mode + ".log"));
        return new RunResult(process.exitValue(), output);
    }

    private Process process(String databaseUrl, String mode, String manifestId, String... option) throws Exception {
        String classpath = System.getProperty("surefire.test.class.path",
            System.getProperty("java.class.path"));
        Path outputFile = temporaryDirectory.resolve("batch-" + mode + ".log");
        var command = new java.util.ArrayList<>(java.util.List.of(
            Path.of(System.getProperty("java.home"), "bin", "java").toString(),
            "-cp", classpath, DurableBatchApplication.class.getName(),
            databaseUrl, mode, manifestId));
        command.addAll(java.util.List.of(option));
        return new ProcessBuilder(command).redirectErrorStream(true)
            .redirectOutput(outputFile.toFile()).start();
    }

    private long instance(String output) {
        Matcher result = Pattern.compile("RESULT status=\\w+ rows=\\d+ ids=[\\d,]+ instance=(\\d+)")
            .matcher(output);
        assertTrue(result.find(), output);
        return Long.parseLong(result.group(1));
    }

    private record RunResult(int exitCode, String output) { }
}
