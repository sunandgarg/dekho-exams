import java.text.BreakIterator;
import java.util.Locale;
public class ReceiptLabelClusters {
    static String prefix(String text,int limit){
        if(limit<0)throw new IllegalArgumentException("Negative cluster limit");
        java.util.Objects.requireNonNull(text);
        BreakIterator boundaries=BreakIterator.getCharacterInstance(Locale.ROOT);
        boundaries.setText(text);int end=boundaries.first();
        for(int count=0;count<limit;count++){
            int next=boundaries.next();if(next==BreakIterator.DONE)return text;end=next;
        }
        return text.substring(0,end);
    }
    public static void main(String[] args){
        String label="e\u0301clair";
        System.out.println(prefix(label,1).length());
        System.out.println(prefix("\ud83d\ude00X",1).length());
        System.out.println(prefix(label,0).isEmpty());
        System.out.println(prefix(label,20).equals(label));
    }
}
