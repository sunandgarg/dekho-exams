import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
public class StatusGroupingReference {
    public static void main(String[] args){
        Map<String,Long> counts=Arrays.asList("paid","pending","paid").stream()
            .collect(Collectors.toMap(Function.identity(),status->1L,Long::sum,LinkedHashMap::new));
        System.out.println(counts);
        System.out.println(Collections.<Integer>emptyList().stream().max(Integer::compare).isPresent());
    }
}
