import java.text.Normalizer;
public class CustomerLabelNormalization {
    public static void main(String[] args) {
        String composed = "Caf\u00e9";
        String decomposed = "Cafe\u0301";
        System.out.println(composed.equals(decomposed));
        String normalized = Normalizer.normalize(decomposed, Normalizer.Form.NFC);
        System.out.println(composed.equals(normalized));
        System.out.println(decomposed.codePointCount(0, decomposed.length()));
        System.out.println(normalized.codePointCount(0, normalized.length()));
    }
}
