package in.aitrove.contracts;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ProblemDetail;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MvcProblemAdviceTest {
    @RestControllerAdvice
    static class ValidationAdvice {
        @ExceptionHandler({MethodArgumentNotValidException.class, HandlerMethodValidationException.class})
        ProblemDetail invalidRequest(Exception rejected) {
            ProblemDetail problem = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
            problem.setTitle("Invalid receipt request");
            problem.setDetail("Check the submitted fields and limits.");
            return problem;
        }
    }

    @Test void twoValidationPathsReturnOnePublicErrorShape() throws Exception {
        var validator = new LocalValidatorFactoryBean();
        validator.afterPropertiesSet();
        try {
            var client = MockMvcBuilders.standaloneSetup(new MvcValidationModesTest.ReceiptController())
                .setControllerAdvice(new ValidationAdvice()).setValidator(validator).build();
            client.perform(post("/contract/validated-receipts").contentType(MediaType.APPLICATION_JSON)
                    .content("{\"note\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid receipt request"));
            client.perform(get("/contract/receipt-limit").param("count", "0"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid receipt request"));
        } finally {
            validator.close();
        }
    }
}
