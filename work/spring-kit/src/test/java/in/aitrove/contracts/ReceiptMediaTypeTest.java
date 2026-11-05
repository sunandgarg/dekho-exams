package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class ReceiptMediaTypeTest {
    @RestController
    static class ReceiptImportController {
        @PostMapping(path = "/contract/imports", consumes = MediaType.APPLICATION_JSON_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE)
        String importReceipt(@RequestBody String request) {
            return "{\"accepted\":true}";
        }
    }

    @Test void separatesRequestTypeFromAcceptableResponseType() throws Exception {
        var client = MockMvcBuilders.standaloneSetup(new ReceiptImportController()).build();
        client.perform(post("/contract/imports")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .content("{\"receiptId\":\"R-41\"}"))
            .andExpect(status().isOk())
            .andExpect(content().json("{\"accepted\":true}"));
        client.perform(post("/contract/imports")
                .contentType(MediaType.TEXT_PLAIN)
                .accept(MediaType.APPLICATION_JSON)
                .content("R-41"))
            .andExpect(status().isUnsupportedMediaType());
        client.perform(post("/contract/imports")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.TEXT_PLAIN)
                .content("{\"receiptId\":\"R-41\"}"))
            .andExpect(status().isNotAcceptable());
    }
}
