public class WalletBoundary {
    static class WarehouseWallet {
        private int credits;
        WarehouseWallet(int initialCredits) {
            if (initialCredits < 0) throw new IllegalArgumentException("Negative balance");
            credits = initialCredits;
        }
        public boolean debit(int amount) {
            if (amount <= 0) throw new IllegalArgumentException("Positive debit required");
            if (amount > credits) return false;
            credits -= amount;
            return true;
        }
        public int balance() { return credits; }
    }
    public static void main(String[] args) {
        WarehouseWallet wallet = new WarehouseWallet(40);
        System.out.println(wallet.debit(12));
        System.out.println(wallet.debit(50));
        System.out.println("balance=" + wallet.balance());
    }
}
