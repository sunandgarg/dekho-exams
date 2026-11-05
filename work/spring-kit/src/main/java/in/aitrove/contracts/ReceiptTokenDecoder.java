package in.aitrove.contracts;
import java.security.interfaces.RSAPublicKey;
import java.util.List;
import org.springframework.security.oauth2.core.*;
import org.springframework.security.oauth2.jwt.*;
public final class ReceiptTokenDecoder {
    public static final String ISSUER="https://issuer.fixture.invalid";
    public static JwtDecoder create(RSAPublicKey publicKey) {
        NimbusJwtDecoder decoder=NimbusJwtDecoder.withPublicKey(publicKey).build();
        var audience=new JwtClaimValidator<List<String>>("aud",values->values!=null&&values.contains("receipt-api"));
        decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(JwtValidators.createDefaultWithIssuer(ISSUER),audience));
        return decoder;
    }
}
