package in.aitrove.learning;
import java.util.List;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Positive;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/receipts")
public class ReceiptController {
    public record CreateReceipt(@Positive int amountMinor) {}
    private final ReceiptStore store;
    public ReceiptController(ReceiptStore store) { this.store = store; }
    @PostMapping @ResponseStatus(HttpStatus.CREATED)
    public ReceiptStore.Receipt create(@Valid @RequestBody CreateReceipt command) { return store.create(command.amountMinor()); }
    @GetMapping("/{id}") public ReceiptStore.Receipt find(@PathVariable long id) {
        return store.find(id).orElseThrow(() -> new MissingReceipt(id));
    }
    @GetMapping public List<ReceiptStore.Receipt> page(@RequestParam(defaultValue="0") int offset,
        @RequestParam(defaultValue="20") int limit) { return store.page(offset, limit); }
    public static class MissingReceipt extends RuntimeException {
        MissingReceipt(long id) { super("Receipt " + id + " was not found"); }
    }
}
