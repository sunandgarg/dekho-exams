package in.aitrove.contracts;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicBoolean;
import org.springframework.http.*;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import reactor.core.publisher.Flux;
@RestController
public class ReactiveReceiptController {
    public final AtomicBoolean cancelled=new AtomicBoolean();
    @GetMapping(value="/contract/events",produces=MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> events(@RequestParam(defaultValue="3") int count) {
        if(count<1 || count>5)throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"count must be 1..5");
        return Flux.range(1,count).delayElements(Duration.ofMillis(10))
            .map(index->ServerSentEvent.<String>builder("R"+index).id(Integer.toString(index)).event("receipt").build())
            .doOnCancel(()->cancelled.set(true));
    }
}
