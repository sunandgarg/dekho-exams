public class SettlementVariants {
    sealed interface Settlement permits Accepted, Rejected { }
    record Accepted(long cents) implements Settlement {
        Accepted { if (cents < 0) throw new IllegalArgumentException("Negative amount"); }
    }
    record Rejected(String reason) implements Settlement {
        Rejected {
            if (reason == null || reason.isBlank()) throw new IllegalArgumentException("Reason required");
        }
    }
    static String describe(Settlement settlement) {
        if (settlement instanceof Accepted accepted) return "accepted=" + accepted.cents();
        if (settlement instanceof Rejected rejected) return "rejected=" + rejected.reason();
        throw new IllegalArgumentException("Settlement required");
    }
    public static void main(String[] args) {
        System.out.println(describe(new Accepted(1250)));
        System.out.println(describe(new Rejected("expired")));
    }
}
