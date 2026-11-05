import java.nio.charset.StandardCharsets;
import java.util.zip.CRC32;
public class ManifestChecksum {
    static long checksum(byte[] bytes){CRC32 crc=new CRC32();crc.update(bytes);return crc.getValue();}
    public static void main(String[] args) {
        byte[] manifest="receipt=125".getBytes(StandardCharsets.UTF_8);
        long expected=checksum(manifest);System.out.println(expected==checksum(manifest));
        byte[] changed=manifest.clone();changed[changed.length-1]=(byte)'6';
        System.out.println(expected==checksum(changed));
    }
}
