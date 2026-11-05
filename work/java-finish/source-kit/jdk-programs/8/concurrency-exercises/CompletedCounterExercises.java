import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class CompletedCounterExercises {
    public static void main(String[] args) throws Exception {
        ExecutorService workers=Executors.newFixedThreadPool(4);AtomicInteger completed=new AtomicInteger();
        List<Future<?>> tasks=new ArrayList<>();
        try{
            for(int batch=0;batch<20;batch++)tasks.add(workers.submit(()->{
                for(int item=0;item<10;item++)completed.incrementAndGet();
            }));
            for(Future<?> task:tasks)task.get(2,TimeUnit.SECONDS);
            if(completed.get()!=200)throw new AssertionError("Lost work");
            System.out.println("completed="+completed.get());
        }finally{
            workers.shutdownNow();
            if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new AssertionError("Workers retained");
        }
    }
}
