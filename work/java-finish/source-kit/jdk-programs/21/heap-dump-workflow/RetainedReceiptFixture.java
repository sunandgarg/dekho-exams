import java.util.*;
import java.util.concurrent.*;
public class RetainedReceiptFixture {
    static final List<Entry> retained=new ArrayList<>();
    static final class Entry {final byte[] payload=new byte[1024];}
    public static void main(String[] args)throws Exception{
        for(int i=0;i<50;i++)retained.add(new Entry());
        System.out.println("retained="+retained.size());
        if(args.length==1&&args[0].equals("--inspect")){
            System.out.println("ready");System.out.flush();new CountDownLatch(1).await(30,TimeUnit.SECONDS);
        }
    }
}
