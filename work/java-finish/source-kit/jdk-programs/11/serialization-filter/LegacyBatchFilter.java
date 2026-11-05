import java.io.*;
public class LegacyBatchFilter {
    static byte[] encode(Object value) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) { out.writeObject(value); }
        return bytes.toByteArray();
    }
    static int[] read(byte[] bytes) throws Exception {
        if (bytes.length > 1024) throw new IOException("byte limit");
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            in.setObjectInputFilter(info -> {
                if (info.depth() > 2 || info.references() > 8 || info.streamBytes() > 1024 || info.arrayLength() > 4)
                    return ObjectInputFilter.Status.REJECTED;
                Class<?> type = info.serialClass();
                return type == null ? ObjectInputFilter.Status.UNDECIDED
                    : type == int[].class ? ObjectInputFilter.Status.ALLOWED : ObjectInputFilter.Status.REJECTED;
            });
            Object value = in.readObject();
            if (!(value instanceof int[])) throw new IOException("root type");
            return (int[]) value;
        }
    }
    public static void main(String[] args) throws Exception {
        System.out.println(read(encode(new int[]{12, 18})).length);
        try { read(encode(new int[5])); }
        catch (InvalidClassException rejected) { System.out.println("length rejected"); }
        try { read(encode(new long[]{12})); }
        catch (InvalidClassException rejected) { System.out.println("class rejected"); }
    }
}
