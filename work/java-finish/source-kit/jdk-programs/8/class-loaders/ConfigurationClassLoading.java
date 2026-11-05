public class ConfigurationClassLoading {
    static class Configuration {
        static { System.out.println("Configuration initialized"); }
    }
    public static void main(String[] args) throws Exception {
        ClassLoader loader = ConfigurationClassLoading.class.getClassLoader();
        String name = "ConfigurationClassLoading$Configuration";
        Class<?> inspected = Class.forName(name, false, loader);
        System.out.println("Inspected without initialization");
        Class<?> initialized = Class.forName(name, true, loader);
        System.out.println(inspected == initialized);
        System.out.println(String.class.getClassLoader() == null);
    }
}
