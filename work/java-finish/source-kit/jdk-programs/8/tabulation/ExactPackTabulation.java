import java.util.Arrays;
public class ExactPackTabulation {
    static int minimum(int quantity,int[] packs){
        if(quantity<0||quantity>1_000_000)throw new IllegalArgumentException("Quantity outside budget");
        for(int pack:packs)if(pack<=0)throw new IllegalArgumentException("Positive packs required");
        int absent=quantity+1;int[] best=new int[quantity+1];Arrays.fill(best,absent);best[0]=0;
        for(int amount=1;amount<=quantity;amount++)
            for(int pack:packs)if(pack<=amount&&best[amount-pack]!=absent)best[amount]=Math.min(best[amount],best[amount-pack]+1);
        return best[quantity]==absent?-1:best[quantity];
    }
    public static void main(String[] args){
        int[] packs={3,5};System.out.println(minimum(9,packs));
        System.out.println(minimum(7,packs));System.out.println(minimum(0,packs));
    }
}
