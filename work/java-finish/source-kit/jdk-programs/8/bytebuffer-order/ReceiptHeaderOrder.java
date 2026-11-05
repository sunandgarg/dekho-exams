import java.nio.*;
public class ReceiptHeaderOrder {
    static int read(byte[] header) {
        if(header.length!=4)throw new IllegalArgumentException("four-byte header required");
        return ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt();
    }
    public static void main(String[] args) {
        byte[] bytes={1,0,0,0};ByteBuffer original=ByteBuffer.wrap(bytes);
        ByteBuffer view=original.duplicate();original.order(ByteOrder.LITTLE_ENDIAN);
        System.out.println(original.getInt());System.out.println(view.getInt());System.out.println(read(bytes));
        try{read(new byte[3]);}catch(IllegalArgumentException rejected){System.out.println("length rejected");}
    }
}
