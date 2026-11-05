import java.util.Scanner;
public class DepotIntake {
    static int parcelCount(String line) {
        int count = Integer.parseInt(line.trim());
        if (count < 1 || count > 500) {
            throw new IllegalArgumentException("Parcel count outside 1..500");
        }
        return count;
    }
    public static void main(String[] args) {
        try (Scanner input = new Scanner("6\nPune Central Depot\n")) {
            int count = parcelCount(input.nextLine());
            String destination = input.nextLine().trim();
            if (destination.isEmpty()) throw new IllegalArgumentException("Destination required");
            System.out.println(count + " parcels -> " + destination);
        }
        try {
            parcelCount("-4");
        } catch (IllegalArgumentException rejected) {
            System.out.println("Rejected count");
        }
    }
}
