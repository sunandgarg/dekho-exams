import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
public class LabelEncoding {
    public static void main(String[] args) {
        String label = "A\uD83D\uDE80e\u0301";
        System.out.println("units=" + label.length());
        System.out.println("points=" + label.codePointCount(0, label.length()));
        System.out.println("bytes=" + label.getBytes(StandardCharsets.UTF_8).length);
        try {
            StandardCharsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(new byte[]{(byte) 0xC3}));
        } catch (CharacterCodingException rejected) {
            System.out.println("Invalid UTF-8 rejected");
        }
    }
}
