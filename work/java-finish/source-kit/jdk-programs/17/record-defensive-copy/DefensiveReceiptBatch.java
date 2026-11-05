public class DefensiveReceiptBatch {
    record Batch(int[] amounts) {
        Batch {amounts=amounts.clone();}
        public int[] amounts(){return amounts.clone();}
    }
    public static void main(String[] args) {
        int[] input={125,75};Batch batch=new Batch(input);input[0]=0;
        int[] output=batch.amounts();output[1]=0;
        System.out.println(batch.amounts()[0]);System.out.println(batch.amounts()[1]);
        System.out.println(batch.equals(new Batch(new int[]{125,75})));
    }
}
