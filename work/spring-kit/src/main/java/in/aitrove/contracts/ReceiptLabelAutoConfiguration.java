package in.aitrove.contracts;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
@AutoConfiguration
public class ReceiptLabelAutoConfiguration {
    public record ReceiptLabel(String prefix) {public String render(long id){return prefix+":"+id;}}
    @Bean @ConditionalOnMissingBean
    public ReceiptLabel receiptLabel(){return new ReceiptLabel("Receipt");}
}
