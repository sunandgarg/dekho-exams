package in.aitrove.learning;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Qualifier;
@Configuration(proxyBeanMethods = false)
public class QualifiedExportConfig {
    @Bean("csv") ContainerContracts.Exporter csv() { return () -> "csv"; }
    @Bean("archive") ContainerContracts.Exporter archive() { return () -> "archive"; }
    @Bean ContainerContracts.ReceiptReport report(@Qualifier("archive") ContainerContracts.Exporter exporter) {
        return new ContainerContracts.ReceiptReport(exporter);
    }
}
