package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;
public class RepositoryQueryTest {
    @Test void derivedPredicateUsesMappedPropertyAndOrder() {
        try(var kit=new RepositoryContracts()) {
            kit.transaction.executeWithoutResult(status->kit.stocks.findById(2L).orElseThrow().available=30);
            assertEquals(List.of(1L,3L),kit.stocks.findByAvailableGreaterThanOrderByIdAsc(50).stream().map(account->account.id).toList());
            assertTrue(kit.stocks.findByAvailableGreaterThanOrderByIdAsc(100).isEmpty());
        }
    }
    @Test void projectionReadsValuesWithoutCreatingAFullEntity() {
        try(var kit=new RepositoryContracts()) {
            kit.data.statistics().clear();
            var summaries=kit.stocks.findSummaryByAvailableGreaterThanOrderByIdAsc(50);
            assertEquals(3,summaries.size());assertEquals(100,summaries.get(0).getAvailable());assertEquals(1L,summaries.get(0).getId());
            assertEquals(0,kit.data.statistics().getEntityLoadCount());
            assertEquals(1,kit.data.statistics().getPrepareStatementCount());
        }
    }
    @Test void cursorKeepsIdOrderAndMovesPastThePreviousLastId() {
        try(var kit=new RepositoryContracts()) {
            var first=kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(0);
            assertEquals(List.of(1L,2L),first.stream().map(StockRepository.StockSummary::getId).toList());
            var next=kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(2);
            assertEquals(List.of(3L),next.stream().map(StockRepository.StockSummary::getId).toList());
            assertTrue(kit.stocks.findTop2ByIdGreaterThanOrderByIdAsc(3).isEmpty());
        }
    }
}
