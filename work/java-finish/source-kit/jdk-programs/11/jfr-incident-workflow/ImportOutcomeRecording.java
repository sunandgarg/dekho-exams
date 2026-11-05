import jdk.jfr.*;
import jdk.jfr.consumer.*;
import java.nio.file.*;
@Name("in.aitrove.ImportOutcome")
class ImportOutcome extends Event {boolean success;int rows;}
public class ImportOutcomeRecording {
    static void importRows(int rows,boolean reject){
        ImportOutcome event=new ImportOutcome();event.begin();
        try{if(reject)throw new IllegalArgumentException("Rejected rows");event.rows=rows;event.success=true;}
        catch(IllegalArgumentException failed){event.success=false;}
        finally{event.end();event.commit();}
    }
    public static void main(String[] args)throws Exception{
        Path file=Files.createTempFile("aitrove-outcomes-",".jfr");
        try(Recording recording=new Recording()){
            recording.enable(ImportOutcome.class).withStackTrace();recording.start();importRows(4,false);importRows(0,true);recording.stop();recording.dump(file);
            int accepted=0,rejected=0;
            try(RecordingFile events=new RecordingFile(file)){
                while(events.hasMoreEvents()){RecordedEvent event=events.readEvent();if(event.getEventType().getName().equals("in.aitrove.ImportOutcome")){if(event.getBoolean("success"))accepted++;else rejected++;}}
            }System.out.println("accepted="+accepted+", rejected="+rejected);
        }finally{Files.deleteIfExists(file);}
    }
}
