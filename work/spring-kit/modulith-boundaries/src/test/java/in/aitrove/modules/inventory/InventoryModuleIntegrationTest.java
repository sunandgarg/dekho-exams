package in.aitrove.modules.inventory;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationContext;
import org.springframework.modulith.test.ApplicationModuleTest;
import org.springframework.modulith.test.PublishedEvents;

import static org.assertj.core.api.Assertions.assertThat;

@ApplicationModuleTest
class InventoryModuleIntegrationTest {
    @Autowired InventoryReservation reservation;
    @Autowired ApplicationContext context;

    @Test
    void acceptedReservationChangesStateAndPublishesOneEvent(PublishedEvents events) {
        assertThat(context.containsBean("dispatchPlanner")).isFalse();
        assertThat(reservation.reserve("RECEIPT-203", 19)).isTrue();
        assertThat(reservation.availableUnits("RECEIPT-203")).isEqualTo(28);
        assertThat(events.ofType(ReceiptReserved.class)
            .matching(ReceiptReserved::receiptId, "RECEIPT-203")).hasSize(1);
    }

    @Test
    void rejectedReservationPublishesNoSuccessEvent(PublishedEvents events) {
        assertThat(reservation.reserve("RECEIPT-211", 59)).isFalse();
        assertThat(reservation.availableUnits("RECEIPT-211")).isEqualTo(47);
        assertThat(events.ofType(ReceiptReserved.class)
            .matching(ReceiptReserved::receiptId, "RECEIPT-211")).isEmpty();
    }
}
