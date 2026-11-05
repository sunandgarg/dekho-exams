"""Check new tutorial algorithms against independent small-input reference results."""
import html, json, pathlib, re, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
entries=json.loads((ROOT/'src/data/fixtures.json').read_text())
slugs={'two-pointers','sliding-window','binary-search-tree','heap-top-k','union-find','dijkstra','topological-sort','backtracking','array-string-exercises','atomics','locks'}
check=r'''
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class TutorialProperties {
    static int checks;
    static void verify(boolean condition) {
        checks++;
        if (!condition) throw new IllegalStateException("Property failed at check " + checks);
    }
    static void rejects(Runnable operation) {
        boolean rejected = false;
        try { operation.run(); } catch (IllegalArgumentException expected) { rejected = true; }
        verify(rejected);
    }
    public static void main(String[] args) throws Exception {
        Random random = new Random(92026);
        for (int trial = 0; trial < 180; trial++) {
            int count = random.nextInt(10);
            int[] weights = new int[count];
            for (int i = 0; i < count; i++) weights[i] = random.nextInt(31)-15;
            Arrays.sort(weights);
            long target = random.nextInt(41)-20;
            boolean exists=false;
            for(int i=0;i<count;i++) for(int j=i+1;j<count;j++) if((long)weights[i]+weights[j]==target) exists=true;
            int[] pair=PackagePairSearch.pair(weights,target);
            verify((pair.length==2)==exists);
            if(exists) verify((long)pair[0]+pair[1]==target);
            for(int width=1;width<=count;width++) {
                long best=Long.MIN_VALUE;
                for(int start=0;start+width<=count;start++) {
                    long total=0;
                    for(int i=start;i<start+width;i++) total+=weights[i];
                    best=Math.max(best,total);
                }
                verify(BusiestHours.maximum(weights,width)==best);
            }
            for(int limit=1;limit<=count+2;limit++) {
                List<Integer> expected=new ArrayList<>();
                for(int weight:weights) expected.add(weight);
                expected.sort(Collections.reverseOrder());
                expected=new ArrayList<>(expected.subList(0,Math.min(limit,count)));
                verify(QueueDepthLeaders.largest(weights,limit).equals(expected));
            }
            ShipmentIdTree.Entry root=null;
            TreeSet<Integer> membership=new TreeSet<>();
            for(int weight:weights) {root=ShipmentIdTree.insert(root,weight);membership.add(weight);}
            for(int operation=0;operation<15;operation++) {
                int removed=random.nextInt(31)-15;
                root=ShipmentIdTree.delete(root,removed); membership.remove(removed);
                List<Integer> actual=new ArrayList<>(); ShipmentIdTree.ordered(root,actual);
                verify(actual.equals(new ArrayList<>(membership)));
            }
        }
        verify(Arrays.equals(PackagePairSearch.pair(new int[]{Integer.MIN_VALUE,Integer.MAX_VALUE},-1),new int[]{Integer.MIN_VALUE,Integer.MAX_VALUE}));
        rejects(()->BusiestHours.maximum(new int[]{1},0));
        rejects(()->BusiestHours.maximum(new int[]{1},2));
        rejects(()->QueueDepthLeaders.largest(new int[]{1},0));
        for(int trial=0;trial<60;trial++) {
            DepotComponents groups=new DepotComponents(8);
            boolean[][] reachable=new boolean[8][8];
            for(int i=0;i<8;i++) reachable[i][i]=true;
            for(int operation=0;operation<25;operation++) {
                int first=random.nextInt(8),second=random.nextInt(8);
                groups.connect(first,second);reachable[first][second]=reachable[second][first]=true;
                for(int via=0;via<8;via++)for(int i=0;i<8;i++)for(int j=0;j<8;j++)reachable[i][j]|=reachable[i][via]&&reachable[via][j];
                for(int i=0;i<8;i++)for(int j=0;j<8;j++)verify((groups.find(i)==groups.find(j))==reachable[i][j]);
            }
        }
        rejects(()->new DepotComponents(2).find(2));
        for(int trial=0;trial<80;trial++) {
            int depots=7;
            List<List<DeliveryDistances.Road>> roads=new ArrayList<>();
            for(int i=0;i<depots;i++)roads.add(new ArrayList<>());
            for(int i=0;i<depots;i++)for(int j=0;j<depots;j++)if(i!=j&&random.nextInt(4)==0)roads.get(i).add(new DeliveryDistances.Road(j,random.nextInt(10)));
            long[] reference=new long[depots];Arrays.fill(reference,Long.MAX_VALUE);reference[0]=0;
            for(int pass=0;pass<depots-1;pass++)for(int i=0;i<depots;i++)if(reference[i]!=Long.MAX_VALUE)for(DeliveryDistances.Road road:roads.get(i))reference[road.depot]=Math.min(reference[road.depot],reference[i]+road.minutes);
            verify(Arrays.equals(DeliveryDistances.shortest(roads,0),reference));
        }
        rejects(()->new DeliveryDistances.Road(0,-1));
        for(int trial=0;trial<80;trial++) {
            int[][] edges=new int[8][];
            for(int i=0;i<8;i++) {
                List<Integer> destinations=new ArrayList<>();
                for(int j=i+1;j<8;j++)if(random.nextBoolean())destinations.add(j);
                edges[i]=destinations.stream().mapToInt(Integer::intValue).toArray();
            }
            int[] ordered=BuildPrerequisites.order(edges),position=new int[8];
            verify(ordered.length==8);
            for(int i=0;i<8;i++)position[ordered[i]]=i;
            for(int i=0;i<8;i++)for(int j:edges[i])verify(position[i]<position[j]);
        }
        rejects(()->BuildPrerequisites.order(new int[][]{{1},{0}}));
        rejects(()->BuildPrerequisites.order(new int[][]{{0}}));
        verify(BuildPrerequisites.order(new int[0][]).length==0);
        for(int trial=0;trial<80;trial++) {
            int[] weights=new int[random.nextInt(8)];
            for(int i=0;i<weights.length;i++)weights[i]=1+random.nextInt(6);
            int target=random.nextInt(16);
            List<String> expected=new ArrayList<>(),actual=new ArrayList<>();
            for(int mask=0;mask<(1<<weights.length);mask++) {
                int total=0;List<Integer> chosen=new ArrayList<>();
                for(int i=0;i<weights.length;i++)if((mask&(1<<i))!=0){total+=weights[i];chosen.add(weights[i]);}
                if(total==target)expected.add(chosen.toString());
            }
            for(List<Integer> result:PackingCombinations.combinations(weights,target))actual.add(result.toString());
            Collections.sort(expected);Collections.sort(actual);verify(actual.equals(expected));
        }
        rejects(()->PackingCombinations.combinations(new int[]{0},0));
        rejects(()->PackingCombinations.combinations(new int[]{2},-1));
        verify(Arrays.equals(IntakeBoundaryChecks.collapseRuns(new int[]{9,9,9}),new int[]{9}));
        verify(IntakeBoundaryChecks.asciiPalindrome("!!!"));
        ExecutorService workers=Executors.newFixedThreadPool(12);
        try {
            AdmissionGate gate=new AdmissionGate(3);
            AtomicInteger inside=new AtomicInteger();
            List<Future<?>> tasks=new ArrayList<>();
            for(int task=0;task<500;task++)tasks.add(workers.submit(()->{
                if(gate.reserve()) {
                    try {
                        int active=inside.incrementAndGet();
                        if(active>3)throw new IllegalStateException("Admission capacity exceeded");
                        Thread.yield();inside.decrementAndGet();
                    } finally {gate.release();}
                }
            }));
            for(Future<?> task:tasks)task.get();verify(inside.get()==0);
            verify(gate.reserve());verify(gate.reserve());verify(gate.reserve());verify(!gate.reserve());
            StockReservations ledger=new StockReservations();AtomicInteger admitted=new AtomicInteger();tasks.clear();
            for(int task=0;task<100;task++)tasks.add(workers.submit(()->{if(ledger.reserve(1))admitted.incrementAndGet();}));
            for(Future<?> task:tasks)task.get();verify(admitted.get()==12);verify(ledger.snapshot().equals("available=0, reserved=12"));
        } finally {workers.shutdown();}
        System.out.println("propertyChecks="+checks);
    }
}
'''
with tempfile.TemporaryDirectory(prefix='aitrove-java-properties-') as folder:
    directory=pathlib.Path(folder)
    for e in entries:
        if e['path'].split('/')[-1] in slugs:
            for source in re.findall(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',e['body']):
                source=html.unescape(source)
                name=re.search(r'public class (\w+)',source)[1]
                (directory/(name+'.java')).write_text(source)
    (directory/'TutorialProperties.java').write_text(check)
    sources=[str(p) for p in directory.glob('*.java')]
    compiled=subprocess.run(['/usr/bin/javac','--release','8','-d',str(directory)]+sources,capture_output=True,text=True)
    assert compiled.returncode==0,compiled.stderr
    run=subprocess.run(['/usr/bin/java','-cp',str(directory),'TutorialProperties'],capture_output=True,text=True,timeout=45)
    assert run.returncode==0,run.stderr
    count=int(run.stdout.strip().split('=')[1])
report={'passed':True,'seed':92026,'propertyChecks':count,'topics':sorted(slugs),'tests':'Brute-force range/pair/subset checks; reference sorted membership; transitive closure; repeated relaxation distances; prerequisite constraints; concurrent capacity and ledger invariants.'}
(ROOT.parent.parent/'outputs/java-next-properties.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
