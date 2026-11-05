public class ResourceFailureOrder {
    static final class BatchLease implements AutoCloseable {
        @Override
        public void close() {
            throw new IllegalStateException("lease close failed");
        }
    }
    public static void main(String[] args) {
        try (BatchLease lease = new BatchLease()) {
            throw new IllegalArgumentException("batch validation failed");
        } catch (Exception failure) {
            System.out.println(failure.getMessage());
            for (Throwable suppressed : failure.getSuppressed()) {
                System.out.println("suppressed: " + suppressed.getMessage());
            }
        }
    }
}
