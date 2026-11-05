public class ReceiptLabelDistance {
    static int distance(String a,String b){
        java.util.Objects.requireNonNull(a);java.util.Objects.requireNonNull(b);
        if((long)a.length()*b.length()>4_000_000)throw new IllegalArgumentException("Distance work budget");
        if(a.length()<b.length()){String swap=a;a=b;b=swap;}
        int[] previous=new int[b.length()+1],current=new int[b.length()+1];for(int j=0;j<previous.length;j++)previous[j]=j;
        for(int i=1;i<=a.length();i++){
            current[0]=i;for(int j=1;j<=b.length();j++)current[j]=Math.min(Math.min(previous[j]+1,current[j-1]+1),previous[j-1]+(a.charAt(i-1)==b.charAt(j-1)?0:1));
            int[] swap=previous;previous=current;current=swap;
        }return previous[b.length()];
    }
    public static void main(String[] args){System.out.println(distance("parcel","parcels"));System.out.println(distance("label","table"));System.out.println(distance("","PK"));}
}
