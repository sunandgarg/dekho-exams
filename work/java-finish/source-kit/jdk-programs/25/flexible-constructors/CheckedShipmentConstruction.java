public class CheckedShipmentConstruction {
    static class Quantity { final int units;Quantity(int units){this.units=units;} }
    static class Shipment extends Quantity {
        Shipment(long requested){
            if(requested<0)throw new IllegalArgumentException("Negative shipment");
            int validated=Math.toIntExact(requested);
            super(validated);
        }
    }
    public static void main(String[] args){
        System.out.println(new Shipment(9).units);
        try{new Shipment(-1);}catch(IllegalArgumentException rejected){System.out.println("negative rejected");}
        try{new Shipment(3_000_000_000L);}catch(ArithmeticException rejected){System.out.println("range rejected");}
    }
}
