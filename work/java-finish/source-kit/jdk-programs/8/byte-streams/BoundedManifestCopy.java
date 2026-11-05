import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;
public class BoundedManifestCopy {
    static long copy(InputStream input, OutputStream output, long limit) throws IOException {
        if (limit < 0) throw new IllegalArgumentException("Negative limit");
        byte[] buffer = new byte[3];
        long copied = 0;
        int count;
        while ((count = input.read(buffer)) != -1) {
            if (count > limit - copied) throw new IOException("Payload too large");
            output.write(buffer, 0, count);
            copied += count;
        }
        return copied;
    }
    public static void main(String[] args) throws IOException {
        byte[] manifest = {4, 8, 15, 16, 23, 42, 50};
        try (ByteArrayInputStream input = new ByteArrayInputStream(manifest);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            System.out.println("copied=" + copy(input, output, 10));
            System.out.println(Arrays.toString(output.toByteArray()));
        }
    }
}
