import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

public class PluginInspection {
    public static final class ShipmentPlugin {
        public String identifier() { return "shipment-plugin"; }
    }
    public static void main(String[] args) throws ReflectiveOperationException {
        Method identifier = ShipmentPlugin.class.getMethod("identifier");
        try {
            Object result = identifier.invoke(new ShipmentPlugin());
            System.out.println(result);
        } catch (InvocationTargetException failure) {
            throw new IllegalStateException("Plugin failed", failure.getCause());
        }
    }
}
