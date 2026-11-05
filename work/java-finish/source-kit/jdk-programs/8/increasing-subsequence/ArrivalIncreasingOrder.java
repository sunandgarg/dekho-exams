public class ArrivalIncreasingOrder {
    static int length(int[] values){
        int[] tails=new int[values.length];int used=0;
        for(int value:values){
            int low=0,high=used;
            while(low<high){int middle=low+(high-low)/2;if(tails[middle]<value)low=middle+1;else high=middle;}
            tails[low]=value;if(low==used)used++;
        }return used;
    }
    public static void main(String[] args){System.out.println(length(new int[]{7,3,5,5,8,1,9}));System.out.println(length(new int[]{4,4,4}));System.out.println(length(new int[0]));}
}
