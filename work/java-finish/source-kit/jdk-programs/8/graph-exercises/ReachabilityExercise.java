public class ReachabilityExercise {
    static boolean[][] closure(int[][] edges){
        int n=edges.length;if(n>100)throw new IllegalArgumentException("Exercise graph budget");boolean[][] reachable=new boolean[n][n];
        for(int i=0;i<n;i++){reachable[i][i]=true;if(edges[i]==null)throw new IllegalArgumentException("Missing adjacency");for(int to:edges[i]){if(to<0||to>=n)throw new IllegalArgumentException("Endpoint");reachable[i][to]=true;}}
        for(int via=0;via<n;via++)for(int from=0;from<n;from++)for(int to=0;to<n;to++)reachable[from][to]|=reachable[from][via]&&reachable[via][to];return reachable;
    }
    static void require(boolean expected){if(!expected)throw new AssertionError("Reachability exercise");}
    public static void main(String[] args){
        boolean[][] r=closure(new int[][]{{1},{0,2},{},{}});
        require(r[0][1]&&r[1][0]);require(r[0][2]&&!r[2][0]);require(r[3][3]&&!r[3][0]);System.out.println("checks=3");
    }
}
