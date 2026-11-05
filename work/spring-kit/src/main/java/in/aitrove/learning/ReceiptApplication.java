package in.aitrove.learning;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
@SpringBootApplication
@EnableConfigurationProperties(ImportConfiguration.class)
public class ReceiptApplication {
    public static void main(String[] args) { SpringApplication.run(ReceiptApplication.class, args); }
}
