public class ReportRequestScope {
    private static final ScopedValue<String> REQUEST=ScopedValue.newInstance();
    public static void main(String[] args)throws Exception{
        ScopedValue.where(REQUEST,"REQ-51").call(()->{
            System.out.println(REQUEST.get());
            try{ScopedValue.where(REQUEST,"AUDIT-51").run(()->{throw new IllegalStateException("audit failed");});}
            catch(IllegalStateException failed){System.out.println(REQUEST.get());}
            Thread child=Thread.ofVirtual().start(()->System.out.println(REQUEST.isBound()));
            child.join();return null;
        });
        System.out.println(REQUEST.isBound());
    }
}
