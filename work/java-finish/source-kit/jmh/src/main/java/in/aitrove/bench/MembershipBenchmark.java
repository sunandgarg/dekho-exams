package in.aitrove.bench;
import org.openjdk.jmh.annotations.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
public class MembershipBenchmark {
    @Param({"64","4096"}) public int size;
    @Param({"63","8192"}) public int key;
    Set<Integer> indexed;List<Integer> scanned;
    @Setup public void prepare(){
        indexed=new HashSet<>();scanned=new ArrayList<>();
        for(int value=0;value<size;value++){indexed.add(value);scanned.add(value);}
    }
    @Benchmark public boolean indexedLookup(){return indexed.contains(key);}
    @Benchmark public boolean scannedLookup(){return scanned.contains(key);}
}
