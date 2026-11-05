import java.util.concurrent.*;
public class LostStockUpdateTrace {
    public static void main(String[] args)throws Exception{
        ConcurrentHashMap<String,Integer> stock=new ConcurrentHashMap<>();stock.put("PACK",7);
        ExecutorService pool=Executors.newFixedThreadPool(2);CountDownLatch read=new CountDownLatch(2),publish=new CountDownLatch(1);
        try{
            Callable<Void> broken=()->{int prior=stock.get("PACK");read.countDown();if(!publish.await(2,TimeUnit.SECONDS))throw new IllegalStateException("Publish wait");stock.put("PACK",prior-3);return null;};
            Future<Void> first=pool.submit(broken),second=pool.submit(broken);
            if(!read.await(2,TimeUnit.SECONDS))throw new IllegalStateException("Read wait");publish.countDown();first.get(2,TimeUnit.SECONDS);second.get(2,TimeUnit.SECONDS);System.out.println(stock.get("PACK"));
            stock.put("PACK",7);Runnable corrected=()->stock.compute("PACK",(key,prior)->prior-3);
            Future<?> a=pool.submit(corrected),b=pool.submit(corrected);a.get(2,TimeUnit.SECONDS);b.get(2,TimeUnit.SECONDS);System.out.println(stock.get("PACK"));
        }finally{publish.countDown();pool.shutdownNow();if(!pool.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Workers alive");}
    }
}
