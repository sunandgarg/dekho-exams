import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

public class ServiceLabels {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE)
    @interface ServiceLabel { String value(); }
    @ServiceLabel("shipment-index")
    static final class ShipmentIndex { }
    public static void main(String[] args) {
        ServiceLabel label = ShipmentIndex.class.getAnnotation(ServiceLabel.class);
        System.out.println(label == null ? "unlabelled" : label.value());
    }
}
