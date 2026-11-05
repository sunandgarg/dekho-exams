package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.boot.context.annotation.ImportCandidates;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.*;
public class AutoConfigurationContractTest {
    ApplicationContextRunner runner(){return new ApplicationContextRunner().withConfiguration(AutoConfigurations.of(ReceiptLabelAutoConfiguration.class));}
    @Test void defaultBeanRendersLabel(){runner().run(context->assertEquals("Receipt:7",context.getBean(ReceiptLabelAutoConfiguration.ReceiptLabel.class).render(7)));}
    @Configuration static class UserLabel {
        @Bean ReceiptLabelAutoConfiguration.ReceiptLabel label(){return new ReceiptLabelAutoConfiguration.ReceiptLabel("Invoice");}
    }
    @Test void userBeanMakesDefaultBackOff(){runner().withUserConfiguration(UserLabel.class).run(context->{
        assertEquals(1,context.getBeansOfType(ReceiptLabelAutoConfiguration.ReceiptLabel.class).size());
        assertEquals("Invoice:7",context.getBean(ReceiptLabelAutoConfiguration.ReceiptLabel.class).render(7));});}
    @Test void importsResourceRegistersTheConfiguration(){assertTrue(ImportCandidates.load(AutoConfiguration.class,getClass().getClassLoader()).getCandidates().contains(ReceiptLabelAutoConfiguration.class.getName()));}
}
