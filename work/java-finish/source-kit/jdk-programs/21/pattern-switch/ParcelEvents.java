public class ParcelEvents {
    sealed interface ParcelEvent permits Received, Dispatched { }
    record Received(long parcelId) implements ParcelEvent {
        Received { if (parcelId <= 0) throw new IllegalArgumentException("Invalid ID"); }
    }
    record Dispatched(long parcelId, String depot) implements ParcelEvent {
        Dispatched { if (parcelId <= 0) throw new IllegalArgumentException("Invalid ID"); }
    }
    static String describe(ParcelEvent event) {
        return switch (event) {
            case null -> "absent";
            case Received(long id) -> "received=" + id;
            case Dispatched(long id, String depot) -> "dispatched=" + id + ":" + depot;
        };
    }
    public static void main(String[] args) {
        System.out.println(describe(new Dispatched(81, "south")));
        System.out.println(describe(null));
    }
}
