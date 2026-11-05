public class JobNotifier {
    interface NotificationChannel {
        void send(String message);
    }

    static class ConsoleChannel implements NotificationChannel {
        public void send(String message) {
            System.out.println(message);
        }
    }

    public static void main(String[] args) {
        NotificationChannel channel = new ConsoleChannel();
        channel.send("Job JOB-42 completed");
    }
}
