import module java.base;
public class ModuleImportedReceipts {
    public static void main(String[] args){
        List<String> references=List.of("R-23","R-11","R-23");
        Set<String> unique=new TreeSet<>(references);
        System.out.println(unique);
        System.out.println(LocalDate.of(2026,9,29));
    }
}
