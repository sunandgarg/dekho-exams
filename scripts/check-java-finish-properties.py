"""Check exact article algorithms against independent reference models."""
import html,json,pathlib,re,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'src/data/fixtures.json').read_text())
slugs={'avl-tree','trie','binary-heap','kmp-search','minimum-spanning-tree','bellman-ford','tabulation','greedy-intervals','conditions'}
check=r'''
import java.util.*;
import java.util.concurrent.*;
public class FinishProperties {
 static int checks;
 static void verify(boolean ok){checks++;if(!ok)throw new AssertionError("check="+checks);}
 static int avl(ShipmentAvlIndex.Node n,long lower,long upper){
  if(n==null)return 0;
  verify(n.id>lower&&n.id<upper);
  int a=avl(n.left,lower,n.id),b=avl(n.right,n.id,upper);
  verify(Math.abs(a-b)<=1);verify(n.height==1+Math.max(a,b));return n.height;
 }
 static int root(int[] parent,int v){while(parent[v]!=v)v=parent[v];return v;}
 static long bruteForest(int count,DepotLinkForest.Edge[] edges){
  int[] connected=new int[count];for(int i=0;i<count;i++)connected[i]=i;
  for(DepotLinkForest.Edge e:edges)connected[root(connected,e.from)]=root(connected,e.to);
  int required=0;for(int i=0;i<count;i++)if(root(connected,i)==i)required++;
  long best=Long.MAX_VALUE;
  for(int mask=0;mask<(1<<edges.length);mask++){
   int[] parent=new int[count];for(int i=0;i<count;i++)parent[i]=i;
   long cost=0;int remaining=count;boolean valid=true;
   for(int i=0;i<edges.length;i++)if((mask&(1<<i))!=0){
    DepotLinkForest.Edge e=edges[i];int a=root(parent,e.from),b=root(parent,e.to);
    if(a==b){valid=false;break;}parent[a]=b;remaining--;cost+=e.cost;
   }
   if(valid&&remaining==required)best=Math.min(best,cost);
  }return best;
 }
 static int bruteIntervals(int[][] jobs){
  int best=0;
  for(int mask=0;mask<(1<<jobs.length);mask++){
   boolean valid=true;
   for(int i=0;i<jobs.length;i++)for(int j=i+1;j<jobs.length;j++)if((mask&(1<<i))!=0&&(mask&(1<<j))!=0)
    if(jobs[i][0]<jobs[j][1]&&jobs[j][0]<jobs[i][1])valid=false;
   if(valid)best=Math.max(best,Integer.bitCount(mask));
  }return best;
 }
 static int bfsPacks(int quantity,int[] packs){
  int[] distance=new int[quantity+1];Arrays.fill(distance,-1);distance[0]=0;
  ArrayDeque<Integer> queue=new ArrayDeque<>();queue.add(0);
  while(!queue.isEmpty()){
   int amount=queue.remove();for(int pack:packs)if(amount+pack<=quantity&&distance[amount+pack]<0){distance[amount+pack]=distance[amount]+1;queue.add(amount+pack);}
  }return distance[quantity];
 }
 static String word(Random random){StringBuilder b=new StringBuilder();for(int i=random.nextInt(8);i>0;i--)b.append((char)('a'+random.nextInt(4)));return b.toString();}
 static int trieNodes(ParcelCommandTrie.Node node){int count=1;for(ParcelCommandTrie.Node child:node.children)if(child!=null)count+=trieNodes(child);return count;}
 public static void main(String[] args)throws Exception{
  Random random=new Random(29092026L);
  for(int trial=0;trial<100;trial++){
   ShipmentAvlIndex index=new ShipmentAvlIndex();Set<Integer> ids=new TreeSet<>();
   for(int step=0;step<100;step++){
    int id=trial==0?step:trial==1?-step:random.nextInt(101)-50;
    index.add(id);ids.add(id);avl(index.root,Long.MIN_VALUE,Long.MAX_VALUE);
    for(int target=-55;target<=55;target++)verify(index.contains(target)==ids.contains(target));
   }
  }
  for(int trial=0;trial<200;trial++){
   FixedDispatchHeap actual=new FixedDispatchHeap(30);PriorityQueue<Integer> expected=new PriorityQueue<>();
   for(int step=0;step<100;step++){
    if(expected.isEmpty()||expected.size()<30&&random.nextBoolean()){int priority=random.nextInt(41)-20;expected.add(priority);actual.add(priority);}
    else verify(actual.poll()==expected.remove());
    verify(actual.size==expected.size());
    for(int i=1;i<actual.size;i++)verify(actual.priorities[(i-1)/2]<=actual.priorities[i]);
   }
   while(!expected.isEmpty())verify(actual.poll()==expected.remove());
   try{actual.poll();verify(false);}catch(NoSuchElementException correct){verify(true);}
  }
  FixedDispatchHeap full=new FixedDispatchHeap(1);full.add(3);try{full.add(4);verify(false);}catch(IllegalStateException correct){verify(full.size==1&&full.poll()==3);}
  for(int trial=0;trial<120;trial++){
   ParcelCommandTrie trie=new ParcelCommandTrie();Set<String> words=new HashSet<>();
   for(int step=0;step<50;step++){
    String value=word(random);if(!value.isEmpty()){trie.add(value);words.add(value);}
    String query=word(random);verify(trie.contains(query)==words.contains(query));
    boolean prefix=query.isEmpty();for(String s:words)prefix|=s.startsWith(query);verify(trie.hasPrefix(query)==prefix);
   }
   int nodes=trieNodes(trie.root);try{trie.add("abcZ");verify(false);}catch(IllegalArgumentException correct){verify(trieNodes(trie.root)==nodes);}
  }
  for(int trial=0;trial<4000;trial++){
   String text=word(random)+word(random),pattern=word(random);verify(ManifestPatternSearch.find(text,pattern)==text.indexOf(pattern));
  }
  for(String text:new String[]{"","aaaaaa","a\ud83d\ude00b\ud83d\ude00","\ude00","abababac"})
   for(String pattern:new String[]{"","a","aa","ababac","\ud83d\ude00","\ude00","longer-than-text"})verify(ManifestPatternSearch.find(text,pattern)==text.indexOf(pattern));
  for(int trial=0;trial<250;trial++){
   int vertices=1+random.nextInt(5);DepotLinkForest.Edge[] edges=new DepotLinkForest.Edge[random.nextInt(9)];
   for(int i=0;i<edges.length;i++)edges[i]=new DepotLinkForest.Edge(random.nextInt(vertices),random.nextInt(vertices),random.nextInt(19)-9);
   DepotLinkForest.Result result=DepotLinkForest.connect(vertices,edges);verify(result.cost==bruteForest(vertices,edges));
  }
  for(int trial=0;trial<300;trial++){
   int n=6;List<CreditRouteDistances.Edge> edges=new ArrayList<>();long[][] distances=new long[n][n];
   long absent=1_000_000L;for(int i=0;i<n;i++){Arrays.fill(distances[i],absent);distances[i][i]=0;}
   for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(random.nextBoolean()){
    int weight=random.nextInt(21)-10;edges.add(new CreditRouteDistances.Edge(i,j,weight));distances[i][j]=weight;
   }
   for(int via=0;via<n;via++)for(int a=0;a<n;a++)for(int b=0;b<n;b++)if(distances[a][via]!=absent&&distances[via][b]!=absent)distances[a][b]=Math.min(distances[a][b],distances[a][via]+distances[via][b]);
   long[] actual=CreditRouteDistances.distances(n,edges.toArray(new CreditRouteDistances.Edge[0]),0);
   for(int i=0;i<n;i++)verify(actual[i]==(distances[0][i]==absent?Long.MAX_VALUE:distances[0][i]));
  }
  CreditRouteDistances.Edge[] cycle={new CreditRouteDistances.Edge(1,2,-1),new CreditRouteDistances.Edge(2,1,0)};
  verify(CreditRouteDistances.distances(3,cycle,0)[1]==Long.MAX_VALUE);
  try{CreditRouteDistances.distances(3,cycle,1);verify(false);}catch(IllegalStateException correct){verify(true);}
  for(int trial=0;trial<300;trial++){
   int[] packs=new int[random.nextInt(5)];for(int i=0;i<packs.length;i++)packs[i]=1+random.nextInt(12);
   for(int amount=0;amount<60;amount++)verify(ExactPackTabulation.minimum(amount,packs)==bfsPacks(amount,packs));
   int[][] jobs=new int[random.nextInt(9)][2];for(int i=0;i<jobs.length;i++){jobs[i][0]=random.nextInt(21)-10;jobs[i][1]=jobs[i][0]+1+random.nextInt(7);}
   int[][] snapshot=Arrays.stream(jobs).map(int[]::clone).toArray(int[][]::new);
   verify(LoadingBayIntervals.maximumCount(jobs)==bruteIntervals(jobs));verify(Arrays.deepEquals(snapshot,jobs));
  }
  ExecutorService worker=Executors.newSingleThreadExecutor();
  try{
   ReceivingDeskCondition desk=new ReceivingDeskCondition();CountDownLatch started=new CountDownLatch(1);
   Future<Boolean> result=worker.submit(()->{started.countDown();return desk.take(TimeUnit.SECONDS.toNanos(2));});
   verify(started.await(2,TimeUnit.SECONDS));
   boolean waiting=false;long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
   while(!waiting&&System.nanoTime()<deadline){
    desk.lock.lock();try{waiting=desk.lock.hasWaiters(desk.available);}finally{desk.lock.unlock();}
    if(!waiting)Thread.yield();
   }
   verify(waiting);desk.receive();verify(result.get(2,TimeUnit.SECONDS));verify(!desk.take(0));
   verify(!desk.take(TimeUnit.MILLISECONDS.toNanos(2)));
   Thread.currentThread().interrupt();try{desk.take(1000);verify(false);}catch(InterruptedException correct){verify(true);}finally{Thread.interrupted();}
   desk.receive();verify(desk.take(0));
  }finally{worker.shutdownNow();verify(worker.awaitTermination(2,TimeUnit.SECONDS));}
  System.out.println("checks="+checks);
 }
}
'''
with tempfile.TemporaryDirectory(prefix='aitrove-java-finish-properties-') as directory:
 work=pathlib.Path(directory)
 for e in entries:
  if e['path'].split('/')[-1] in slugs:
   source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',e['body'])[1]);name=re.search(r'public class (\w+)',source)[1];(work/(name+'.java')).write_text(source)
 (work/'FinishProperties.java').write_text(check)
 run=subprocess.run(['/usr/bin/javac','--release','8','-d',str(work),*map(str,work.glob('*.java'))],capture_output=True,text=True);assert run.returncode==0,run.stderr
 run=subprocess.run(['/usr/bin/java','-cp',str(work),'FinishProperties'],capture_output=True,text=True,timeout=30);assert run.returncode==0,(run.stdout,run.stderr)
 report={'topics':sorted(slugs),'checks':int(re.search(r'checks=(\d+)',run.stdout)[1]),'passed':True,'methods':'Seeded random tests, AVL invariants, JDK references, exhaustive small forests and schedules, Floyd-Warshall, BFS, and bounded condition waiting.'}
 (ROOT.parent.parent/'outputs/java-finish-properties.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
