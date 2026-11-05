import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class ImportCompletionCount {
    public static void main(String[] args) throws Exception {
        CountDownLatch completed=new CountDownLatch(2);
        AtomicInteger accepted=new AtomicInteger(),failed=new AtomicInteger();
        Thread first=new Thread(()->{try{accepted.incrementAndGet();}finally{completed.countDown();}});
        Thread second=new Thread(()->{try{throw new IllegalStateException("bad record");}
            catch(IllegalStateException failure){failed.incrementAndGet();}finally{completed.countDown();}});
        first.start();second.start();completed.await();first.join();second.join();
        System.out.println("accepted="+accepted.get());System.out.println("failed="+failed.get());
        System.out.println("remaining="+completed.getCount());
    }
}
