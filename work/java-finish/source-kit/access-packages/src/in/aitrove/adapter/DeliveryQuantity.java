package in.aitrove.adapter;
import in.aitrove.base.Quantity;
public class DeliveryQuantity extends Quantity {public int readOwn(){return units;} public int readCompatible(DeliveryQuantity other){return other.units;}}
