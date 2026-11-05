package in.aitrove.contracts;
import java.util.*;
import org.springframework.data.jpa.repository.JpaRepository;
public interface StockRepository extends JpaRepository<JpaContracts.StockAccount,Long> {
    List<JpaContracts.StockAccount> findByAvailableGreaterThanOrderByIdAsc(int minimum);
    interface StockSummary {Long getId();int getAvailable();}
    List<StockSummary> findSummaryByAvailableGreaterThanOrderByIdAsc(int minimum);
    List<StockSummary> findTop2ByIdGreaterThanOrderByIdAsc(long afterId);
}
