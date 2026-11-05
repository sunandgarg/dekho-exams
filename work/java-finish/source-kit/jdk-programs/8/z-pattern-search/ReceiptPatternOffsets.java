import java.util.*;
public class ReceiptPatternOffsets {
    static List<Integer> find(String pattern,String text) {
        if(pattern.isEmpty() || pattern.length()>100000 || text.length()>100000)throw new IllegalArgumentException("input bounds");
        int boundary=pattern.length();int[] values=new int[boundary+1+text.length()];
        for(int i=0;i<boundary;i++)values[i]=pattern.charAt(i);values[boundary]=-1;
        for(int i=0;i<text.length();i++)values[boundary+1+i]=text.charAt(i);
        int[] matched=new int[values.length];int left=0,right=0;
        List<Integer> offsets=new ArrayList<>();
        for(int index=1;index<values.length;index++) {
            if(index<right)matched[index]=Math.min(right-index,matched[index-left]);
            while(index+matched[index]<values.length && values[matched[index]]==values[index+matched[index]])matched[index]++;
            if(index+matched[index]>right){left=index;right=index+matched[index];}
            if(index>boundary && matched[index]>=boundary)offsets.add(index-boundary-1);
        }
        return offsets;
    }
    public static void main(String[] args) {
        System.out.println(find("aba","ababa"));System.out.println(find("#","a##"));
        try{find("","receipt");}catch(IllegalArgumentException rejected){System.out.println("empty pattern rejected");}
    }
}
