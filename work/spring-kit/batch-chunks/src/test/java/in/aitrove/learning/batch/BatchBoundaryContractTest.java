package in.aitrove.learning.batch;

import java.util.concurrent.atomic.AtomicBoolean;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.JobExecution;
import org.springframework.batch.core.job.parameters.JobParameters;
import org.springframework.batch.core.job.parameters.JobParametersBuilder;
import org.springframework.batch.core.step.Step;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.launch.JobInstanceAlreadyCompleteException;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.core.configuration.annotation.StepScope;
import org.springframework.batch.infrastructure.item.database.JdbcCursorItemReader;
import org.springframework.batch.infrastructure.item.database.builder.JdbcCursorItemReaderBuilder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringBootTest(classes = BatchBoundaryContractTest.BatchTestApplication.class,
    properties = {"spring.batch.job.enabled=false", "spring.batch.jdbc.initialize-schema=always",
        "spring.datasource.url=jdbc:h2:mem:batch_contract;DB_CLOSE_DELAY=-1"})
class BatchBoundaryContractTest {

    @Autowired JobLauncher launcher;
    @Autowired Job receiptImportJob;
    @Autowired JdbcTemplate jdbc;
    @Autowired AtomicBoolean failOnThirdReceipt;

    private JobParameters parameters(String manifestId) {
        return new JobParametersBuilder().addString("manifestId", manifestId).toJobParameters();
    }

    @BeforeEach
    void prepareBusinessTables() {
        jdbc.execute("CREATE TABLE IF NOT EXISTS receipt_source (id INT PRIMARY KEY, units INT NOT NULL)");
        jdbc.execute("CREATE TABLE IF NOT EXISTS receipt_import (id INT PRIMARY KEY, units INT NOT NULL)");
        jdbc.update("DELETE FROM receipt_import");
        jdbc.update("DELETE FROM receipt_source");
        for (int receiptId = 1; receiptId <= 4; receiptId++) {
            jdbc.update("INSERT INTO receipt_source (id, units) VALUES (?, ?)", receiptId, receiptId * 7);
        }
        failOnThirdReceipt.set(false);
    }

    @Test
    void committedChunkSurvivesFailureAndIdempotentRestartCompletes() throws Exception {
        failOnThirdReceipt.set(true);
        JobExecution failed = launcher.run(receiptImportJob, parameters("MANIFEST-47"));
        assertEquals(BatchStatus.FAILED, failed.getStatus());
        assertEquals(2, countImported());
        assertEquals(2, failed.getStepExecutions().iterator().next()
            .getExecutionContext().getInt("receiptCursor.read.count"));

        failOnThirdReceipt.set(false);
        JobExecution completed = launcher.run(receiptImportJob, parameters("MANIFEST-47"));
        assertEquals(BatchStatus.COMPLETED, completed.getStatus());
        assertEquals(4, countImported());
        assertEquals(7, jdbc.queryForObject("SELECT units FROM receipt_import WHERE id = 1", Integer.class));
        assertEquals(28, jdbc.queryForObject("SELECT units FROM receipt_import WHERE id = 4", Integer.class));
        assertEquals(failed.getJobInstance().getInstanceId(), completed.getJobInstance().getInstanceId());
    }

    @Test
    void completedInstanceDoesNotSilentlyRunAgain() throws Exception {
        JobExecution completed = launcher.run(receiptImportJob, parameters("MANIFEST-93"));
        assertEquals(BatchStatus.COMPLETED, completed.getStatus());
        assertEquals(4, countImported());
        assertThrows(JobInstanceAlreadyCompleteException.class,
            () -> launcher.run(receiptImportJob, parameters("MANIFEST-93")));
        assertEquals(4, countImported());
    }

    private int countImported() {
        return jdbc.queryForObject("SELECT COUNT(*) FROM receipt_import", Integer.class);
    }

    @SpringBootConfiguration
    @EnableAutoConfiguration
    static class BatchTestApplication {
        @Bean AtomicBoolean failOnThirdReceipt() { return new AtomicBoolean(); }

        @Bean
        @StepScope
        JdbcCursorItemReader<ReceiptRow> receiptReader(DataSource dataSource) {
            return new JdbcCursorItemReaderBuilder<ReceiptRow>()
                .name("receiptCursor")
                .dataSource(dataSource)
                .sql("SELECT id, units FROM receipt_source ORDER BY id")
                .rowMapper((result, rowNumber) ->
                    new ReceiptRow(result.getInt("id"), result.getInt("units")))
                .build();
        }

        @Bean
        Step receiptImportStep(JobRepository repository, PlatformTransactionManager transactionManager,
                               JdbcCursorItemReader<ReceiptRow> receiptReader,
                               JdbcTemplate jdbc, AtomicBoolean failOnThirdReceipt) {
            return new StepBuilder("receiptImportStep", repository)
                .<ReceiptRow, ReceiptRow>chunk(2)
                .transactionManager(transactionManager)
                .reader(receiptReader)
                .writer(chunk -> {
                    for (ReceiptRow receipt : chunk) {
                        jdbc.update("MERGE INTO receipt_import (id, units) KEY (id) VALUES (?, ?)",
                            receipt.id(), receipt.units());
                        if (receipt.id() == 3 && failOnThirdReceipt.get()) {
                            throw new IllegalStateException("injected failure after first row of second chunk");
                        }
                    }
                }).build();
        }

        @Bean
        Job receiptImportJob(JobRepository repository, Step receiptImportStep) {
            return new JobBuilder("receiptImportJob", repository).start(receiptImportStep).build();
        }
    }

    record ReceiptRow(int id, int units) { }
}
