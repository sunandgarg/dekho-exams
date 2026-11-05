import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
public class NativeReceiptBlock {
    public static void main(String[] args) {
        MemorySegment receipt;
        try (Arena arena = Arena.ofConfined()) {
            receipt = arena.allocate(8, 4);
            receipt.set(ValueLayout.JAVA_INT, 0, 17);
            receipt.set(ValueLayout.JAVA_INT, 4, 29);
            System.out.println(receipt.get(ValueLayout.JAVA_INT, 0));
            try { receipt.get(ValueLayout.JAVA_INT, 8); }
            catch (IndexOutOfBoundsException rejected) { System.out.println("bounds rejected"); }
        }
        try { receipt.get(ValueLayout.JAVA_INT, 0); }
        catch (IllegalStateException rejected) { System.out.println("closed rejected"); }
    }
}
