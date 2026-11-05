"""Independent checks for deletion, sequence, graph, range and application invariants."""
import html,json,pathlib,re,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'src/data/fixtures.json').read_text())
slugs={'avl-deletion','trie-deletion','floyd-warshall','strong-components','edit-distance','longest-subsequence','increasing-subsequence','zero-one-knapsack','fenwick-tree','dp-exercises','multi-index-invariants','concurrent-import-project'}
check=r'''
import java.util.*;
import java.util.concurrent.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
public class DepthProperties {
 static int checks;
 static void verify(boolean ok){checks++;if(!ok)throw new AssertionError("check="+checks);}
 static int avl(DeletableShipmentAvl.Node n,long low,long high){
  if(n==null)return 0;verify(n.key>low&&n.key<high);int a=avl(n.left,low,n.key),b=avl(n.right,n.key,high);verify(Math.abs(a-b)<=1);verify(n.height==1+Math.max(a,b));return n.height;
 }
 static String word(Random r){StringBuilder b=new StringBuilder();for(int i=1+r.nextInt(7);i>0;i--)b.append((char)('a'+r.nextInt(4)));return b.toString();}
 static int nodes(DeletableCommandTrie.Node n){int total=1;for(DeletableCommandTrie.Node child:n.children)if(child!=null)total+=nodes(child);return total;}
 static int edits(String a,String b){int[][] result=new int[a.length()+1][b.length()+1];for(int i=0;i<=a.length();i++)result[i][0]=i;for(int j=0;j<=b.length();j++)result[0][j]=j;for(int i=1;i<=a.length();i++)for(int j=1;j<=b.length();j++)result[i][j]=Math.min(Math.min(result[i-1][j]+1,result[i][j-1]+1),result[i-1][j-1]+(a.charAt(i-1)==b.charAt(j-1)?0:1));return result[a.length()][b.length()];}
 static int common(String a,String b){int best=0;for(int mask=0;mask<(1<<a.length());mask++){int cursor=0,used=0;boolean matches=true;for(int i=0;i<a.length();i++)if((mask&(1<<i))!=0){cursor=b.indexOf(a.charAt(i),cursor);if(cursor<0){matches=false;break;}cursor++;used++;}if(matches)best=Math.max(best,used);}return best;}
 static int increasing(int[] values){int[] best=new int[values.length];int answer=0;for(int i=0;i<values.length;i++){best[i]=1;for(int j=0;j<i;j++)if(values[j]<values[i])best[i]=Math.max(best[i],best[j]+1);answer=Math.max(answer,best[i]);}return answer;}
 static boolean[][] reach(int[][] edges){int n=edges.length;boolean[][] r=new boolean[n][n];for(int start=0;start<n;start++){ArrayDeque<Integer> q=new ArrayDeque<>();r[start][start]=true;q.add(start);while(!q.isEmpty()){int v=q.remove();for(int next:edges[v])if(!r[start][next]){r[start][next]=true;q.add(next);}}}return r;}
 public static void main(String[] args)throws Exception{
  Random random=new Random(30092026L);
  for(int trial=0;trial<180;trial++){
   DeletableShipmentAvl index=new DeletableShipmentAvl();TreeSet<Integer> expected=new TreeSet<>();
   for(int step=0;step<160;step++){
    int key=trial==0?step:trial==1?-step:random.nextInt(151)-75;
    if(step<50||random.nextBoolean()){index.root=DeletableShipmentAvl.add(index.root,key);expected.add(key);}
    else{index.root=DeletableShipmentAvl.remove(index.root,key);expected.remove(key);}
    avl(index.root,Long.MIN_VALUE,Long.MAX_VALUE);List<Integer> actual=new ArrayList<>();DeletableShipmentAvl.ordered(index.root,actual);verify(actual.equals(new ArrayList<>(expected)));
   }
   for(int key:new ArrayList<>(expected)){index.root=DeletableShipmentAvl.remove(index.root,key);expected.remove(key);avl(index.root,Long.MIN_VALUE,Long.MAX_VALUE);}verify(index.root==null);
  }
  for(int trial=0;trial<100;trial++){
   DeletableCommandTrie trie=new DeletableCommandTrie();Set<String> stored=new HashSet<>();
   for(int step=0;step<100;step++){
    String w=word(random);if(random.nextBoolean()){trie.add(w);stored.add(w);}else verify(trie.remove(w)==stored.remove(w));
    String q=word(random);verify(trie.contains(q)==stored.contains(q));Set<String> prefixes=new HashSet<>();for(String s:stored)for(int i=1;i<=s.length();i++)prefixes.add(s.substring(0,i));verify(nodes(trie.root)==prefixes.size()+1);
   }
   int prior=nodes(trie.root);try{trie.remove("abcZ");verify(false);}catch(IllegalArgumentException expected){verify(nodes(trie.root)==prior);}
  }
  for(int trial=0;trial<250;trial++){
   int n=1+random.nextInt(8);int[][] edges=new int[n][];
   for(int i=0;i<n;i++){List<Integer> next=new ArrayList<>();for(int j=0;j<n;j++)if(random.nextInt(4)==0)next.add(j);edges[i]=next.stream().mapToInt(Integer::intValue).toArray();}
   int[] groups=DependencyComponents.groups(edges);boolean[][] r=reach(edges);for(int i=0;i<n;i++)for(int j=0;j<n;j++)verify((groups[i]==groups[j])==(r[i][j]&&r[j][i]));
   long[][] weights=new long[n][n];for(int i=0;i<n;i++){Arrays.fill(weights[i],Long.MAX_VALUE);weights[i][i]=0;for(int to:edges[i])if(to!=i)weights[i][to]=random.nextInt(15);}
   long[][] actual=DepotAllPairs.distances(weights);
   for(int start=0;start<n;start++){
    long[] reference=new long[n];Arrays.fill(reference,Long.MAX_VALUE);reference[start]=0;
    for(int pass=1;pass<n;pass++)for(int from=0;from<n;from++)for(int to=0;to<n;to++)if(reference[from]!=Long.MAX_VALUE&&weights[from][to]!=Long.MAX_VALUE)reference[to]=Math.min(reference[to],reference[from]+weights[from][to]);
    verify(Arrays.equals(reference,actual[start]));
   }
  }
  verify(DependencyComponents.groups(new int[0][]).length==0);verify(DepotAllPairs.distances(new long[0][]).length==0);
  try{DepotAllPairs.distances(new long[][]{{0,-2},{1,0}});verify(false);}catch(IllegalStateException expected){verify(true);}
  for(int trial=0;trial<1000;trial++){
   String a=word(random),b=word(random);verify(ReceiptLabelDistance.distance(a,b)==edits(a,b));verify(ManifestCommonOrder.length(a,b)==common(a,b));
   int[] values=new int[random.nextInt(14)];for(int i=0;i<values.length;i++)values[i]=random.nextInt(13)-6;verify(ArrivalIncreasingOrder.length(values)==increasing(values));
  }
  for(String a:new String[]{"","\ud83d\ude00","e\u0301","ababa"})for(String b:new String[]{"","\ude00","\u00e9","baba"}){verify(ReceiptLabelDistance.distance(a,b)==edits(a,b));verify(ManifestCommonOrder.length(a,b)==common(a,b));}
  verify(ArrivalIncreasingOrder.length(new int[]{Integer.MIN_VALUE,0,Integer.MAX_VALUE})==3);
  for(int trial=0;trial<500;trial++){
   int n=random.nextInt(10),capacity=random.nextInt(25);int[] weights=new int[n];long[] values=new long[n];for(int i=0;i<n;i++){weights[i]=1+random.nextInt(9);values[i]=random.nextInt(25);}
   verify(DispatchBagValue.maximum(capacity,weights,values)==BagSubsetOracle.maximum(capacity,weights,values));
  }
  try{DispatchBagValue.maximum(2,new int[]{1,1},new long[]{Long.MAX_VALUE,1});verify(false);}catch(ArithmeticException expected){verify(true);}
  for(int trial=0;trial<100;trial++){
   int n=1+random.nextInt(35);ReceiptFenwickTotals sums=new ReceiptFenwickTotals(n);long[] values=new long[n];
   for(int step=0;step<150;step++){
    int at=random.nextInt(n),delta=random.nextInt(2001)-1000;sums.add(at,delta);values[at]+=delta;
    for(int end=0;end<=n;end++){long total=0;for(int i=0;i<end;i++)total+=values[i];verify(sums.prefix(end)==total);}
    int from=random.nextInt(n+1),end=from+random.nextInt(n-from+1);long total=0;for(int i=from;i<end;i++)total+=values[i];verify(sums.range(from,end)==total);
   }
   long[] snapshot=sums.sums.clone();try{sums.add(0,Long.MIN_VALUE);verify(false);}catch(IllegalArgumentException expected){verify(Arrays.equals(snapshot,sums.sums));}
  }
  StockReservationBoundary service=new StockReservationBoundary();ExecutorService pool=Executors.newFixedThreadPool(4);List<Future<Boolean>> reservations=new ArrayList<>();
  try{for(int i=0;i<40;i++){final int id=i;reservations.add(pool.submit(()->service.reserve("R-"+id,1)));}int accepted=0;for(Future<Boolean> f:reservations)if(f.get(2,TimeUnit.SECONDS))accepted++;verify(accepted==7);verify(service.status().equals("stock=0, reservations=7"));}
  finally{pool.shutdownNow();verify(pool.awaitTermination(2,TimeUnit.SECONDS));}
  Path directory=Files.createTempDirectory("aitrove-depth-import-"),input=directory.resolve("input.csv"),output=directory.resolve("snapshot.csv");
  try{
   for(int count=0;count<=6;count++){List<String> rows=new ArrayList<>();for(int i=0;i<count;i++)rows.add("R-"+i+","+i);Files.write(input,rows,StandardCharsets.UTF_8);ConcurrentReceiptImport.importFile(input,output);verify(Files.readAllLines(output,StandardCharsets.UTF_8).equals(rows));}
   byte[] snapshot=Files.readAllBytes(output);
   for(List<String> bad:Arrays.asList(Arrays.asList("R-1,3","invalid"),Arrays.asList("R-1,3","R-1,2"),Arrays.asList("R-2,-1"))){
    Files.write(input,bad,StandardCharsets.UTF_8);try{ConcurrentReceiptImport.importFile(input,output);verify(false);}catch(ExecutionException|IllegalArgumentException expected){verify(Arrays.equals(snapshot,Files.readAllBytes(output)));}
   }
  }finally{Files.deleteIfExists(input);Files.deleteIfExists(output);Files.deleteIfExists(directory);}
  System.out.println("checks="+checks);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='aitrove-java-depth-properties-') as directory:
 work=pathlib.Path(directory)
 for e in entries:
  if e['path'].split('/')[-1] in slugs:
   text=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',e['body'])[1]);name=re.search(r'public class (\w+)',text)[1];(work/(name+'.java')).write_text(text)
 (work/'DepthProperties.java').write_text(check)
 a=subprocess.run(['/usr/bin/javac','--release','8','-d',str(work),*map(str,work.glob('*.java'))],capture_output=True,text=True);assert a.returncode==0,a.stderr
 b=subprocess.run(['/usr/bin/java','-cp',str(work),'DepthProperties'],capture_output=True,text=True,timeout=30);assert b.returncode==0,(b.stdout,b.stderr)
 report={'topics':sorted(slugs),'checks':int(re.search('checks=(\\d+)',b.stdout)[1]),'passed':True,'methods':'Seeded random tests, TreeSet plus AVL invariants, trie prefix sets, independent reachability and relaxation, exhaustive subsequences/subsets, quadratic LIS, full-matrix edit distance, array sums and failure-preserving imports.'}
 (ROOT.parent.parent/'outputs/java-depth-properties.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
