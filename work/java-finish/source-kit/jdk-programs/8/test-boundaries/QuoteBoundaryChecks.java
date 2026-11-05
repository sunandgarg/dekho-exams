import java.io.IOException;
public class QuoteBoundaryChecks {
    interface Gateway{int amount(String destination)throws IOException;}
    static int total(String destination,Gateway gateway)throws IOException{
        if(destination==null||destination.trim().isEmpty())throw new IllegalArgumentException("Missing destination");
        int base=gateway.amount(destination);
        if(base<0)throw new IllegalArgumentException("Negative quote");
        return Math.addExact(base,10);
    }
    public static void main(String[] args)throws Exception{
        if(total("Delhi",destination->90)!=100)throw new AssertionError("Fee changed");
        try{total("",destination->{throw new AssertionError("Invalid request called gateway");});throw new AssertionError("Missing destination accepted");}
        catch(IllegalArgumentException expected){ }
        try{total("Delhi",destination->{throw new IOException("Supplier unavailable");});throw new AssertionError("Failure hidden");}
        catch(IOException expected){ }
        try{total("Delhi",destination->-1);throw new AssertionError("Negative quote accepted");}
        catch(IllegalArgumentException expected){ }
        System.out.println("4 gateway checks passed");
    }
}
