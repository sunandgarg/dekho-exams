import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.channels.FileChannel;
import java.nio.file.*;
public class ManifestHeaderChannel {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("aitrove-header-", ".bin");
        try {
            ByteBuffer header = ByteBuffer.allocate(12).order(ByteOrder.BIG_ENDIAN);
            header.putInt(7).putInt(42).putInt(3).flip();
            try (FileChannel channel = FileChannel.open(file, StandardOpenOption.WRITE, StandardOpenOption.READ)) {
                while (header.hasRemaining()) channel.write(header);
                channel.position(0);
                ByteBuffer restored = ByteBuffer.allocate(12).order(ByteOrder.BIG_ENDIAN);
                while (restored.hasRemaining() && channel.read(restored) != -1) { }
                if (restored.position() != 12) throw new IllegalStateException("Truncated header");
                restored.flip();
                System.out.println(restored.getInt() + ":" + restored.getInt() + ":" + restored.getInt());
            }
        } finally { Files.deleteIfExists(file); }
    }
}
