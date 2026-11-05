import java.util.ListResourceBundle;
import java.util.Locale;
import java.util.MissingResourceException;
import java.util.ResourceBundle;
public class ReceiptMessages {
    public static class Labels extends ListResourceBundle {
        protected Object[][] getContents() { return new Object[][]{{"ready", "Ready"}, {"unknown", "Unknown"}}; }
    }
    public static class Labels_fr extends ListResourceBundle {
        protected Object[][] getContents() { return new Object[][]{{"ready", "Pret"}}; }
    }
    public static void main(String[] args) {
        ResourceBundle root = ResourceBundle.getBundle(Labels.class.getName(), Locale.ROOT);
        ResourceBundle french = ResourceBundle.getBundle(Labels.class.getName(), Locale.FRENCH);
        System.out.println(root.getString("ready"));
        System.out.println(french.getString("ready"));
        System.out.println(french.getString("unknown"));
        try { french.getString("deleted"); }
        catch (MissingResourceException rejected) { System.out.println("missing rejected"); }
    }
}
