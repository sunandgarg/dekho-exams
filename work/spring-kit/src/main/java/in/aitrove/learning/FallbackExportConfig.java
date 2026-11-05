package in.aitrove.learning;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
@Configuration(proxyBeanMethods = false)
public class FallbackExportConfig {
    @Bean @ConditionalOnMissingBean(ContainerContracts.Exporter.class)
    ContainerContracts.Exporter fallbackExporter() { return () -> "fallback"; }
}
