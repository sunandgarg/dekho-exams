package in.aitrove.billing;
public class BillingRule {
    public static long total(int quantity,long unitCents){
        if(quantity<0||unitCents<0)throw new IllegalArgumentException("Negative billing input");
        return Math.multiplyExact((long)quantity,unitCents);
    }
    public static void main(String[] args){System.out.println(total(3,50));}
}
