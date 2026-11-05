import java.util.*;
public class MonitoredVirtualReceipts {
    final Object monitor=new Object();int accepted;
    void accept(){synchronized(monitor){accepted++;}}
    public static void main(String[] args)throws Exception{
        MonitoredVirtualReceipts service=new MonitoredVirtualReceipts();List<Thread> workers=new ArrayList<>();
        for(int i=0;i<40;i++)workers.add(Thread.ofVirtual().start(service::accept));
        for(Thread worker:workers)worker.join();
        System.out.println(service.accepted);
    }
}
