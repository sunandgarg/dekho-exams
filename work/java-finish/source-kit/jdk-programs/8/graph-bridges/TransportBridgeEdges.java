import java.util.*;
public class TransportBridgeEdges {
    static class Edge {final int target,id;Edge(int target,int id){this.target=target;this.id=id;}}
    static void visit(int vertex,int parentEdge,List<List<Edge>> graph,int[] discovered,int[] low,int[] clock,List<Integer> bridges) {
        discovered[vertex]=low[vertex]=++clock[0];
        for(Edge edge:graph.get(vertex)) {
            if(edge.id==parentEdge)continue;
            if(discovered[edge.target]==0) {
                visit(edge.target,edge.id,graph,discovered,low,clock,bridges);
                low[vertex]=Math.min(low[vertex],low[edge.target]);
                if(low[edge.target]>discovered[vertex])bridges.add(edge.id);
            } else low[vertex]=Math.min(low[vertex],discovered[edge.target]);
        }
    }
    static List<Integer> bridges(int vertices,int[][] links) {
        if(vertices<1 || vertices>500 || links.length>5000)throw new IllegalArgumentException("graph bounds");
        List<List<Edge>> graph=new ArrayList<>();for(int i=0;i<vertices;i++)graph.add(new ArrayList<>());
        for(int id=0;id<links.length;id++) {
            int[] edge=links[id];if(edge.length!=2 || edge[0]<0 || edge[0]>=vertices || edge[1]<0 || edge[1]>=vertices)throw new IllegalArgumentException("endpoint");
            graph.get(edge[0]).add(new Edge(edge[1],id));graph.get(edge[1]).add(new Edge(edge[0],id));
        }
        List<Integer> critical=new ArrayList<>();int[] discovered=new int[vertices],low=new int[vertices],clock={0};
        for(int vertex=0;vertex<vertices;vertex++)if(discovered[vertex]==0)visit(vertex,-1,graph,discovered,low,clock,critical);
        Collections.sort(critical);return critical;
    }
    public static void main(String[] args) {
        System.out.println(bridges(4,new int[][]{{0,1},{1,2},{2,0},{1,3}}));
        System.out.println(bridges(2,new int[][]{{0,1},{0,1}}));
    }
}
