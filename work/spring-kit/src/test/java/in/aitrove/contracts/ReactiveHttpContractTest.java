package in.aitrove.contracts;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.http.MediaType;
import reactor.test.StepVerifier;
import java.time.Duration;
public class ReactiveHttpContractTest {
    WebTestClient client(ReactiveReceiptController controller){return WebTestClient.bindToController(controller).build();}
    @Test void emitsOrderedSseEventsAndCompletes(){
        var result=client(new ReactiveReceiptController()).get().uri("/contract/events?count=3").exchange()
            .expectStatus().isOk().expectHeader().contentTypeCompatibleWith(MediaType.TEXT_EVENT_STREAM)
            .returnResult(new ParameterizedTypeReference<ServerSentEvent<String>>(){});
        StepVerifier.create(result.getResponseBody()).expectNextMatches(event->event.id().equals("1")&&event.data().equals("R1"))
            .expectNextMatches(event->event.id().equals("2")&&event.data().equals("R2"))
            .expectNextMatches(event->event.id().equals("3")&&event.data().equals("R3"))
            .expectComplete().verify(Duration.ofSeconds(3));
    }
    @Test void rejectsCountBeforeSuccessfulStreamHeaders(){client(new ReactiveReceiptController()).get().uri("/contract/events?count=0").exchange().expectStatus().isBadRequest();}
    @Test void downstreamCancellationReachesTheControllerSequence(){
        var controller=new ReactiveReceiptController();
        var result=client(controller).get().uri("/contract/events?count=5").exchange().expectStatus().isOk()
            .returnResult(new ParameterizedTypeReference<ServerSentEvent<String>>(){});
        StepVerifier.create(result.getResponseBody()).expectNextCount(1).thenCancel().verify(Duration.ofSeconds(3));
        assertTrue(controller.cancelled.get());
    }
}
