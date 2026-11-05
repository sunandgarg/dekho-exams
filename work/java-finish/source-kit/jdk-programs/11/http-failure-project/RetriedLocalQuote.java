import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class RetriedLocalQuote {
    static String fetch(HttpClient client,URI uri,Duration budget)throws Exception{
        long deadline=System.nanoTime()+budget.toNanos();
        for(int attempt=0;attempt<3;attempt++){
            long remaining=deadline-System.nanoTime();if(remaining<=0)throw new TimeoutException("Quote budget");
            HttpRequest request=HttpRequest.newBuilder(uri).timeout(Duration.ofNanos(remaining)).GET().build();
            HttpResponse<String> response=client.send(request,HttpResponse.BodyHandlers.ofString());
            if(response.statusCode()==200)return response.body();if(response.statusCode()!=503)throw new IllegalStateException("Unexpected HTTP status");
        }throw new IllegalStateException("Attempt limit");
    }
    public static void main(String[] args)throws Exception{
        AtomicInteger calls=new AtomicInteger();HttpServer server=HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);ExecutorService handlers=Executors.newSingleThreadExecutor();server.setExecutor(handlers);
        server.createContext("/quote",exchange->{int attempt=calls.incrementAndGet();byte[] body=(attempt==1?"busy":"quote=150").getBytes(StandardCharsets.UTF_8);exchange.sendResponseHeaders(attempt==1?503:200,body.length);try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}});server.start();
        try{
            URI uri=new URI("http",null,server.getAddress().getAddress().getHostAddress(),server.getAddress().getPort(),"/quote",null,null);
            HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(1)).build();System.out.println(fetch(client,uri,Duration.ofSeconds(2)));System.out.println("attempts="+calls.get());
        }finally{server.stop(0);handlers.shutdownNow();if(!handlers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("Server worker");}
    }
}
