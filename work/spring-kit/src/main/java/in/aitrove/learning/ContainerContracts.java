package in.aitrove.learning;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.context.PayloadApplicationEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.aop.framework.ProxyFactory;
import org.aopalliance.intercept.MethodInterceptor;
public class ContainerContracts {
    public interface Exporter { String format(); }
    public static class CsvExporter implements Exporter { public String format() { return "csv"; } }
    public static class ReceiptReport {
        private final Exporter exporter;
        public ReceiptReport(Exporter exporter) { this.exporter = exporter; }
        public String render() { return exporter.format() + ":receipt"; }
    }
    public static class ImportBuffer { private final int capacity = 32; public int capacity() { return capacity; } }
    public static class ClosingChannel implements DisposableBean {
        public boolean closed; public void destroy() { closed = true; }
    }
    public interface Counter { void outer(); void inner(); }
    public static class CounterTarget implements Counter {
        public void outer() { inner(); }
        public void inner() {}
    }
    public static void main(String[] args) {
        ClosingChannel channel;
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext()) {
            context.registerBean("csv", Exporter.class, CsvExporter::new);
            context.registerBean(ReceiptReport.class);
            context.registerBean(ImportBuffer.class, ImportBuffer::new,
                definition -> definition.setScope(BeanDefinition.SCOPE_PROTOTYPE));
            context.registerBean(ClosingChannel.class); context.refresh();
            channel = context.getBean(ClosingChannel.class);
            System.out.println(context.getBean(ReceiptReport.class).render());
            ObjectProvider<ImportBuffer> buffers = context.getBeanProvider(ImportBuffer.class);
            System.out.println("different=" + (buffers.getObject() != buffers.getObject()));
            AtomicInteger messages = new AtomicInteger();
            context.addApplicationListener((ApplicationListener<PayloadApplicationEvent<String>>) event -> messages.incrementAndGet());
            context.publishEvent("receipt-created");
            System.out.println("events=" + messages.get());
        }
        System.out.println("closed=" + channel.closed);
        AtomicInteger advised = new AtomicInteger();
        ProxyFactory factory = new ProxyFactory(new CounterTarget());
        factory.addAdvice((MethodInterceptor) invocation -> { advised.incrementAndGet(); return invocation.proceed(); });
        Counter proxy = (Counter) factory.getProxy(); proxy.outer();
        System.out.println("advised=" + advised.get());
    }
}
