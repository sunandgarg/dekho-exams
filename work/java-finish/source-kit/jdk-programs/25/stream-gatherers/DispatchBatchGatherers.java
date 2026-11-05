import java.util.List;
import java.util.stream.Gatherers;
public class DispatchBatchGatherers {
    public static void main(String[] args){
        List<Integer> counts=List.of(4,7,2,9,3);
        System.out.println(counts.stream().gather(Gatherers.windowFixed(2)).toList());
        System.out.println(counts.stream().gather(Gatherers.scan(()->0,Math::addExact)).toList());
        System.out.println(List.<Integer>of().stream().gather(Gatherers.windowFixed(2)).count());
    }
}
