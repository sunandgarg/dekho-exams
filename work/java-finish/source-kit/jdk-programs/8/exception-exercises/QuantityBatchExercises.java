import java.util.*;
public class QuantityBatchExercises {
    static List<Integer> parse(String[] lines){
        List<Integer> accepted=new ArrayList<>();
        for(String line:lines){
            if(line==null)throw new IllegalArgumentException("Missing quantity");
            int quantity=Integer.parseInt(line);
            if(quantity<=0)throw new IllegalArgumentException("Positive quantity required");
            accepted.add(quantity);
        }
        return Collections.unmodifiableList(accepted);
    }
    static void rejected(String[] lines){
        try{parse(lines);throw new AssertionError("Invalid batch accepted");}
        catch(IllegalArgumentException expected){ }
    }
    public static void main(String[] args){
        if(!parse(new String[]{"3","7"}).equals(Arrays.asList(3,7)))throw new AssertionError("Wrong order");
        rejected(new String[]{"3","bad"});rejected(new String[]{"0"});rejected(new String[]{null});
        System.out.println("4 parsing checks passed");
    }
}
