import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
public class OpaqueReceiptToken {
    public static void main(String[] args) {
        byte[] entropy = new byte[24];
        new SecureRandom().nextBytes(entropy);
        String encoded = Base64.getUrlEncoder().withoutPadding().encodeToString(entropy);
        byte[] decoded = Base64.getUrlDecoder().decode(encoded);
        System.out.println("characters=" + encoded.length());
        System.out.println("bytes=" + decoded.length);
        System.out.println(MessageDigest.isEqual(entropy, decoded));
    }
}
