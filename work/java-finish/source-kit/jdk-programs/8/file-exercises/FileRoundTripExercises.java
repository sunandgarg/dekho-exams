import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public class FileRoundTripExercises {
    public static void main(String[] args) throws Exception {
        Path directory=Files.createTempDirectory("aitrove-file-check-");Path file=directory.resolve("titles.txt");
        try{
            List<String> expected=Arrays.asList("Caf\u00e9 notes","Parcel handbook");
            Files.write(file,expected,StandardCharsets.UTF_8);
            if(!Files.readAllLines(file,StandardCharsets.UTF_8).equals(expected))throw new AssertionError("Round trip changed");
            try{Files.readAllLines(directory.resolve("missing.txt"),StandardCharsets.UTF_8);throw new AssertionError("Missing file accepted");}
            catch(IOException rejected){ }
            Files.delete(file);if(Files.exists(file))throw new AssertionError("File retained");
            System.out.println("3 file checks passed");
        }finally{Files.deleteIfExists(file);Files.deleteIfExists(directory);}
    }
}
