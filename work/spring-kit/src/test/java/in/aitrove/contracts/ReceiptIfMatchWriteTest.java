package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class ReceiptIfMatchWriteTest {
    @RestController
    static class ReceiptRevisionController {
        private int version = 1;
        private String state = "received";

        @GetMapping("/contract/revisions/{id}")
        synchronized ResponseEntity<String> read(@PathVariable int id) {
            if (id != 7) return ResponseEntity.notFound().build();
            return ResponseEntity.ok().eTag("receipt-7-v" + version).body(state);
        }

        @PutMapping(path = "/contract/revisions/{id}", consumes = MediaType.TEXT_PLAIN_VALUE)
        synchronized ResponseEntity<String> update(@PathVariable int id,
            @RequestHeader(value = "If-Match", required = false) String expected,
            @RequestBody String nextState) {
            if (id != 7) return ResponseEntity.notFound().build();
            if (expected == null) return ResponseEntity.status(HttpStatus.PRECONDITION_REQUIRED).build();
            String current = "\"receipt-7-v" + version + "\"";
            if (!current.equals(expected))
                return ResponseEntity.status(HttpStatus.PRECONDITION_FAILED).eTag(current).build();
            state = nextState;
            version++;
            return ResponseEntity.ok().eTag("receipt-7-v" + version).body(state);
        }
    }

    @Test void staleClientCannotOverwriteTheCurrentRevision() throws Exception {
        var client = MockMvcBuilders.standaloneSetup(new ReceiptRevisionController()).build();
        client.perform(get("/contract/revisions/7"))
            .andExpect(status().isOk())
            .andExpect(header().string("ETag", "\"receipt-7-v1\""));
        client.perform(put("/contract/revisions/7").contentType(MediaType.TEXT_PLAIN).content("reviewed"))
            .andExpect(status().isPreconditionRequired());
        client.perform(put("/contract/revisions/7").contentType(MediaType.TEXT_PLAIN)
                .header("If-Match", "\"receipt-7-v0\"").content("reviewed"))
            .andExpect(status().isPreconditionFailed());
        client.perform(put("/contract/revisions/7").contentType(MediaType.TEXT_PLAIN)
                .header("If-Match", "\"receipt-7-v1\"").content("reviewed"))
            .andExpect(status().isOk())
            .andExpect(header().string("ETag", "\"receipt-7-v2\""));
        client.perform(put("/contract/revisions/7").contentType(MediaType.TEXT_PLAIN)
                .header("If-Match", "\"receipt-7-v1\"").content("overwritten"))
            .andExpect(status().isPreconditionFailed());
        client.perform(get("/contract/revisions/7"))
            .andExpect(content().string("reviewed"));
    }
}
