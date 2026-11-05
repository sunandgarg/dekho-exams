package in.aitrove.learning.batch;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import javax.sql.DataSource;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.JobExecution;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.job.parameters.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.listener.SkipListener;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.Step;
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
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(classes = BatchFaultPolicyContractTest.FaultPolicyApplication.class,
    properties = {"spring.batch.job.enabled=false", "spring.batch.jdbc.initialize-schema=always",
        "spring.datasource.url=jdbc:h2:mem:batch_fault_policy;DB_CLOSE_DELAY=-1"})
class BatchFaultPolicyContractTest {
    @Autowired JobLauncher launcher;
    @Autowired Job receiptPolicyJob;
    @Autowired JdbcTemplate jdbc;
    @Autowired AtomicInteger transientAttempts;
    @Autowired AtomicBoolean alwaysFailTransient;

    @BeforeEach
    void resetRows() {
        jdbc.execute("CREATE TABLE IF NOT EXISTS policy_source (id INT PRIMARY KEY, units INT NOT NULL)");
        jdbc.execute("CREATE TABLE IF NOT EXISTS policy_target (id INT PRIMARY KEY, units INT NOT NULL)");
        jdbc.execute("CREATE TABLE IF NOT EXISTS policy_rejection (id INT PRIMARY KEY, reason_code VARCHAR(40) NOT NULL)");
        jdbc.update("DELETE FROM policy_target");
        jdbc.update("DELETE FROM policy_rejection");
        jdbc.update("DELETE FROM policy_source");
        transientAttempts.set(0);
        alwaysFailTransient.set(false);
    }

    @Test
    void skipsOneInvalidRowAndRetriesOneTemporaryFailure() throws Exception {
        insert(1, 7); insert(2, -1); insert(3, 47); insert(4, 28);
        JobExecution run = launch("POLICY-47");
        assertEquals(BatchStatus.COMPLETED, run.getStatus());
        assertEquals(3, imported());
        assertEquals(1, run.getStepExecutions().iterator().next().getSkipCount());
        assertTrue(transientAttempts.get() >= 2);
        assertEquals(47, jdbc.queryForObject("SELECT units FROM policy_target WHERE id = 3", Integer.class));
        assertEquals(1, rejected());
        assertEquals("INVALID_UNITS", jdbc.queryForObject(
            "SELECT reason_code FROM policy_rejection WHERE id = 2", String.class));
    }

    @Test
    void secondInvalidRowExceedsOneRowSkipBudget() throws Exception {
        insert(1, 7); insert(2, -1); insert(3, -1); insert(4, 28);
        JobExecution run = launch("POLICY-93");
        assertEquals(BatchStatus.FAILED, run.getStatus());
        assertEquals(1, run.getStepExecutions().iterator().next().getSkipCount());
        assertEquals(1, imported());
        assertEquals(1, rejected());
    }

    @Test
    void exhaustedTemporaryFailureStopsTheJob() throws Exception {
        insert(1, 7); insert(2, 47);
        alwaysFailTransient.set(true);
        JobExecution run = launch("POLICY-119");
        assertEquals(BatchStatus.FAILED, run.getStatus());
        assertTrue(transientAttempts.get() >= 2);
        assertEquals(0, imported());
        assertEquals(0, rejected());
    }

    private void insert(int id, int units) {
        jdbc.update("INSERT INTO policy_source (id, units) VALUES (?, ?)", id, units);
    }

    private int imported() {
        return jdbc.queryForObject("SELECT COUNT(*) FROM policy_target", Integer.class);
    }

    private int rejected() {
        return jdbc.queryForObject("SELECT COUNT(*) FROM policy_rejection", Integer.class);
    }

    private JobExecution launch(String manifestId) throws Exception {
        return launcher.run(receiptPolicyJob, new JobParametersBuilder()
            .addString("manifestId", manifestId).toJobParameters());
    }

    @SpringBootConfiguration
    @EnableAutoConfiguration
    static class FaultPolicyApplication {
        @Bean AtomicInteger transientAttempts() { return new AtomicInteger(); }
        @Bean AtomicBoolean alwaysFailTransient() { return new AtomicBoolean(); }

        @Bean
        @StepScope
        JdbcCursorItemReader<PolicyRow> policyReader(DataSource dataSource) {
            return new JdbcCursorItemReaderBuilder<PolicyRow>()
                .name("policyCursor")
                .dataSource(dataSource)
                .sql("SELECT id, units FROM policy_source ORDER BY id")
                .rowMapper((result, rowNumber) ->
                    new PolicyRow(result.getInt("id"), result.getInt("units")))
                .build();
        }

        @Bean
        Step receiptPolicyStep(JobRepository repository, PlatformTransactionManager transactionManager,
                               JdbcCursorItemReader<PolicyRow> policyReader, JdbcTemplate jdbc,
                               AtomicInteger transientAttempts, AtomicBoolean alwaysFailTransient) {
            return new StepBuilder("receiptPolicyStep", repository)
                .<PolicyRow, PolicyRow>chunk(2)
                .transactionManager(transactionManager)
                .reader(policyReader)
                .processor(row -> {
                    if (row.units() < 0) throw new InvalidReceiptException();
                    if (row.units() == 47 &&
                        (alwaysFailTransient.get() || transientAttempts.getAndIncrement() == 0)) {
                        if (alwaysFailTransient.get()) transientAttempts.incrementAndGet();
                        throw new TemporaryReceiptException();
                    }
                    return row;
                })
                .writer(chunk -> {
                    for (PolicyRow row : chunk) {
                        jdbc.update("INSERT INTO policy_target (id, units) VALUES (?, ?)",
                            row.id(), row.units());
                    }
                })
                .faultTolerant()
                .skip(InvalidReceiptException.class).skipLimit(1)
                .retry(TemporaryReceiptException.class).retryLimit(2)
                .listener(new SkipListener<PolicyRow, PolicyRow>() {
                    @Override
                    public void onSkipInProcess(PolicyRow row, Throwable failure) {
                        jdbc.update("MERGE INTO policy_rejection (id, reason_code) KEY(id) VALUES (?, ?)",
                            row.id(), "INVALID_UNITS");
                    }
                })
                .build();
        }

        @Bean
        Job receiptPolicyJob(JobRepository repository, Step receiptPolicyStep) {
            return new JobBuilder("receiptPolicyJob", repository).start(receiptPolicyStep).build();
        }
    }

    record PolicyRow(int id, int units) { }
    static class InvalidReceiptException extends RuntimeException { }
    static class TemporaryReceiptException extends RuntimeException { }
}
