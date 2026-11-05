import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ServiceLoader;
public class ReceiptProviderDiscovery {
    public interface Exporter { String format(); }
    public static class TextExporter implements Exporter {
        public TextExporter() {}
        public String format() { return "receipt-text"; }
    }
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("receipt-provider-");
        Path services = Files.createDirectories(root.resolve("META-INF/services"));
        Path config = services.resolve(Exporter.class.getName());
        try {
            Files.write(config, (TextExporter.class.getName()+"\n").getBytes(StandardCharsets.UTF_8));
            try (URLClassLoader loader = new URLClassLoader(new URL[]{root.toUri().toURL()}, ReceiptProviderDiscovery.class.getClassLoader())) {
                int count=0;
                for (Exporter exporter : ServiceLoader.load(Exporter.class, loader)) {
                    System.out.println(exporter.format()); count++;
                }
                System.out.println("providers="+count);
            }
        } finally {
            Files.deleteIfExists(config); Files.deleteIfExists(services);
            Files.deleteIfExists(root.resolve("META-INF")); Files.deleteIfExists(root);
        }
    }
}
