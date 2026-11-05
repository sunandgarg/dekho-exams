"""Compare new range/DP lessons against independent direct-sum and BFS oracles."""
import html,json,pathlib,re,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];lookup={e['path']:e for e in json.loads((ROOT/'src/data/fixtures.json').read_text())}
with tempfile.TemporaryDirectory(prefix='aitrove-new-algorithms-') as tmp:
 work=pathlib.Path(tmp)
 for slug in ('segment-tree','coin-change'):
  text=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',lookup['java/'+slug]['body'])[1]);name=re.search(r'public class (\w+)',text)[1];(work/(name+'.java')).write_text(text)
 source='''import java.util.*;
public class AdditionalAlgorithmChecks {
 public static void main(String[] args) {
  Random random = new Random(92831); int assertions = 0;
  for(int trial=0;trial<500;trial++) {
   int[] values=new int[1+random.nextInt(40)];
   for(int i=0;i<values.length;i++) values[i]=random.nextInt(201)-100;
   WarehouseRangeTotals ranges=new WarehouseRangeTotals(values);
   for(int turn=0;turn<80;turn++) {
    if(turn%3==0){int index=random.nextInt(values.length);int value=random.nextInt(201)-100;values[index]=value;ranges.replace(index,value);}
    int start=random.nextInt(values.length+1);int end=start+random.nextInt(values.length-start+1);long expected=0;
    for(int i=start;i<end;i++)expected+=values[i];
    if(expected!=ranges.sum(start,end))throw new AssertionError("range");assertions++;
   }
  }
  for(int trial=0;trial<500;trial++) {
   int[] coins={1+random.nextInt(10),1+random.nextInt(10),1+random.nextInt(10)};
   int target=random.nextInt(60);int[] distance=new int[target+1];Arrays.fill(distance,-1);distance[0]=0;
   ArrayDeque<Integer> queue=new ArrayDeque<>();queue.add(0);
   while(!queue.isEmpty()){int amount=queue.remove();for(int coin:coins){int next=amount+coin;if(next<=target&&distance[next]<0){distance[next]=distance[amount]+1;queue.add(next);}}}
   if(distance[target]!=VoucherMinimum.minimum(coins,target))throw new AssertionError("coin");assertions++;
  }
  System.out.println(assertions);
 }
}'''
 (work/'AdditionalAlgorithmChecks.java').write_text(source)
 result=subprocess.run(['/usr/bin/javac','--release','8','-d',str(work),*map(str,work.glob('*.java'))],capture_output=True,text=True);assert result.returncode==0,result.stderr
 result=subprocess.run(['/usr/bin/java','-cp',str(work),'AdditionalAlgorithmChecks'],capture_output=True,text=True);assert result.returncode==0,result.stderr;assert result.stdout.strip()=='40500',result.stdout
report={'passed':True,'independentOracleAssertions':40500,'segmentTreeCases':40000,'coinChangeBfsComparisons':500,'seed':92831}
(ROOT.parent.parent/'outputs/java-spring-algorithm-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
