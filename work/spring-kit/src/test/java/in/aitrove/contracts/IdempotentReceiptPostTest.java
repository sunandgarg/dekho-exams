package in.aitrove.contracts;

import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class IdempotentReceiptPostTest {
    @RestController
    static class ReceiptIntake {
        private record Stored(String request, String receipt) {}
        private final Map<String, Stored> accepted = new HashMap<>();

        @PostMapping(path = "/contract/idempotent-receipts", consumes = MediaType.TEXT_PLAIN_VALUE)
        synchronized ResponseEntity<String> create(
            @RequestHeader(value = "Idempotency-Key", required = false) String key,
            @RequestBody String request) {
            if (key == null || key.isBlank()) return ResponseEntity.badRequest().build();
            Stored prior = accepted.get(key);
            if (prior != null) {
                if (!prior.request().equals(request)) return ResponseEntity.status(409).build();
                return ResponseEntity.ok(prior.receipt());
            }
            String receipt = "receipt-" + (accepted.size() + 1);
            accepted.put(key, new Stored(request, receipt));
            return ResponseEntity.ok(receipt);
        }
    }

    @Test void replayReturnsTheOriginalReceiptAndConflictingPayloadIsRejected() throws Exception {
        var client = MockMvcBuilders.standaloneSetup(new ReceiptIntake()).build();
        client.perform(post("/contract/idempotent-receipts").contentType(MediaType.TEXT_PLAIN).content("42"))
            .andExpect(status().isBadRequest());
        client.perform(post("/contract/idempotent-receipts").contentType(MediaType.TEXT_PLAIN)
                .header("Idempotency-Key", "intake-41").content("42"))
            .andExpect(status().isOk()).andExpect(content().string("receipt-1"));
        client.perform(post("/contract/idempotent-receipts").contentType(MediaType.TEXT_PLAIN)
                .header("Idempotency-Key", "intake-41").content("42"))
            .andExpect(status().isOk()).andExpect(content().string("receipt-1"));
        client.perform(post("/contract/idempotent-receipts").contentType(MediaType.TEXT_PLAIN)
                .header("Idempotency-Key", "intake-41").content("99"))
            .andExpect(status().isConflict());
        client.perform(post("/contract/idempotent-receipts").contentType(MediaType.TEXT_PLAIN)
                .header("Idempotency-Key", "intake-42").content("99"))
            .andExpect(status().isOk()).andExpect(content().string("receipt-2"));
    }
}
