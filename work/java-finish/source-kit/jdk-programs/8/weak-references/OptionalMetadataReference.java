import java.lang.ref.WeakReference;
public class OptionalMetadataReference {
    public static void main(String[] args) {
        String record = new String("parcel-42");
        WeakReference<String> index = new WeakReference<>(record);
        String selected = index.get();
        System.out.println(selected != null ? selected : "absent");
        index.clear();
        System.out.println(index.get() == null);
        System.out.println(record);
    }
}
