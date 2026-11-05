public class BagSubsetOracle {
    static long maximum(int capacity,int[] weights,long[] values){
        if(capacity<0||weights.length!=values.length||weights.length>20)throw new IllegalArgumentException("Oracle budget");
        for(int i=0;i<weights.length;i++)if(weights[i]<=0||values[i]<0)throw new IllegalArgumentException("Item contract");
        long best=0;
        for(int mask=0;mask<(1<<weights.length);mask++){
            long weight=0,value=0;for(int i=0;i<weights.length;i++)if((mask&(1<<i))!=0){weight=Math.addExact(weight,weights[i]);value=Math.addExact(value,values[i]);}
            if(weight<=capacity)best=Math.max(best,value);
        }return best;
    }
    public static void main(String[] args){
        if(maximum(7,new int[]{3,4},new long[]{8,10})!=18)throw new AssertionError("Exact pair");
        if(maximum(2,new int[]{3},new long[]{8})!=0)throw new AssertionError("Heavy item");
        if(maximum(6,new int[]{3},new long[]{8})!=8)throw new AssertionError("Repeated item");System.out.println("checks=3");
    }
}
