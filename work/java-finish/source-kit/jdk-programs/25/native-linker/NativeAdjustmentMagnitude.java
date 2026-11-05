import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;
public class NativeAdjustmentMagnitude {
    static int magnitude(MethodHandle operation,int adjustment) throws Throwable {
        if (adjustment == Integer.MIN_VALUE) throw new IllegalArgumentException("magnitude exceeds signed int");
        return (int) operation.invokeExact(adjustment);
    }
    public static void main(String[] args) throws Throwable {
        Linker linker=Linker.nativeLinker();
        MemoryLayout integer=linker.canonicalLayouts().get("int");
        if (!(integer instanceof ValueLayout.OfInt)) throw new UnsupportedOperationException("C int carrier");
        MethodHandle operation=linker.downcallHandle(linker.defaultLookup().find("abs").orElseThrow(),
            FunctionDescriptor.of(integer,integer));
        System.out.println(magnitude(operation,-125));
        System.out.println(magnitude(operation,0));
        try {magnitude(operation,Integer.MIN_VALUE);}
        catch(IllegalArgumentException rejected){System.out.println("range rejected");}
    }
}
