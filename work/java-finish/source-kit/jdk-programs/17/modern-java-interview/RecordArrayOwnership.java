public class RecordArrayOwnership {
    record ParcelCounts(int[] values){
        ParcelCounts{values=values.clone();}
        public int[] values(){return values.clone();}
    }
    public static void main(String[] args){
        int[] input={2,3};ParcelCounts recorded=new ParcelCounts(input);input[0]=9;
        System.out.println(recorded.values()[0]);
        int[] output=recorded.values();output[0]=8;
        System.out.println(recorded.values()[0]);
        System.out.println(recorded.equals(new ParcelCounts(new int[]{2,3})));
    }
}
