import com.sun.net.httpserver.*;
import javax.net.ssl.*;
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.security.KeyStore;
import java.time.Duration;
import java.util.concurrent.*;
public class LocalTlsIdentity {
    public static void main(String[] args)throws Exception{
        Path directory=Files.createTempDirectory("aitrove-tls-"),store=directory.resolve("fixture.p12"),log=directory.resolve("keytool.log");char[] password="fixture-only".toCharArray();
        HttpsServer server=null;ExecutorService handlers=Executors.newSingleThreadExecutor();
        try{
            String keytool=Path.of(System.getProperty("java.home"),"bin","keytool").toString();
            Process creation=new ProcessBuilder(keytool,"-genkeypair","-alias","server","-keyalg","RSA","-keysize","2048","-storetype","PKCS12","-keystore",store.toString(),"-storepass",new String(password),"-dname","CN=localhost","-ext","SAN=dns:localhost","-validity","2","-noprompt").redirectErrorStream(true).redirectOutput(log.toFile()).start();
            if(!creation.waitFor(10,TimeUnit.SECONDS)){creation.destroyForcibly();throw new IllegalStateException("Key creation timeout");}if(creation.exitValue()!=0)throw new IllegalStateException("Key creation failed");
            KeyStore keys=KeyStore.getInstance("PKCS12");try(java.io.InputStream input=Files.newInputStream(store)){keys.load(input,password);}
            KeyManagerFactory keyManagers=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());keyManagers.init(keys,password);
            SSLContext serverContext=SSLContext.getInstance("TLS");serverContext.init(keyManagers.getKeyManagers(),null,null);
            KeyStore trusted=KeyStore.getInstance("PKCS12");trusted.load(null,null);trusted.setCertificateEntry("fixture",keys.getCertificate("server"));
            TrustManagerFactory trustManagers=TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());trustManagers.init(trusted);
            SSLContext clientContext=SSLContext.getInstance("TLS");clientContext.init(null,trustManagers.getTrustManagers(),null);
            server=HttpsServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(),0),0);server.setHttpsConfigurator(new HttpsConfigurator(serverContext));server.setExecutor(handlers);
            server.createContext("/receipt",exchange->{byte[] body="tls=verified".getBytes(java.nio.charset.StandardCharsets.UTF_8);exchange.sendResponseHeaders(200,body.length);try(java.io.OutputStream output=exchange.getResponseBody()){output.write(body);}});server.start();
            HttpClient client=HttpClient.newBuilder().sslContext(clientContext).connectTimeout(Duration.ofSeconds(2)).build();int port=server.getAddress().getPort();
            HttpRequest valid=HttpRequest.newBuilder(new URI("https",null,"localhost",port,"/receipt",null,null)).timeout(Duration.ofSeconds(3)).GET().build();
            System.out.println(client.send(valid,HttpResponse.BodyHandlers.ofString()).body());
            HttpRequest invalid=HttpRequest.newBuilder(new URI("https",null,server.getAddress().getAddress().getHostAddress(),port,"/receipt",null,null)).timeout(Duration.ofSeconds(3)).GET().build();
            try{client.send(invalid,HttpResponse.BodyHandlers.ofString());throw new IllegalStateException("Wrong hostname accepted");}
            catch(SSLHandshakeException rejected){System.out.println("hostname rejected");}
        }finally{
            if(server!=null)server.stop(0);handlers.shutdownNow();if(!handlers.awaitTermination(2,TimeUnit.SECONDS))throw new IllegalStateException("TLS worker");
            Files.deleteIfExists(store);Files.deleteIfExists(log);Files.deleteIfExists(directory);
        }
    }
}
