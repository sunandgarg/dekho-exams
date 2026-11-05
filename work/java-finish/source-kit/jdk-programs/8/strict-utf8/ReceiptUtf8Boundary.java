import java.nio.ByteBuffer;
import java.nio.charset.*;
public class ReceiptUtf8Boundary {
    static String decode(byte[] bytes) throws CharacterCodingException {
        if (bytes.length > 4096) throw new IllegalArgumentException("record too large");
        return StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(bytes)).toString();
    }
    public static void main(String[] args) throws Exception {
        System.out.println(decode("amount=125".getBytes(StandardCharsets.UTF_8)));
        try { decode(new byte[]{(byte)0xE2, (byte)0x82}); }
        catch (CharacterCodingException rejected) { System.out.println("malformed rejected"); }
    }
}
