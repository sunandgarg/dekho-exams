public class OrderStateCodes {
    enum OrderState {
        NEW("new"), PAID("paid"), CANCELLED("cancelled");
        private final String externalCode;
        OrderState(String externalCode) { this.externalCode = externalCode; }
        String externalCode() { return externalCode; }
        boolean canMoveTo(OrderState next) {
            return this == NEW && (next == PAID || next == CANCELLED);
        }
    }
    public static void main(String[] args) {
        OrderState current = OrderState.NEW;
        OrderState requested = OrderState.PAID;
        if (!current.canMoveTo(requested)) {
            throw new IllegalStateException("Rejected order transition");
        }
        System.out.println(requested.externalCode());
        System.out.println(OrderState.CANCELLED.canMoveTo(OrderState.PAID));
    }
}
