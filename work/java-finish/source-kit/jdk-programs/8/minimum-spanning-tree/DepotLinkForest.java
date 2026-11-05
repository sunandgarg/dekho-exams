import java.util.Arrays;
import java.util.Comparator;
public class DepotLinkForest {
    static final class Edge {
        final int from,to,cost;
        Edge(int from,int to,int cost){this.from=from;this.to=to;this.cost=cost;}
    }
    static final class Result { final long cost; final int components;
        Result(long cost,int components){this.cost=cost;this.components=components;} }
    static int root(int[] parent,int vertex){
        while(parent[vertex]!=vertex){parent[vertex]=parent[parent[vertex]];vertex=parent[vertex];}
        return vertex;
    }
    static Result connect(int vertices,Edge[] input){
        if(vertices<0)throw new IllegalArgumentException("Negative vertices");
        for(Edge edge:input)if(edge.from<0||edge.to<0||edge.from>=vertices||edge.to>=vertices)throw new IllegalArgumentException("Invalid endpoint");
        Edge[] edges=input.clone();Arrays.sort(edges,Comparator.comparingInt(edge->edge.cost));
        int[] parent=new int[vertices],sizes=new int[vertices];
        for(int v=0;v<vertices;v++){parent[v]=v;sizes[v]=1;}
        long cost=0;int components=vertices;
        for(Edge edge:edges){
            int a=root(parent,edge.from),b=root(parent,edge.to);if(a==b)continue;
            if(sizes[a]<sizes[b]){int temporary=a;a=b;b=temporary;}
            parent[b]=a;sizes[a]+=sizes[b];cost=Math.addExact(cost,edge.cost);components--;
        }
        return new Result(cost,components);
    }
    public static void main(String[] args){
        Result result=connect(4,new Edge[]{new Edge(0,1,4),new Edge(1,2,2),new Edge(2,3,3),new Edge(0,3,10)});
        System.out.println("cost="+result.cost+", components="+result.components);
        Result forest=connect(3,new Edge[]{new Edge(0,1,-2)});
        System.out.println("cost="+forest.cost+", components="+forest.components);
    }
}
