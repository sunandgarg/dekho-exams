package in.aitrove.learning;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
public class ReceiptBoundaryTest {
    MockMvc mvc() {
        var validator = new LocalValidatorFactoryBean(); validator.afterPropertiesSet();
        return MockMvcBuilders.standaloneSetup(new ReceiptController(new ReceiptStore()))
            .setControllerAdvice(new ReceiptErrors()).setValidator(validator).build();
    }
    @Test void createsValidReceipt() throws Exception { mvc().perform(post("/api/receipts").contentType("application/json").content("{\"amountMinor\":125}"))
        .andExpect(status().isCreated()).andExpect(jsonPath("$.amountMinor").value(125)); }
    @Test void rejectsZeroAmount() throws Exception { mvc().perform(post("/api/receipts").contentType("application/json").content("{\"amountMinor\":0}"))
        .andExpect(status().isBadRequest()).andExpect(jsonPath("$.detail").value("Receipt input is invalid")); }
    @Test void missingReceiptUsesProblemDetail() throws Exception { mvc().perform(get("/api/receipts/999"))
        .andExpect(status().isNotFound()).andExpect(content().contentTypeCompatibleWith("application/problem+json")); }
    @Test void rejectsPageSizeBeyondLimit() throws Exception { mvc().perform(get("/api/receipts").param("limit", "101")).andExpect(status().isBadRequest()); }
    @Test void emptyPageOutsideRangeIsEmpty() { var store = new ReceiptStore(); store.create(10); assertTrue(store.page(40, 20).isEmpty()); }
    @Test void returnedPageCannotMutateStore() { var store = new ReceiptStore(); store.create(10); assertThrows(UnsupportedOperationException.class, () -> store.page(0,20).clear()); }
    @Test void databaseFailureRollsBackWholeBatch() { var ledger = new JdbcReceiptLedger(); assertThrows(DataIntegrityViolationException.class, ledger::batchThatFails); assertEquals(0, ledger.count()); }
    @Test void rollbackOnlyDoesNotCommit() { var ledger = new JdbcReceiptLedger(); ledger.rollbackOnly(); assertEquals(0, ledger.count()); }
    @Test void boundInsertCommitsAndDuplicateIsRejected() { var ledger = new JdbcReceiptLedger(); ledger.add(9, 40); assertThrows(DataIntegrityViolationException.class, () -> ledger.add(9,50)); assertEquals(1, ledger.count()); }
}
