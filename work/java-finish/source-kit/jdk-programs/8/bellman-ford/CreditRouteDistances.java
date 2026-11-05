import java.util.Arrays;
public class CreditRouteDistances {
    static final class Edge { final int from,to,weight;
        Edge(int from,int to,int weight){this.from=from;this.to=to;this.weight=weight;} }
    static long[] distances(int vertices,Edge[] edges,int source){
        if(vertices<1||source<0||source>=vertices)throw new IllegalArgumentException("Invalid source");
        for(Edge edge:edges)if(edge.from<0||edge.to<0||edge.from>=vertices||edge.to>=vertices)throw new IllegalArgumentException("Invalid edge");
        long[] result=new long[vertices];Arrays.fill(result,Long.MAX_VALUE);result[source]=0;
        for(int pass=1;pass<vertices;pass++){
            boolean changed=false;
            for(Edge edge:edges)if(result[edge.from]!=Long.MAX_VALUE){
                long candidate=Math.addExact(result[edge.from],edge.weight);
                if(candidate<result[edge.to]){result[edge.to]=candidate;changed=true;}
            }
            if(!changed)break;
        }
        for(Edge edge:edges)if(result[edge.from]!=Long.MAX_VALUE&&Math.addExact(result[edge.from],edge.weight)<result[edge.to])
            throw new IllegalStateException("Reachable negative cycle");
        return result;
    }
    public static void main(String[] args){
        Edge[] valid={new Edge(0,1,4),new Edge(0,2,7),new Edge(1,2,-2),new Edge(2,3,3)};
        System.out.println(Arrays.toString(distances(4,valid,0)));
        Edge[] cycle=Arrays.copyOf(valid,5);cycle[4]=new Edge(3,1,-6);
        try{distances(4,cycle,0);}catch(IllegalStateException rejected){System.out.println(rejected.getMessage());}
    }
}
