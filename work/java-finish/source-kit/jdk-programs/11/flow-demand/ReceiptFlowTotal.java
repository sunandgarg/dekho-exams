import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class ReceiptFlowTotal {
    public static void main(String[] args) {
        AtomicInteger total=new AtomicInteger();
        CompletableFuture<Void> finished=new CompletableFuture<>();
        try(SubmissionPublisher<Integer> publisher=new SubmissionPublisher<>(Runnable::run,8)) {
            publisher.subscribe(new Flow.Subscriber<Integer>() {
                Flow.Subscription subscription;
                public void onSubscribe(Flow.Subscription value){subscription=value;subscription.request(1);}
                public void onNext(Integer amount){total.addAndGet(amount);subscription.request(1);}
                public void onError(Throwable failure){finished.completeExceptionally(failure);}
                public void onComplete(){finished.complete(null);}
            });
            publisher.submit(10);publisher.submit(20);
        }
        finished.join();System.out.println(total.get());
    }
}
