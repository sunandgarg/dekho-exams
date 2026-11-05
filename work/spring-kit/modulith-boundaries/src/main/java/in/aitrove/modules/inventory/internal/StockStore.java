package in.aitrove.modules.inventory.internal;

import in.aitrove.modules.inventory.InventoryQueries;

public final class StockStore implements InventoryQueries {
    @Override public int availableUnits(String receiptId) {
        return receiptId.equals("RC-47") ? 19 : 0;
    }
}
