package in.aitrove.invalidmodules.inventory.internal;

public final class UnsafeStockStore {
    public int availableUnits(String receiptId) { return receiptId.equals("RC-47") ? 19 : 0; }
}
