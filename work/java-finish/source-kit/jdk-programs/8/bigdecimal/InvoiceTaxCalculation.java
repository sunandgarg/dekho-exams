import java.math.BigDecimal;
import java.math.RoundingMode;

public class InvoiceTaxCalculation {
    public static void main(String[] args) {
        BigDecimal subtotal = new BigDecimal("19.95");
        BigDecimal taxRate = new BigDecimal("0.18");
        BigDecimal tax = subtotal.multiply(taxRate).setScale(2, RoundingMode.HALF_UP);
        BigDecimal total = subtotal.add(tax);
        System.out.println("tax=" + tax.toPlainString());
        System.out.println("total=" + total.toPlainString());
        System.out.println(new BigDecimal("2.0").equals(new BigDecimal("2.00")));
        System.out.println(new BigDecimal("2.0").compareTo(new BigDecimal("2.00")) == 0);
    }
}
