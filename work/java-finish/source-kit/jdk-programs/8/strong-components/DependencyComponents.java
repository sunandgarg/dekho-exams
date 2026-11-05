import java.util.*;
public class DependencyComponents {
    static int[] groups(int[][] edges){
        int n=edges.length;List<List<Integer>> reverse=new ArrayList<>();for(int i=0;i<n;i++)reverse.add(new ArrayList<>());
        for(int v=0;v<n;v++){if(edges[v]==null)throw new IllegalArgumentException("Missing adjacency");for(int next:edges[v]){if(next<0||next>=n)throw new IllegalArgumentException("Invalid endpoint");reverse.get(next).add(v);}}
        boolean[] seen=new boolean[n];int[] cursor=new int[n];List<Integer> finished=new ArrayList<>();ArrayDeque<Integer> stack=new ArrayDeque<>();
        for(int start=0;start<n;start++)if(!seen[start]){
            seen[start]=true;stack.push(start);
            while(!stack.isEmpty()){
                int v=stack.peek();if(cursor[v]<edges[v].length){int next=edges[v][cursor[v]++];if(!seen[next]){seen[next]=true;stack.push(next);}}
                else {stack.pop();finished.add(v);}
            }
        }
        int[] group=new int[n];Arrays.fill(group,-1);int label=0;
        for(int i=finished.size()-1;i>=0;i--){int start=finished.get(i);if(group[start]>=0)continue;group[start]=label;stack.push(start);
            while(!stack.isEmpty()){int v=stack.pop();for(int next:reverse.get(v))if(group[next]<0){group[next]=label;stack.push(next);}}
            label++;
        }return group;
    }
    public static void main(String[] args){
        int[] group=groups(new int[][]{{1},{0,2},{3},{2},{}});
        System.out.println(group[0]==group[1]);System.out.println(group[2]==group[3]);System.out.println(group[1]==group[2]);
    }
}
