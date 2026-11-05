public class QuantityConversions {
    public static void main(String[] args) {
        long accumulated = 3_000_000_000L;
        try { Math.toIntExact(accumulated); }
        catch (ArithmeticException rejected) { System.out.println("Quantity rejected"); }
        System.out.println((byte) 260);
        int measured = Integer.MAX_VALUE;
        System.out.println((long) measured + 1);
        Object receipt = "RC-81";
        System.out.println(((String) receipt).length());
        try { Integer unused = (Integer) receipt; }
        catch (ClassCastException rejected) { System.out.println("Wrong reference type"); }
    }
}
