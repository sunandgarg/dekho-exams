package in.aitrove.modules.dispatch;

import in.aitrove.modules.inventory.InventoryQueries;
import org.springframework.stereotype.Component;

@Component
public final class DispatchPlanner {
    private final InventoryQueries inventory;
    public DispatchPlanner(InventoryQueries inventory) { this.inventory = inventory; }
    public boolean canDispatch(String receiptId, int units) {
        return units > 0 && inventory.availableUnits(receiptId) >= units;
    }
}
