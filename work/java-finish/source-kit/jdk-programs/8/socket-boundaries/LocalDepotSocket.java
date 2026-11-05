import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;
public class LocalDepotSocket {
    public static void main(String[] args) throws Exception {
        ExecutorService peer = Executors.newSingleThreadExecutor();
        try (ServerSocket server = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            server.setSoTimeout(2000);
            Future<?> reply = peer.submit(() -> {
                try (Socket accepted = server.accept()) {
                    accepted.setSoTimeout(2000);
                    BufferedReader input = new BufferedReader(new InputStreamReader(accepted.getInputStream(), StandardCharsets.UTF_8));
                    PrintWriter output = new PrintWriter(new OutputStreamWriter(accepted.getOutputStream(), StandardCharsets.UTF_8), true);
                    if (!"PING".equals(input.readLine())) throw new IOException("Invalid record");
                    output.println("PONG");
                } catch (IOException failure) { throw new UncheckedIOException(failure); }
            });
            try (Socket client = new Socket()) {
                client.connect(new InetSocketAddress(InetAddress.getLoopbackAddress(), server.getLocalPort()), 2000);
                client.setSoTimeout(2000);
                PrintWriter output = new PrintWriter(new OutputStreamWriter(client.getOutputStream(), StandardCharsets.UTF_8), true);
                output.println("PING");
                BufferedReader input = new BufferedReader(new InputStreamReader(client.getInputStream(), StandardCharsets.UTF_8));
                System.out.println(input.readLine());
            }
            reply.get(2, TimeUnit.SECONDS);
        } finally {
            peer.shutdownNow();
            if (!peer.awaitTermination(2, TimeUnit.SECONDS)) throw new IllegalStateException("Peer did not stop");
        }
    }
}
