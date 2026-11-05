public class SupportTicket {
    private final String ticketId;

    public SupportTicket(String ticketId) {
        if (ticketId == null || ticketId.trim().isEmpty()) {
            throw new IllegalArgumentException("ticketId is required");
        }
        this.ticketId = ticketId;
    }

    public String id() {
        return ticketId;
    }
}
