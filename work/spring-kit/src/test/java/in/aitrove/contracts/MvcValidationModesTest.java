package in.aitrove.contracts;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MvcValidationModesTest {
    record ReceiptCommand(@NotBlank String note) {}

    @RestController
    static class ReceiptController {
        @PostMapping(path = "/contract/validated-receipts", consumes = MediaType.APPLICATION_JSON_VALUE)
        String create(@Valid @RequestBody ReceiptCommand command) { return command.note(); }

        @GetMapping("/contract/receipt-limit")
        String limit(@RequestParam @Min(1) int count) { return Integer.toString(count); }
    }

    @Test void objectAndDirectParameterConstraintsRejectDifferentInputs() throws Exception {
        var validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();
        try {
            var client = MockMvcBuilders.standaloneSetup(new ReceiptController())
                .setValidator(validator).build();
            client.perform(post("/contract/validated-receipts").contentType(MediaType.APPLICATION_JSON)
                    .content("{\"note\":\"\"}"))
                .andExpect(status().isBadRequest());
            client.perform(post("/contract/validated-receipts").contentType(MediaType.APPLICATION_JSON)
                    .content("{\"note\":\"reviewed\"}"))
                .andExpect(status().isOk()).andExpect(content().string("reviewed"));
            client.perform(get("/contract/receipt-limit").param("count", "0"))
                .andExpect(status().isBadRequest());
            client.perform(get("/contract/receipt-limit").param("count", "2"))
                .andExpect(status().isOk()).andExpect(content().string("2"));
        } finally {
            validator.close();
        }
    }
}
