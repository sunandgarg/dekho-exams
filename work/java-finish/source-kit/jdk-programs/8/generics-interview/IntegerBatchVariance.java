import java.util.*;
public class IntegerBatchVariance {
    static void copy(List<? super Integer> target,List<? extends Integer> source){
        for(Integer amount:source)target.add(amount);
    }
    public static void main(String[] args){
        List<Integer> quantities=new ArrayList<>(Arrays.asList(7,9));
        List<? extends Number> observed=quantities;
        List<Object> exported=new ArrayList<>();copy(exported,quantities);
        System.out.println(exported);
        System.out.println(observed.get(0).intValue());
        System.out.println(quantities.getClass()==new ArrayList<String>().getClass());
    }
}
