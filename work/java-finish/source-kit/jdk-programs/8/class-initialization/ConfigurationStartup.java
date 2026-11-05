public class ConfigurationStartup {
    static class Limits {
        static final int FIXED_BATCH = 20;
        static final int LOADED_BATCH = readBatch();
        static int readBatch() {
            System.out.println("Limits initialized");
            return 30;
        }
    }
    public static void main(String[] args) {
        System.out.println("fixed=" + Limits.FIXED_BATCH);
        System.out.println("loaded=" + Limits.LOADED_BATCH);
        System.out.println("again=" + Limits.LOADED_BATCH);
    }
}
