public class ModuleBoundaryInspection {
    public static void main(String[] args) {
        Module platform = String.class.getModule();
        Module application = ModuleBoundaryInspection.class.getModule();
        System.out.println(platform.getName());
        System.out.println(application.isNamed());
        System.out.println(platform.isExported("java.lang"));
        System.out.println(application.canRead(platform));
    }
}
