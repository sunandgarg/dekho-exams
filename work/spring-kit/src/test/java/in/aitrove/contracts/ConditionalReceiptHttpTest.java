package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.http.CacheControl;
import org.springframework.http.ResponseEntity;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class ConditionalReceiptHttpTest {
    @RestController
    static class ReceiptVersionController {
        @GetMapping("/contract/receipts/{id}")
        ResponseEntity<String> read(@PathVariable int id) {
            if (id != 7) return ResponseEntity.notFound().build();
            return ResponseEntity.ok()
                .cacheControl(CacheControl.noCache())
                .eTag("receipt-7-v3")
                .body("receipt:7:reviewed");
        }
    }
    @Test void returnsA304OnlyForTheMatchingRepresentationTag() throws Exception {
        var client = MockMvcBuilders.standaloneSetup(new ReceiptVersionController()).build();
        client.perform(get("/contract/receipts/7"))
            .andExpect(status().isOk())
            .andExpect(header().string("ETag", "\"receipt-7-v3\""))
            .andExpect(content().string("receipt:7:reviewed"));
        client.perform(get("/contract/receipts/7").header("If-None-Match", "\"receipt-7-v3\""))
            .andExpect(status().isNotModified())
            .andExpect(content().string(""));
        client.perform(get("/contract/receipts/7").header("If-None-Match", "\"receipt-7-v2\""))
            .andExpect(status().isOk())
            .andExpect(content().string("receipt:7:reviewed"));
        client.perform(get("/contract/receipts/8"))
            .andExpect(status().isNotFound());
    }
}
