public class NestAccessReceipt {
    static class Receipt { private final int accepted = 7; }
    static class Audit { static int read(Receipt receipt) { return receipt.accepted; } }
    public static void main(String[] args) { System.out.println(Audit.read(new Receipt())); }
}
