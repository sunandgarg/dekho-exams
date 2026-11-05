import java.util.Deque;
import java.util.LinkedList;
public class TaskDequeCommands {
    final Deque<String> pending=new LinkedList<>();
    String execute(String line){
        if(line==null||line.trim().isEmpty())throw new IllegalArgumentException("Missing command");
        String[] parts=line.trim().split("\\s+",2);String command=parts[0];String argument=parts.length==2?parts[1].trim():"";
        if(command.equals("add")||command.equals("urgent")){
            if(argument.isEmpty())throw new IllegalArgumentException("Missing task");
            if(command.equals("add"))pending.addLast(argument);else pending.addFirst(argument);
            return "accepted";
        }
        if(!argument.isEmpty())throw new IllegalArgumentException("Unexpected argument");
        if(command.equals("next")){String task=pending.pollFirst();return task==null?"empty":task;}
        if(command.equals("list"))return pending.toString();
        throw new IllegalArgumentException("Unknown command");
    }
    public static void main(String[] args){
        TaskDequeCommands queue=new TaskDequeCommands();
        queue.execute("add Audit stock");queue.execute("add Print label");queue.execute("urgent Verify address");
        System.out.println(queue.execute("list"));System.out.println(queue.execute("next"));
        System.out.println(queue.execute("list"));
        try{queue.execute("add");}catch(IllegalArgumentException rejected){System.out.println("Empty task rejected");}
    }
}
