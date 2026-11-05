import java.util.*;
import java.util.concurrent.locks.ReentrantLock;
public class StockReservationBoundary {
    final ReentrantLock lock=new ReentrantLock();final Map<String,Integer> stock=new HashMap<>(),reserved=new HashMap<>();
    StockReservationBoundary(){stock.put("PACK",7);}
    boolean reserve(String reference,int units){
        if(reference==null||reference.isEmpty()||units<=0)throw new IllegalArgumentException("Reservation input");
        lock.lock();try{
            if(reserved.containsKey(reference)||stock.get("PACK")<units)return false;
            stock.put("PACK",stock.get("PACK")-units);reserved.put(reference,units);return true;
        }finally{lock.unlock();}
    }
    String status(){lock.lock();try{return "stock="+stock.get("PACK")+", reservations="+reserved.size();}finally{lock.unlock();}}
    public static void main(String[] args){StockReservationBoundary service=new StockReservationBoundary();System.out.println(service.reserve("R-71",8));System.out.println(service.status());System.out.println(service.reserve("R-71",3));System.out.println(service.status());}
}
