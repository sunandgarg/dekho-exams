public class DispatchPolicies {
    static abstract class DispatchRequest {
        private final String destination;
        DispatchRequest(String destination) {
            if (destination == null || destination.trim().isEmpty()) {
                throw new IllegalArgumentException("Destination is required");
            }
            this.destination = destination;
        }
        public final String dispatch() { return receipt(destination); }
        protected abstract String receipt(String destination);
    }
    static final class WarehouseRequest extends DispatchRequest {
        WarehouseRequest(String destination) { super(destination); }
        protected String receipt(String destination) {
            return "queued:" + destination;
        }
    }
    public static void main(String[] args) {
        DispatchRequest request = new WarehouseRequest("delhi-warehouse");
        System.out.println(request.dispatch());
    }
}
