public class SensorAverage {
    public static void main(String[] args) {
        Integer[] readings = {120, null, 180};
        long total = 0;
        int present = 0;
        for (Integer reading : readings) {
            if (reading != null) {
                total += reading;
                present++;
            }
        }
        if (present == 0) {
            System.out.println("No readings");
        } else {
            System.out.println("mean=" + total / present);
        }
        System.out.println("present=" + present);
    }
}
