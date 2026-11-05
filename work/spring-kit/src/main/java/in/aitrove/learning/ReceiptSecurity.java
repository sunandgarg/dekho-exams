package in.aitrove.learning;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.config.Customizer;
@Configuration(proxyBeanMethods=false)
public class ReceiptSecurity {
    @Bean PasswordEncoder passwordEncoder() { return PasswordEncoderFactories.createDelegatingPasswordEncoder(); }
    @Bean InMemoryUserDetailsManager readers(PasswordEncoder encoder) {
        // Local source-kit credential only; never deploy this user store.
        return new InMemoryUserDetailsManager(User.withUsername("local-reader")
            .password(encoder.encode("local-fixture-only")).roles("READER").build());
    }
    @Bean SecurityFilterChain receiptChain(HttpSecurity http) throws Exception {
        http.cors(Customizer.withDefaults()).authorizeHttpRequests(requests -> requests
            .requestMatchers("/actuator/health", "/actuator/health/**").permitAll().anyRequest().authenticated())
            .httpBasic(Customizer.withDefaults());
        return http.build(); // CSRF stays enabled for this session-capable learning application.
    }
}
