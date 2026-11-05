public class ReceiptDispatch {
    static String format(Object value) { return "object"; }
    static String format(String value) { return "text"; }
    static class Receipt {
        String render() { return "standard"; }
    }
    static class SpecializedReceipt extends Receipt {
        @Override String render() { return "priority"; }
    }
    public static void main(String[] args) {
        Object storedLabel = "paid";
        System.out.println(format(storedLabel));
        System.out.println(format((String) storedLabel));
        Receipt receipt = new SpecializedReceipt();
        System.out.println(receipt.render());
        System.out.println(format((String) null));
    }
}
