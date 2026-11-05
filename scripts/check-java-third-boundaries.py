"""Compare new algorithms with direct reference work and check bounded-input failures."""
import html,json,pathlib,re,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
lookup={e['path']:e for e in json.loads((ROOT/'src/data/fixtures.json').read_text())}
with tempfile.TemporaryDirectory(prefix='aitrove-third-oracles-') as tmp:
 work=pathlib.Path(tmp)
 for slug in ('z-pattern-search','graph-bridges','matrix-chain','lru-cache','bytebuffer-order','record-defensive-copy'):
  source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',lookup['java/'+slug]['body'])[1])
  name=re.search(r'public class (\w+)',source)[1];(work/(name+'.java')).write_text(source)
 source=r'''import java.util.*;
public class ThirdBoundaryChecks {
 static int matches,graphs,chains,boundaries;
 static void equal(Object expected,Object actual){if(!Objects.equals(expected,actual))throw new AssertionError(expected+" != "+actual);}
 static void reject(Runnable operation){try{operation.run();}catch(IllegalArgumentException accepted){boundaries++;return;}throw new AssertionError("accepted invalid input");}
 static List<Integer> directMatches(String pattern,String text){List<Integer> result=new ArrayList<>();for(int i=0;i+pattern.length()<=text.length();i++)if(text.startsWith(pattern,i))result.add(i);return result;}
 static int components(int vertices,int[][] edges,int removed){
  boolean[] visited=new boolean[vertices];int count=0;
  for(int start=0;start<vertices;start++)if(!visited[start]){
   count++;ArrayDeque<Integer> pending=new ArrayDeque<>();pending.add(start);visited[start]=true;
   while(!pending.isEmpty()){int current=pending.remove();for(int id=0;id<edges.length;id++)if(id!=removed){int next=-1;if(edges[id][0]==current)next=edges[id][1];else if(edges[id][1]==current)next=edges[id][0];if(next>=0&&!visited[next]){visited[next]=true;pending.add(next);}}}
  }return count;
 }
 static List<Integer> directBridges(int vertices,int[][] edges){int baseline=components(vertices,edges,-1);List<Integer> result=new ArrayList<>();for(int id=0;id<edges.length;id++)if(components(vertices,edges,id)>baseline)result.add(id);return result;}
 static long allGroupings(int[] dimensions,int left,int right){if(left==right)return 0;long best=Long.MAX_VALUE;for(int split=left;split<right;split++)best=Math.min(best,allGroupings(dimensions,left,split)+allGroupings(dimensions,split+1,right)+(long)dimensions[left]*dimensions[split+1]*dimensions[right+1]);return best;}
 static String text(Random random,int size){StringBuilder result=new StringBuilder();char[] alphabet={'a','b','#','\uD83D','\uDE00'};for(int i=0;i<size;i++)result.append(alphabet[random.nextInt(alphabet.length)]);return result.toString();}
 public static void main(String[] args){
  Random random=new Random(929207);
  for(int trial=0;trial<3000;trial++){String pattern=text(random,1+random.nextInt(10)),input=text(random,random.nextInt(80));equal(directMatches(pattern,input),ReceiptPatternOffsets.find(pattern,input));matches++;}
  for(int trial=0;trial<1000;trial++){int vertices=1+random.nextInt(8);int[][] edges=new int[random.nextInt(18)][2];for(int[] edge:edges){edge[0]=random.nextInt(vertices);edge[1]=random.nextInt(vertices);}equal(directBridges(vertices,edges),TransportBridgeEdges.bridges(vertices,edges));graphs++;}
  for(int trial=0;trial<700;trial++){int[] dimensions=new int[2+random.nextInt(7)];for(int i=0;i<dimensions.length;i++)dimensions[i]=1+random.nextInt(20);equal(allGroupings(dimensions,0,dimensions.length-2),MatrixPlanCost.minimum(dimensions));chains++;}
  reject(()->ReceiptPatternOffsets.find("","x"));reject(()->ReceiptPatternOffsets.find("x".repeat(100001),"x"));reject(()->ReceiptPatternOffsets.find("x","x".repeat(100001)));
  equal(List.of(),ReceiptPatternOffsets.find("x",""));boundaries++;
  reject(()->TransportBridgeEdges.bridges(0,new int[0][]));reject(()->TransportBridgeEdges.bridges(501,new int[0][]));reject(()->TransportBridgeEdges.bridges(2,new int[][]{{0,2}}));
  int[][] path=new int[499][2];for(int i=0;i<499;i++){path[i][0]=i;path[i][1]=i+1;}equal(499,TransportBridgeEdges.bridges(500,path).size());boundaries++;
  reject(()->MatrixPlanCost.minimum(new int[]{4}));reject(()->MatrixPlanCost.minimum(new int[]{4,0}));reject(()->MatrixPlanCost.minimum(new int[]{4,1001}));
  int[] maximum=new int[11];Arrays.fill(maximum,1000);equal(9000000000L,MatrixPlanCost.minimum(maximum));boundaries++;
  reject(()->new DocumentLruCache(0));DocumentLruCache cache=new DocumentLruCache(1);cache.put("invoice","old");cache.put("invoice","new");equal(1,cache.size());equal("new",cache.get("invoice"));boundaries++;
  cache.put("receipt","R");equal(false,cache.containsKey("invoice"));equal(1,cache.size());boundaries++;
  reject(()->ReceiptHeaderOrder.read(new byte[5]));equal(-1,ReceiptHeaderOrder.read(new byte[]{-1,-1,-1,-1}));boundaries++;
  int[] input={7,9};var batch=new DefensiveReceiptBatch.Batch(input);input[0]=0;equal(7,batch.amounts()[0]);boundaries++;
  int[] returned=batch.amounts();returned[1]=0;equal(9,batch.amounts()[1]);boundaries++;
  equal(false,batch.equals(new DefensiveReceiptBatch.Batch(new int[]{7,9})));boundaries++;
  System.out.println(matches+":"+graphs+":"+chains+":"+boundaries);
 }
}'''
 (work/'ThirdBoundaryChecks.java').write_text(source)
 result=subprocess.run(['/usr/bin/javac','--release','17','-d',str(work),*map(str,work.glob('*.java'))],capture_output=True,text=True);assert result.returncode==0,result.stderr
 result=subprocess.run(['/usr/bin/java','-cp',str(work),'ThirdBoundaryChecks'],capture_output=True,text=True);assert result.returncode==0,result.stderr;assert result.stdout.strip()=='3000:1000:700:20',result.stdout
report={'passed':True,'zSearchAgainstDirectMatch':3000,'multigraphBridgesAgainstEdgeRemoval':1000,'matrixChainAgainstAllGroupings':700,'additionalBoundaries':20,'randomSeed':929207,'scope':'bounded in-memory inputs, UTF-16 offsets, multigraphs with self-loops; not a production load benchmark'}
(ROOT.parent.parent/'outputs/java-third-boundaries.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
