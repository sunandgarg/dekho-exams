public class ReservationBoundaryExercises {
    static final class Stock {
        private int available,reserved;
        Stock(int available){if(available<0)throw new IllegalArgumentException("Negative stock");this.available=available;}
        boolean reserve(int quantity){
            if(quantity<=0)throw new IllegalArgumentException("Positive quantity required");
            if(quantity>available)return false;
            available-=quantity;reserved+=quantity;return true;
        }
        int[] snapshot(){return new int[]{available,reserved};}
    }
    static void require(boolean condition){if(!condition)throw new AssertionError("Boundary failed");}
    public static void main(String[] args){
        Stock stock=new Stock(10);require(stock.reserve(3));
        require(!stock.reserve(20));require(stock.snapshot()[0]==7&&stock.snapshot()[1]==3);
        try{stock.reserve(0);throw new AssertionError("Zero accepted");}catch(IllegalArgumentException expected){ }
        int[] detached=stock.snapshot();detached[0]=99;require(stock.snapshot()[0]==7);
        System.out.println("4 reservation checks passed");
    }
}
