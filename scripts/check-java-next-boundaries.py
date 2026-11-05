"""Run independent range-sum oracles and additional rejected-input/lifetime checks."""
import html,json,pathlib,re,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];lookup={e['path']:e for e in json.loads((ROOT/'src/data/fixtures.json').read_text())}
with tempfile.TemporaryDirectory(prefix='aitrove-next-boundaries-') as tmp:
 work=pathlib.Path(tmp)
 for slug in ('lazy-segment-tree','strict-utf8','decimal-parse-boundary','serialization-filter'):
  source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',lookup['java/'+slug]['body'])[1]);name=re.search(r'public class (\w+)',source)[1];(work/(name+'.java')).write_text(source)
 source='''import java.util.*;
import java.math.*;
public class NextBoundaryChecks {
 static int assertions;
 static void equal(long expected,long actual) {if(expected!=actual)throw new AssertionError(expected+" != "+actual);assertions++;}
 interface Work {void run() throws Exception;}
 static void rejected(Class<? extends Exception> type,Work operation) throws Exception {
  try {operation.run();}catch(Exception failure){if(type.isInstance(failure)){assertions++;return;}throw failure;}
  throw new AssertionError("accepted invalid input");
 }
 public static void main(String[] args) throws Exception {
  Random random=new Random(929206);
  for(int trial=0;trial<600;trial++) {
   int n=1+random.nextInt(70);long[] values=new long[n];for(int i=0;i<n;i++)values[i]=random.nextInt(201)-100;
   CapacityRangeTree tree=new CapacityRangeTree(values);
   for(int step=0;step<100;step++) {
    int left=random.nextInt(n),right=left+1+random.nextInt(n-left);
    if(step%2==0){long change=random.nextInt(101)-50;tree.add(left,right,change);for(int i=left;i<right;i++)values[i]+=change;}
    int from=random.nextInt(n),until=from+1+random.nextInt(n-from);long total=0;for(int i=from;i<until;i++)total+=values[i];equal(total,tree.sum(from,until));
   }
  }
  rejected(IllegalArgumentException.class,()->new CapacityRangeTree(new long[0]));
  CapacityRangeTree one=new CapacityRangeTree(new long[]{9});one.add(0,1,-9);equal(0,one.sum(0,1));
  rejected(IllegalArgumentException.class,()->one.add(-1,1,4));
  rejected(IllegalArgumentException.class,()->one.sum(0,2));
  rejected(java.nio.charset.CharacterCodingException.class,()->ReceiptUtf8Boundary.decode(new byte[]{(byte)0xFF}));
  rejected(IllegalArgumentException.class,()->ReceiptUtf8Boundary.decode(new byte[4097]));
  equal(0,ReceiptUtf8Boundary.decode(new byte[0]).length());
  rejected(IllegalArgumentException.class,()->InvoiceAmountInput.parse("0.00"));
  rejected(IllegalArgumentException.class,()->InvoiceAmountInput.parse("12.00suffix"));
  rejected(ArithmeticException.class,()->InvoiceAmountInput.parse("12.345"));
  rejected(IllegalArgumentException.class,()->InvoiceAmountInput.parse("NaN"));
  rejected(java.io.InvalidClassException.class,()->LegacyBatchFilter.read(LegacyBatchFilter.encode(new int[5])));
  rejected(java.io.InvalidClassException.class,()->LegacyBatchFilter.read(LegacyBatchFilter.encode(new long[1])));
  rejected(java.io.IOException.class,()->LegacyBatchFilter.read(new byte[1025]));
  equal(2,LegacyBatchFilter.read(LegacyBatchFilter.encode(new int[]{7,9})).length);
  System.out.println(assertions);
 }
}'''
 (work/'NextBoundaryChecks.java').write_text(source)
 result=subprocess.run(['/usr/bin/javac','--release','11','-d',str(work),*map(str,work.glob('*.java'))],capture_output=True,text=True);assert result.returncode==0,result.stderr
 result=subprocess.run(['/usr/bin/java','-cp',str(work),'NextBoundaryChecks'],capture_output=True,text=True);assert result.returncode==0,result.stderr;assert result.stdout.strip()=='60015',result.stdout
report={'passed':True,'lazyRangeSumOracleComparisons':60000,'additionalInputBoundaryAssertions':15,'randomSeed':929206,'arithmeticScope':'small bounded values; no long-overflow guarantee'}
(ROOT.parent.parent/'outputs/java-next-boundaries.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
