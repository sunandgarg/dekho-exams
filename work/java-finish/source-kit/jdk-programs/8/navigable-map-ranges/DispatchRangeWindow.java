import java.util.*;
public class DispatchRangeWindow {
    public static void main(String[] args) {
        NavigableMap<Integer,String> ledger=new TreeMap<>();
        ledger.put(10,"queued");ledger.put(20,"review");ledger.put(30,"sent");
        NavigableMap<Integer,String> window=ledger.subMap(10,true,30,false);
        NavigableMap<Integer,String> snapshot=new TreeMap<>(window);
        window.put(20,"approved");ledger.put(25,"packed");
        System.out.println(window);System.out.println(snapshot);System.out.println(ledger.floorEntry(24).getKey());
        try{window.put(40,"outside");}catch(IllegalArgumentException rejected){System.out.println("range rejected");}
    }
}
