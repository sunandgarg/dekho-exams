import java.text.Collator;
import java.util.*;
public class CustomerDirectoryOrder {
    public static void main(String[] args){
        Collator french=Collator.getInstance(Locale.FRENCH);french.setStrength(Collator.PRIMARY);
        String first="cote",second="c\u00f4te";
        TreeSet<String> grouped=new TreeSet<>((a,b)->french.compare(a,b));
        grouped.add(first);grouped.add(second);
        Comparator<String> distinct=(a,b)->{int compared=french.compare(a,b);return compared!=0?compared:a.compareTo(b);};
        TreeSet<String> labels=new TreeSet<>(distinct);labels.add(first);labels.add(second);
        System.out.println(french.compare(first,second)==0);
        System.out.println(grouped.size());System.out.println(labels.size());
    }
}
