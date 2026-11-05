import java.io.StringReader;
import java.util.Properties;
public class ValidatedImportConfig {
    static int batch(String text) throws Exception {
        Properties values = new Properties(); values.load(new StringReader(text));
        for (String key : values.stringPropertyNames())
            if (!key.equals("batch") && !key.equals("mode")) throw new IllegalArgumentException("Unknown setting");
        String raw = values.getProperty("batch");
        if (raw == null) throw new IllegalArgumentException("Missing batch");
        int size = Integer.parseInt(raw);
        if (size < 1 || size > 500) throw new IllegalArgumentException("Batch outside bounds");
        String mode = values.getProperty("mode");
        if (!"summary".equals(mode) && !"detail".equals(mode)) throw new IllegalArgumentException("Invalid mode");
        return size;
    }
    public static void main(String[] args) throws Exception {
        System.out.println(batch("batch=80\nmode=summary"));
        try { batch("batch=0\nmode=detail"); }
        catch (IllegalArgumentException rejected) { System.out.println("range rejected"); }
        try { batch("batch=80\nmode=summary\nmod=detail"); }
        catch (IllegalArgumentException rejected) { System.out.println("unknown rejected"); }
    }
}
