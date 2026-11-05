package in.aitrove.contracts;
import java.util.ArrayList;
import java.util.List;
import org.springframework.transaction.event.*;
public class CommitEvents {
    public record ImportedReceipt(int id) {}
    public final List<Integer> committed=new ArrayList<>();
    @TransactionalEventListener(phase=TransactionPhase.AFTER_COMMIT)
    public void committed(ImportedReceipt event) { committed.add(event.id()); }
}
