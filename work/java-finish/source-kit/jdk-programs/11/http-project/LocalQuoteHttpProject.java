import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;
public class LocalQuoteHttpProject {
    public static void main(String[] args) throws Exception {
        HttpServer server=HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);
        ExecutorService workers=Executors.newSingleThreadExecutor();server.setExecutor(workers);
        server.createContext("/quote",exchange->{
            byte[] body="quote=150".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("Content-Type","text/plain; charset=utf-8");
            exchange.sendResponseHeaders(200,body.length);
            try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}
            finally{exchange.close();}
        });
        server.start();
        try{
            String host=server.getAddress().getAddress().getHostAddress();int port=server.getAddress().getPort();
            HttpClient client=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).followRedirects(HttpClient.Redirect.NEVER).build();
            URI quote=new URI("http",null,host,port,"/quote",null,null);
            HttpRequest request=HttpRequest.newBuilder(quote).timeout(Duration.ofSeconds(2)).GET().build();
            HttpResponse<String> response=client.send(request,HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            System.out.println(response.statusCode()+":"+response.body());
            URI missing=new URI("http",null,host,port,"/missing",null,null);
            System.out.println(client.send(HttpRequest.newBuilder(missing).timeout(Duration.ofSeconds(2)).build(),HttpResponse.BodyHandlers.discarding()).statusCode());
        }finally{
            server.stop(0);workers.shutdownNow();
            if(!workers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("HTTP workers retained");
        }
    }
}
