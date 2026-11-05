public class ManifestCommonOrder {
    static int length(String a,String b){
        java.util.Objects.requireNonNull(a);java.util.Objects.requireNonNull(b);
        if((long)a.length()*b.length()>4_000_000)throw new IllegalArgumentException("Subsequence work budget");
        if(a.length()<b.length()){String swap=a;a=b;b=swap;}int[] row=new int[b.length()+1];
        for(int i=0;i<a.length();i++){
            int diagonal=0;
            for(int j=1;j<row.length;j++){int old=row[j];row[j]=a.charAt(i)==b.charAt(j-1)?diagonal+1:Math.max(row[j],row[j-1]);diagonal=old;}
        }return row[b.length()];
    }
    public static void main(String[] args){System.out.println(length("PKRSL","PRL"));System.out.println(length("ABC","XYZ"));System.out.println(length("","PK"));}
}
