package in.aitrove.contracts;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class NestedReceiptValidationTest {
    static class ReceiptLine {
        @NotBlank public String sku;
        @Positive public int quantity;
    }
    static class ReceiptImport {
        @NotBlank public String receiptId;
        @Valid public ReceiptLine line;
    }
    @RestController
    static class ReceiptImportController {
        @PostMapping(path = "/contract/validated-imports", consumes = MediaType.APPLICATION_JSON_VALUE)
        String accept(@Valid @RequestBody ReceiptImport request) {
            return request.receiptId;
        }
    }

    @Test void rejectsInvalidNestedFieldsBeforeCallingTheHandler() throws Exception {
        try (var validator = new LocalValidatorFactoryBean()) {
            validator.afterPropertiesSet();
            var client = MockMvcBuilders.standaloneSetup(new ReceiptImportController())
                .setValidator(validator).build();
            client.perform(post("/contract/validated-imports")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("{\"receiptId\":\"R-41\",\"line\":{\"sku\":\"A-7\",\"quantity\":2}}"))
                .andExpect(status().isOk());
            client.perform(post("/contract/validated-imports")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("{\"receiptId\":\"R-41\",\"line\":{\"sku\":\"A-7\",\"quantity\":0}}"))
                .andExpect(status().isBadRequest());
            client.perform(post("/contract/validated-imports")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("{\"receiptId\":\" \",\"line\":{\"sku\":\"A-7\",\"quantity\":2}}"))
                .andExpect(status().isBadRequest());
        }
    }
}
