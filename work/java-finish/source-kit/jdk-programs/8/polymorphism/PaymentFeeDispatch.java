public class PaymentFeeDispatch {
    interface PaymentFee {
        int feeCents(int amountCents);
    }
    static final class CashFee implements PaymentFee {
        public int feeCents(int amountCents) {
            if (amountCents < 0) throw new IllegalArgumentException("Negative amount");
            return Math.max(10, amountCents / 100);
        }
    }
    static final class TransferFee implements PaymentFee {
        public int feeCents(int amountCents) {
            if (amountCents < 0) throw new IllegalArgumentException("Negative amount");
            return 25;
        }
    }
    public static void main(String[] args) {
        PaymentFee[] policies = {new CashFee(), new TransferFee()};
        for (PaymentFee policy : policies) {
            System.out.println(policy.feeCents(1200));
        }
    }
}
