public class QuantityValidation {
    static int parseQuantity(String rawQuantity) {
        final int quantity;
        try {
            quantity = Integer.parseInt(rawQuantity);
        } catch (NumberFormatException invalidNumber) {
            throw new IllegalArgumentException("Quantity must be a whole number", invalidNumber);
        }
        if (quantity < 1 || quantity > 500) {
            throw new IllegalArgumentException("Quantity must be between 1 and 500");
        }
        return quantity;
    }
    public static void main(String[] args) {
        System.out.println(parseQuantity("12"));
        try {
            parseQuantity("many");
        } catch (IllegalArgumentException rejectedInput) {
            System.out.println(rejectedInput.getMessage());
            System.out.println(rejectedInput.getCause().getClass().getSimpleName());
        }
    }
}
