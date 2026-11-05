import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
public class ConcurrentReceiptImport {
    static class Row {final String reference;final int units;Row(String reference,int units){this.reference=reference;this.units=units;}}
    static Row parse(String line){
        if(line.length()>80)throw new IllegalArgumentException("Row length");String[] fields=line.split(",",-1);
        if(fields.length!=2||!fields[0].matches("R-[0-9]{1,8}"))throw new IllegalArgumentException("Receipt row");
        int units=Integer.parseInt(fields[1]);if(units<0||units>1000)throw new IllegalArgumentException("Unit range");return new Row(fields[0],units);
    }
    static void importFile(Path input,Path output)throws Exception{
        if(Files.size(input)>16_000)throw new IllegalArgumentException("Input size");List<String> lines=Files.readAllLines(input,StandardCharsets.UTF_8);if(lines.size()>6)throw new IllegalArgumentException("Row count");
        ThreadPoolExecutor workers=new ThreadPoolExecutor(2,2,0,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<>(4));List<Future<Row>> pending=new ArrayList<>();long deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2);
        try{
            for(String line:lines)pending.add(workers.submit(()->parse(line)));
            List<String> snapshot=new ArrayList<>();Set<String> references=new HashSet<>();
            for(Future<Row> future:pending){long remaining=deadline-System.nanoTime();if(remaining<=0)throw new TimeoutException("Import budget");Row row=future.get(remaining,TimeUnit.NANOSECONDS);if(!references.add(row.reference))throw new IllegalArgumentException("Duplicate receipt");snapshot.add(row.reference+","+row.units);}
            Path staged=Files.createTempFile(output.getParent(),"snapshot-",".tmp");
            try{Files.write(staged,snapshot,StandardCharsets.UTF_8);Files.move(staged,output,StandardCopyOption.REPLACE_EXISTING);}finally{Files.deleteIfExists(staged);}
        }finally{for(Future<Row> future:pending)future.cancel(true);workers.shutdownNow();if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Import workers alive");}
    }
    public static void main(String[] args)throws Exception{
        Path directory=Files.createTempDirectory("aitrove-import-"),input=directory.resolve("input.csv"),output=directory.resolve("snapshot.csv");
        try{
            Files.write(input,Arrays.asList("R-41,4","R-42,3"),StandardCharsets.UTF_8);importFile(input,output);System.out.println("published="+Files.readAllLines(output).size());
            Files.write(input,Arrays.asList("R-43,2","invalid"),StandardCharsets.UTF_8);
            try{importFile(input,output);}catch(ExecutionException rejected){System.out.println("invalid row rejected");}
            System.out.println("preserved="+Files.readAllLines(output).size());
        }finally{Files.deleteIfExists(input);Files.deleteIfExists(output);Files.deleteIfExists(directory);}
    }
}
