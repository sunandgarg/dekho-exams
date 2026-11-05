import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
public class ClaimedReceiptState {
    private volatile int state;
    private static final VarHandle STATE;
    static {
        try { STATE = MethodHandles.lookup().findVarHandle(ClaimedReceiptState.class, "state", int.class); }
        catch (ReflectiveOperationException failure) { throw new ExceptionInInitializerError(failure); }
    }
    public static void main(String[] args) {
        ClaimedReceiptState receipt = new ClaimedReceiptState();
        System.out.println(STATE.compareAndSet(receipt, 0, 1));
        System.out.println(STATE.compareAndSet(receipt, 0, 1));
        System.out.println((int) STATE.getVolatile(receipt));
    }
}
