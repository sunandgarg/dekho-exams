package in.aitrove.contracts;
import reactor.core.publisher.Flux;
import java.util.concurrent.atomic.AtomicBoolean;
public class ReactiveReceiptDemand {
    public static Flux<Integer> records(AtomicBoolean cancelled) {
        return Flux.range(1,5).doOnCancel(() -> cancelled.set(true));
    }
}
