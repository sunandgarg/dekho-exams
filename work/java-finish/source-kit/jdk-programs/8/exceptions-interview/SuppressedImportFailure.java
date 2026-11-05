import java.io.IOException;
public class SuppressedImportFailure {
    static final class InputHandle implements AutoCloseable {
        public void close() throws IOException { throw new IOException("close failed"); }
    }
    public static void main(String[] args){
        try(InputHandle input=new InputHandle()){
            throw new IllegalStateException("parse failed");
        }catch(Exception failure){
            System.out.println(failure.getMessage());
            System.out.println(failure.getSuppressed()[0].getMessage());
        }
    }
}
