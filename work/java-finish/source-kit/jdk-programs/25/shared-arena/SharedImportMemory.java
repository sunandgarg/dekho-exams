import java.lang.foreign.*;
public class SharedImportMemory {
    public static void main(String[] args) throws Exception {
        MemorySegment retained;
        try (Arena arena = Arena.ofShared()) {
            retained = arena.allocate(ValueLayout.JAVA_INT);
            Thread worker = new Thread(() -> retained.set(ValueLayout.JAVA_INT, 0, 125));
            worker.start(); worker.join();
            System.out.println(retained.get(ValueLayout.JAVA_INT, 0));
        }
        try { retained.get(ValueLayout.JAVA_INT, 0); }
        catch (IllegalStateException closed) { System.out.println("closed access rejected"); }
    }
}
