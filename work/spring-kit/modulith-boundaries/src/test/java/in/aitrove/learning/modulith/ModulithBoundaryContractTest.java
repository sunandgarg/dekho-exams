package in.aitrove.learning.modulith;

import in.aitrove.invalidmodules.InvalidReceiptModulesApplication;
import in.aitrove.modules.ReceiptModulesApplication;
import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertThrows;

class ModulithBoundaryContractTest {
    @Test
    void dispatchMayDependOnInventoryRootApi() {
        assertDoesNotThrow(() -> ApplicationModules.of(ReceiptModulesApplication.class).verify());
    }

    @Test
    void dispatchMayNotReachIntoInventoryInternalPackage() {
        assertThrows(RuntimeException.class,
            () -> ApplicationModules.of(InvalidReceiptModulesApplication.class).verify());
    }
}
