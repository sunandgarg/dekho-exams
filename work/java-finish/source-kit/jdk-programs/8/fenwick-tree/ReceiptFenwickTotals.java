public class ReceiptFenwickTotals {
    final long[] sums;long spent;
    ReceiptFenwickTotals(int size){if(size<0||size>1_000_000)throw new IllegalArgumentException("Tree size");sums=new long[size+1];}
    void add(int index,long delta){
        if(index<0||index>=sums.length-1||delta==Long.MIN_VALUE)throw new IllegalArgumentException("Update boundary");
        long cost=Math.abs(delta),budget=Long.MAX_VALUE/4;if(cost>budget-spent)throw new IllegalArgumentException("Magnitude budget");
        spent+=cost;for(int slot=index+1;slot<sums.length;slot+=slot&-slot)sums[slot]+=delta;
    }
    long prefix(int end){if(end<0||end>=sums.length)throw new IllegalArgumentException("Prefix boundary");long total=0;for(int slot=end;slot>0;slot-=slot&-slot)total+=sums[slot];return total;}
    long range(int start,int end){if(start<0||start>end||end>=sums.length)throw new IllegalArgumentException("Range boundary");return prefix(end)-prefix(start);}
    public static void main(String[] args){ReceiptFenwickTotals totals=new ReceiptFenwickTotals(4);totals.add(0,4);totals.add(1,7);totals.add(3,-2);System.out.println(totals.prefix(2));System.out.println(totals.range(1,4));System.out.println(totals.range(2,2));}
}
