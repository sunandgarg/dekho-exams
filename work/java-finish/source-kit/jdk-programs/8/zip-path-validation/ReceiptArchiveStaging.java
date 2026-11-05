import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
public class ReceiptArchiveStaging {
    static Map<Path, byte[]> stage(byte[] archive) throws Exception {
        Path root = Paths.get("receipt-output").toAbsolutePath().normalize();
        Map<Path, byte[]> staged = new LinkedHashMap<>(); int total=0;
        try (ZipInputStream input = new ZipInputStream(new ByteArrayInputStream(archive))) {
            ZipEntry entry;
            while ((entry=input.getNextEntry()) != null) {
                String name=entry.getName();
                if (name.isEmpty() || name.startsWith("/") || name.contains("\\") || name.contains(":")) throw new IllegalArgumentException("Invalid name");
                Path target=root.resolve(name).normalize();
                if (!target.startsWith(root) || target.equals(root)) throw new IllegalArgumentException("Outside root");
                if (entry.isDirectory()) { input.closeEntry(); continue; }
                if (staged.size()==8 || staged.containsKey(target)) throw new IllegalArgumentException("File count or duplicate");
                ByteArrayOutputStream content=new ByteArrayOutputStream(); byte[] buffer=new byte[1024]; int count;
                while ((count=input.read(buffer)) != -1) {
                    if (count>65536-total) throw new IllegalArgumentException("Uncompressed budget");
                    total+=count; content.write(buffer,0,count);
                }
                staged.put(target,content.toByteArray()); input.closeEntry();
            }
        }
        return staged;
    }
    static byte[] archive(String name) throws Exception {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try (ZipOutputStream output=new ZipOutputStream(bytes)) {
            output.putNextEntry(new ZipEntry(name)); output.write("R-51".getBytes(StandardCharsets.UTF_8)); output.closeEntry();
        }
        return bytes.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        System.out.println(stage(archive("reports/receipt.txt")).size());
        try { stage(archive("../outside.txt")); }
        catch (IllegalArgumentException rejected) { System.out.println("traversal rejected"); }
    }
}
