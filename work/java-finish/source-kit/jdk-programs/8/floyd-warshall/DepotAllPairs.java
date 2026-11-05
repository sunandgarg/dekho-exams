import java.util.Arrays;
public class DepotAllPairs {
    static final long ABSENT=Long.MAX_VALUE;
    static long[][] distances(long[][] input){
        int n=input.length;if(n>200)throw new IllegalArgumentException("Matrix budget");
        long[][] result=new long[n][n];
        for(int i=0;i<n;i++){
            if(input[i]==null||input[i].length!=n)throw new IllegalArgumentException("Square matrix required");
            for(int j=0;j<n;j++){
                long value=input[i][j];if(value!=ABSENT&&(value<-1_000_000||value>1_000_000))throw new IllegalArgumentException("Edge budget");result[i][j]=value;
            }result[i][i]=Math.min(0,result[i][i]);
        }
        for(int via=0;via<n;via++)for(int from=0;from<n;from++)for(int to=0;to<n;to++)
            if(result[from][via]!=ABSENT&&result[via][to]!=ABSENT)result[from][to]=Math.min(result[from][to],Math.addExact(result[from][via],result[via][to]));
        for(int i=0;i<n;i++)if(result[i][i]<0)throw new IllegalStateException("Negative cycle");
        return result;
    }
    public static void main(String[] args){
        long[][] edges={{0,5,ABSENT},{ABSENT,0,-2},{ABSENT,ABSENT,0}};
        System.out.println(Arrays.toString(distances(edges)[0]));System.out.println(edges[0][2]==ABSENT);
    }
}
