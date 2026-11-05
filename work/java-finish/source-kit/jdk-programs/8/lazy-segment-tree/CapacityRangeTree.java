public class CapacityRangeTree {
    private final int count;
    private final long[] sums, pending;
    CapacityRangeTree(long[] values) {
        if (values.length == 0 || values.length > 100000) throw new IllegalArgumentException("size");
        count = values.length; sums = new long[4 * count]; pending = new long[4 * count];
        build(1, 0, count, values);
    }
    private void build(int node, int left, int right, long[] values) {
        if (right-left == 1) { sums[node] = values[left]; return; }
        int middle = left + (right-left)/2;
        build(node*2,left,middle,values); build(node*2+1,middle,right,values);
        sums[node] = sums[node*2] + sums[node*2+1];
    }
    private void apply(int node,int length,long delta) { sums[node] += delta * length; pending[node] += delta; }
    private void push(int node,int left,int right) {
        int middle = left + (right-left)/2;
        apply(node*2,middle-left,pending[node]); apply(node*2+1,right-middle,pending[node]); pending[node]=0;
    }
    private void bounds(int left,int right) {
        if (left<0 || right>count || left>=right) throw new IllegalArgumentException("range");
    }
    void add(int left,int right,long delta) { bounds(left,right); add(1,0,count,left,right,delta); }
    private void add(int node,int left,int right,int from,int until,long delta) {
        if (until<=left || right<=from) return;
        if (from<=left && right<=until) { apply(node,right-left,delta); return; }
        push(node,left,right); int middle=left+(right-left)/2;
        add(node*2,left,middle,from,until,delta); add(node*2+1,middle,right,from,until,delta);
        sums[node]=sums[node*2]+sums[node*2+1];
    }
    long sum(int left,int right) { bounds(left,right); return sum(1,0,count,left,right); }
    private long sum(int node,int left,int right,int from,int until) {
        if (until<=left || right<=from) return 0;
        if (from<=left && right<=until) return sums[node];
        push(node,left,right); int middle=left+(right-left)/2;
        return sum(node*2,left,middle,from,until)+sum(node*2+1,middle,right,from,until);
    }
    public static void main(String[] args) {
        CapacityRangeTree ledger=new CapacityRangeTree(new long[]{10,20,30,40});
        ledger.add(1,4,5); System.out.println(ledger.sum(0,4));
        ledger.add(0,2,-3); System.out.println(ledger.sum(1,3));
        try { ledger.sum(2,2); } catch (IllegalArgumentException rejected) { System.out.println("empty range rejected"); }
    }
}
