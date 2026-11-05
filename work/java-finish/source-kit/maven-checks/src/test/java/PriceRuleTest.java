import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

public class PriceRuleTest {
    static long payable(long subtotal, long discount) {
        if (subtotal < 0 || discount < 0 || discount > subtotal) {
            throw new IllegalArgumentException("Invalid price inputs");
        }
        return subtotal - discount;
    }
    @Test void appliesDiscount() { assertEquals(850, payable(1000, 150)); }
    @Test void acceptsZero() { assertEquals(0, payable(0, 0)); }
    @Test void acceptsFullDiscount() { assertEquals(0, payable(1000, 1000)); }
    @Test void rejectsNegativeSubtotal() {
        assertThrows(IllegalArgumentException.class, () -> payable(-1, 0));
    }
    @Test void rejectsNegativeDiscount() {
        assertThrows(IllegalArgumentException.class, () -> payable(100, -1));
    }
    @Test void rejectsExcessDiscount() {
        assertThrows(IllegalArgumentException.class, () -> payable(100, 101));
    }
}
