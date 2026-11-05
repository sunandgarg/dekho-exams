public class WarehouseSnapshot {
    private final String warehouseId;
    WarehouseSnapshot(String warehouseId) { this.warehouseId = warehouseId; }
    static final class ShipmentState {
        private final String id;
        private final String state;
        ShipmentState(String id, String state) {
            this.id = id;
            this.state = state;
        }
        String render() { return id + ":" + state; }
    }
    ShipmentState snapshot(String shipmentId) {
        return new ShipmentState(warehouseId + "/" + shipmentId, "ready");
    }
    public static void main(String[] args) {
        ShipmentState snapshot = new WarehouseSnapshot("north").snapshot("s-54");
        System.out.println(snapshot.render());
    }
}
