public class DeliveryCharge {
    public int chargePaise() {
        return 5000;
    }

    static class PickupCharge extends DeliveryCharge {
        @Override
        public int chargePaise() {
            return 0;
        }
    }

    public static void main(String[] args) {
        DeliveryCharge charge = new PickupCharge();
        System.out.println(charge.chargePaise());
    }
}
