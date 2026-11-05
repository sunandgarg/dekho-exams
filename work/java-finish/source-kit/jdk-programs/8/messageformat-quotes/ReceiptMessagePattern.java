import java.text.MessageFormat;
import java.util.Locale;
public class ReceiptMessagePattern {
    public static void main(String[] args) {
        MessageFormat receipt=new MessageFormat("Customer''s receipt: {0}",Locale.ROOT);
        MessageFormat literal=new MessageFormat("Pending '{0}'",Locale.ROOT);
        System.out.println(receipt.format(new Object[]{"R125"}));
        System.out.println(literal.format(new Object[]{"R125"}));
    }
}
