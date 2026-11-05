import java.util.Arrays;
import java.util.Comparator;
public class LoadingBayIntervals {
    static int maximumCount(int[][] input){
        int[][] jobs=new int[input.length][2];
        for(int i=0;i<input.length;i++){
            if(input[i]==null||input[i].length!=2||input[i][0]>=input[i][1])throw new IllegalArgumentException("Invalid interval");
            jobs[i]=input[i].clone();
        }
        Arrays.sort(jobs,Comparator.comparingInt(job->job[1]));
        int finish=Integer.MIN_VALUE,accepted=0;
        for(int[] job:jobs)if(job[0]>=finish){accepted++;finish=job[1];}
        return accepted;
    }
    public static void main(String[] args){
        System.out.println(maximumCount(new int[][]{{1,4},{3,5},{0,2},{5,7},{2,3}}));
        System.out.println(maximumCount(new int[0][2]));
    }
}
