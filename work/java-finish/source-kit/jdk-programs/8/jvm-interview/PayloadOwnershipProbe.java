import java.util.Arrays;
public class PayloadOwnershipProbe {
    static final class StoredPayload {
        private final byte[] bytes;
        StoredPayload(byte[] input){bytes=input.clone();}
        byte[] snapshot(){return bytes.clone();}
    }
    public static void main(String[] args){
        byte[] incoming={1,2};StoredPayload stored=new StoredPayload(incoming);
        incoming[0]=9;
        byte[] first=stored.snapshot();first[1]=8;
        System.out.println(Arrays.toString(stored.snapshot()));
        System.out.println(Arrays.toString(incoming));
    }
}
