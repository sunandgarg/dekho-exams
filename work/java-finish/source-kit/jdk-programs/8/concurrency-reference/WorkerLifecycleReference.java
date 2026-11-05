import java.util.concurrent.*;
public class WorkerLifecycleReference {
    public static void main(String[] args) throws Exception {
        ExecutorService owner=Executors.newSingleThreadExecutor();
        try{
            Future<Integer> task=owner.submit(()->42);
            System.out.println("result="+task.get(2,TimeUnit.SECONDS));
            owner.shutdown();
            try{owner.submit(()->43);}catch(RejectedExecutionException rejected){System.out.println("Admission closed");}
        }finally{
            owner.shutdownNow();
            if(!owner.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Owner did not close");
        }
    }
}
