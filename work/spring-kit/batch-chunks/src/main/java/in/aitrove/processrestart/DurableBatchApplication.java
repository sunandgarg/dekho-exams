package in.aitrove.processrestart;

import java.util.Map;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

import javax.sql.DataSource;

import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.JobExecution;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.job.parameters.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.launch.JobOperator;
import org.springframework.batch.core.launch.JobExecutionAlreadyRunningException;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.repository.explore.JobExplorer;
import org.springframework.batch.core.step.Step;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.infrastructure.item.database.JdbcCursorItemReader;
import org.springframework.batch.infrastructure.item.database.builder.JdbcCursorItemReaderBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;

@SpringBootApplication
public class DurableBatchApplication {
    public static void main(String[] args) throws Exception {
        if (args.length < 3 || args.length > 4) {
            throw new IllegalArgumentException("database URL, mode, manifest ID and optional mode argument required");
        }
        String mode = args[1];
        if (!mode.equals("fail") && !mode.equals("resume") && !mode.equals("pause") &&
            !mode.equals("probe") && !mode.equals("recover")) {
            throw new IllegalArgumentException("unknown test mode");
        }
        if (mode.equals("pause") && args.length != 4) {
            throw new IllegalArgumentException("pause requires a marker path");
        }
        if (mode.equals("recover") && (args.length != 4 || !args[3].equals("CONFIRMED_DEAD"))) {
            throw new IllegalArgumentException("recover requires explicit dead-worker confirmation");
        }
        SpringApplication application = new SpringApplication(DurableBatchApplication.class);
        application.setWebApplicationType(WebApplicationType.NONE);
        application.setDefaultProperties(Map.of(
            "spring.batch.job.enabled", "false",
            "spring.batch.jdbc.initialize-schema", (mode.equals("fail") || mode.equals("pause")) ? "always" : "never",
            "spring.datasource.url", args[0],
            "import.fail-third", Boolean.toString(mode.equals("fail")),
            "import.pause-third", Boolean.toString(mode.equals("pause")),
            "import.marker-path", mode.equals("pause") ? args[3] : ""));
        try (ConfigurableApplicationContext context = application.run()) {
            JdbcTemplate jdbc = context.getBean(JdbcTemplate.class);
            jdbc.execute("CREATE TABLE IF NOT EXISTS receipt_source (id INT PRIMARY KEY, units INT NOT NULL)");
            jdbc.execute("CREATE TABLE IF NOT EXISTS receipt_import (id INT PRIMARY KEY, units INT NOT NULL)");
            jdbc.execute("CREATE TABLE IF NOT EXISTS receipt_manifest (manifest_id VARCHAR(120) PRIMARY KEY, source_hash VARCHAR(64) NOT NULL)");
            if (jdbc.queryForObject("SELECT COUNT(*) FROM receipt_source", Integer.class) == 0) {
                for (int receiptId = 1; receiptId <= 4; receiptId++) {
                    jdbc.update("INSERT INTO receipt_source (id, units) VALUES (?, ?)",
                        receiptId, receiptId * 11);
                }
            }
            String sourceHash = sourceHash(jdbc);
            String storedHash = jdbc.query("SELECT source_hash FROM receipt_manifest WHERE manifest_id = ?",
                result -> result.next() ? result.getString(1) : null, args[2]);
            if (storedHash == null) {
                jdbc.update("INSERT INTO receipt_manifest (manifest_id, source_hash) VALUES (?, ?)", args[2], sourceHash);
            } else if (!storedHash.equals(sourceHash)) {
                throw new IllegalStateException("source changed for manifest " + args[2]);
            }
            Job job = context.getBean(Job.class);
            var parameters = new JobParametersBuilder().addString("manifestId", args[2]).toJobParameters();
            JobExecution execution;
            if (mode.equals("recover")) {
                JobExecution stale = context.getBean(JobExplorer.class)
                    .getLastJobExecution(job.getName(), parameters);
                if (stale == null || !stale.getStatus().isRunning()) {
                    throw new IllegalStateException("no running execution to recover");
                }
                context.getBean(JobOperator.class).recover(stale);
                execution = context.getBean(JobLauncher.class).run(job, parameters);
            } else if (mode.equals("probe")) {
                try {
                    context.getBean(JobLauncher.class).run(job, parameters);
                    throw new IllegalStateException("orphaned execution unexpectedly relaunched");
                } catch (JobExecutionAlreadyRunningException expected) {
                    System.out.println("BLOCKED_RUNNING manifest=" + args[2]);
                    return;
                }
            } else {
                execution = context.getBean(JobLauncher.class).run(job, parameters);
            }
            int count = jdbc.queryForObject("SELECT COUNT(*) FROM receipt_import", Integer.class);
            String ids = String.join(",", jdbc.queryForList(
                "SELECT CAST(id AS VARCHAR) FROM receipt_import ORDER BY id", String.class));
            System.out.println("RESULT status=" + execution.getStatus() + " rows=" + count +
                " ids=" + ids + " instance=" + execution.getJobInstance().getInstanceId());
        }
    }

    private static String sourceHash(JdbcTemplate jdbc) throws Exception {
        String input = String.join("\n", jdbc.queryForList(
            "SELECT CONCAT(id, ':', units) FROM receipt_source ORDER BY id", String.class));
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
            .digest(input.getBytes(StandardCharsets.UTF_8)));
    }

    @Bean
    @StepScope
    JdbcCursorItemReader<ReceiptRow> receiptReader(DataSource dataSource) {
        return new JdbcCursorItemReaderBuilder<ReceiptRow>()
            .name("durableReceiptCursor")
            .dataSource(dataSource)
            .sql("SELECT id, units FROM receipt_source ORDER BY id")
            .rowMapper((result, rowNumber) ->
                new ReceiptRow(result.getInt("id"), result.getInt("units")))
            .build();
    }

    @Bean
    Step durableReceiptStep(JobRepository repository, PlatformTransactionManager transactionManager,
                            JdbcCursorItemReader<ReceiptRow> receiptReader, JdbcTemplate jdbc,
                            @Value("${import.fail-third:false}") boolean failThird,
                            @Value("${import.pause-third:false}") boolean pauseThird,
                            @Value("${import.marker-path:}") String markerPath) {
        return new StepBuilder("durableReceiptStep", repository)
            .<ReceiptRow, ReceiptRow>chunk(2)
            .transactionManager(transactionManager)
            .reader(receiptReader)
            .processor(row -> {
                if (pauseThird && row.id() == 3) {
                    Files.writeString(Path.of(markerPath), "first chunk committed");
                    Thread.sleep(60_000);
                }
                return row;
            })
            .writer(chunk -> {
                for (ReceiptRow row : chunk) {
                    jdbc.update("MERGE INTO receipt_import (id, units) KEY (id) VALUES (?, ?)",
                        row.id(), row.units());
                    if (failThird && row.id() == 3) {
                        throw new IllegalStateException("injected failure after earlier chunk commit");
                    }
                }
            }).build();
    }

    @Bean
    Job durableReceiptJob(JobRepository repository, Step durableReceiptStep) {
        return new JobBuilder("durableReceiptJob", repository).start(durableReceiptStep).build();
    }

    record ReceiptRow(int id, int units) { }
}
