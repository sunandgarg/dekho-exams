public class MatrixPlanCost {
    static long minimum(int[] dimensions) {
        if(dimensions.length<2 || dimensions.length>11)throw new IllegalArgumentException("chain size");
        for(int dimension:dimensions)if(dimension<1 || dimension>1000)throw new IllegalArgumentException("dimension");
        int count=dimensions.length-1;long[][] cost=new long[count][count];
        for(int length=2;length<=count;length++)for(int left=0;left+length<=count;left++) {
            int right=left+length-1;cost[left][right]=Long.MAX_VALUE;
            for(int split=left;split<right;split++) {
                long candidate=cost[left][split]+cost[split+1][right]
                    +(long)dimensions[left]*dimensions[split+1]*dimensions[right+1];
                cost[left][right]=Math.min(cost[left][right],candidate);
            }
        }
        return cost[0][count-1];
    }
    public static void main(String[] args) {
        System.out.println(minimum(new int[]{10,20,30,40}));System.out.println(minimum(new int[]{10,20}));
        try{minimum(new int[]{10,0,20});}catch(IllegalArgumentException rejected){System.out.println("dimension rejected");}
    }
}
