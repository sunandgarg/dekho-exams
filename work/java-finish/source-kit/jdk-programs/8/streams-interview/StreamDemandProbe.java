import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;
public class StreamDemandProbe {
    public static void main(String[] args){
        AtomicInteger inspected=new AtomicInteger();
        Stream<Integer> selected=Arrays.asList(3,7,7).stream()
            .map(quantity->{inspected.incrementAndGet();return quantity;}).filter(quantity->quantity>4);
        System.out.println(inspected.get());
        System.out.println(selected.collect(Collectors.toList()));
        System.out.println(inspected.get());
        try{selected.count();}catch(IllegalStateException consumed){System.out.println("Stream already consumed");}
    }
}
