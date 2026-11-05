package in.aitrove.learning;
import java.time.Duration;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotNull;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;
@Validated
@ConfigurationProperties("receipt.import")
public record ImportConfiguration(@Min(1) @Max(500) int batchSize, @NotNull Duration timeout) {}
