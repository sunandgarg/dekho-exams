package in.aitrove.invalidmodules.dispatch;

import in.aitrove.invalidmodules.inventory.internal.UnsafeStockStore;

public final class UnsafeDispatchPlanner {
    private final UnsafeStockStore store = new UnsafeStockStore();
    public boolean canDispatch(String receiptId, int units) {
        return units > 0 && store.availableUnits(receiptId) >= units;
    }
}
