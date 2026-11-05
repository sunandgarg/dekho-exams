public class DispatchBagValue {
    static long maximum(int capacity,int[] weights,long[] values){
        if(capacity<0||capacity>100_000||weights.length!=values.length||(long)capacity*weights.length>5_000_000)throw new IllegalArgumentException("Knapsack budget");
        for(int i=0;i<weights.length;i++)if(weights[i]<=0||values[i]<0)throw new IllegalArgumentException("Item contract");
        long[] best=new long[capacity+1];
        for(int i=0;i<weights.length;i++)for(int available=capacity;available>=weights[i];available--)
            best[available]=Math.max(best[available],Math.addExact(best[available-weights[i]],values[i]));
        return best[capacity];
    }
    public static void main(String[] args){System.out.println(maximum(7,new int[]{3,4,5},new long[]{8,10,12}));System.out.println(maximum(6,new int[]{3},new long[]{8}));System.out.println(maximum(0,new int[]{3},new long[]{8}));}
}
