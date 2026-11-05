import java.util.Comparator;
import java.util.PriorityQueue;

public class SupportTicketQueue {
    static final class Ticket {
        final int urgency;
        final long sequence;
        final String id;
        Ticket(int urgency, long sequence, String id) {
            this.urgency = urgency;
            this.sequence = sequence;
            this.id = id;
        }
    }
    public static void main(String[] args) {
        Comparator<Ticket> order = Comparator.comparingInt((Ticket ticket) -> ticket.urgency)
                .thenComparingLong(ticket -> ticket.sequence);
        PriorityQueue<Ticket> tickets = new PriorityQueue<>(order);
        tickets.add(new Ticket(2, 1, "billing-17"));
        tickets.add(new Ticket(1, 2, "login-42"));
        tickets.add(new Ticket(1, 3, "login-43"));
        while (!tickets.isEmpty()) {
            System.out.println(tickets.poll().id);
        }
    }
}
