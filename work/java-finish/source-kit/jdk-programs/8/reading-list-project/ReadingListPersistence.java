import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public class ReadingListPersistence {
    final List<String> titles=new ArrayList<>();
    void add(String title){
        if(title==null||title.trim().isEmpty()||title.indexOf('\n')>=0||title.indexOf('\r')>=0)throw new IllegalArgumentException("Single nonempty title required");
        if(titles.size()==10000)throw new IllegalArgumentException("Title budget exhausted");
        titles.add(title.trim());
    }
    List<String> snapshot(){return Collections.unmodifiableList(new ArrayList<>(titles));}
    void remove(int index){titles.remove(index);}
    void save(Path destination) throws Exception {
        Path absolute=destination.toAbsolutePath();Path staged=Files.createTempFile(absolute.getParent(),"reading-stage-",".txt");
        try{
            byte[] snapshot=String.join("\n",titles).getBytes(StandardCharsets.UTF_8);
            if(snapshot.length>2_000_000)throw new IllegalArgumentException("Snapshot budget exhausted");
            Files.write(staged,snapshot);
            Files.move(staged,absolute,StandardCopyOption.REPLACE_EXISTING);
        }finally{Files.deleteIfExists(staged);}
    }
    static ReadingListPersistence load(Path source) throws Exception {
        if(Files.size(source)>2_000_000)throw new IllegalArgumentException("File budget exhausted");
        ReadingListPersistence restored=new ReadingListPersistence();
        for(String title:Files.readAllLines(source,StandardCharsets.UTF_8))restored.add(title);
        return restored;
    }
    public static void main(String[] args) throws Exception {
        Path directory=Files.createTempDirectory("aitrove-reading-");Path file=directory.resolve("titles.txt");
        try{
            ReadingListPersistence original=new ReadingListPersistence();
            original.add("Concurrency notes");original.add("Collections handbook");original.save(file);
            ReadingListPersistence restored=load(file);System.out.println(restored.snapshot());
            restored.remove(0);System.out.println(restored.snapshot());System.out.println("saved="+load(file).snapshot().size());
        }finally{Files.deleteIfExists(file);Files.deleteIfExists(directory);}
    }
}
