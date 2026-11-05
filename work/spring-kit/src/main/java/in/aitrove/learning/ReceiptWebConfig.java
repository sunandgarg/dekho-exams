package in.aitrove.learning;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
@Configuration(proxyBeanMethods=false)
public class ReceiptWebConfig implements WebMvcConfigurer {
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/receipts/**").allowedOrigins("https://reader.aitrove.in")
            .allowedMethods("GET", "POST").allowCredentials(true).maxAge(600);
    }
}
