import java.math.*;
import java.text.*;
import java.util.Locale;
public class InvoiceAmountInput {
    static BigDecimal parse(String input) {
        if (input.length() > 32) throw new IllegalArgumentException("amount too long");
        DecimalFormat format = new DecimalFormat("0.00", DecimalFormatSymbols.getInstance(Locale.US));
        format.setGroupingUsed(false); format.setParseBigDecimal(true);
        ParsePosition position = new ParsePosition(0);
        Number parsed = format.parse(input, position);
        if (!(parsed instanceof BigDecimal) || position.getIndex() != input.length())
            throw new IllegalArgumentException("complete decimal required");
        BigDecimal amount = ((BigDecimal) parsed).setScale(2, RoundingMode.UNNECESSARY);
        if (amount.signum() <= 0) throw new IllegalArgumentException("positive amount required");
        return amount;
    }
    public static void main(String[] args) {
        System.out.println(parse("125.50"));
        try { parse("125.50INR"); }
        catch (IllegalArgumentException rejected) { System.out.println("suffix rejected"); }
    }
}
