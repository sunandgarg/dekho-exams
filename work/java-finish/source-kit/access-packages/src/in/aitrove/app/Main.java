package in.aitrove.app;
import in.aitrove.adapter.DeliveryQuantity;
public class Main {public static void main(String[] args){DeliveryQuantity quantity=new DeliveryQuantity();System.out.println(quantity.readOwn());System.out.println(quantity.readCompatible(quantity));}}
