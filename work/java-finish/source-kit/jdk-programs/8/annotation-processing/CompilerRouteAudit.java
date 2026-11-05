import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.net.URI;
import java.util.Collections;
import java.util.Set;
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.RoundEnvironment;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.TypeElement;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
public class CompilerRouteAudit {
    @Target(ElementType.TYPE) @Retention(RetentionPolicy.SOURCE)
    public @interface Route { String value(); }
    static class RouteProcessor extends AbstractProcessor {
        public Set<String> getSupportedAnnotationTypes() { return Collections.singleton(Route.class.getCanonicalName()); }
        public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment round) {
            for (javax.lang.model.element.Element endpoint : round.getElementsAnnotatedWith(Route.class))
                if (!endpoint.getAnnotation(Route.class).value().startsWith("/"))
                    processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, "Route must start with a slash", endpoint);
            return true;
        }
    }
    static boolean check(String path) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("Full JDK required");
        String text = "@CompilerRouteAudit.Route(\""+path+"\") class ReceiptEndpoint {}";
        JavaFileObject unit = new SimpleJavaFileObject(URI.create("string:///ReceiptEndpoint.java"), JavaFileObject.Kind.SOURCE) {
            public CharSequence getCharContent(boolean ignoreErrors) { return text; }
        };
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavaCompiler.CompilationTask task = compiler.getTask(null, files, diagnostics,
                java.util.Arrays.asList("-proc:only", "-classpath", System.getProperty("java.class.path")),
                null, Collections.singletonList(unit));
            task.setProcessors(Collections.singletonList(new RouteProcessor()));
            return task.call();
        }
    }
    public static void main(String[] args) throws Exception {
        System.out.println(check("/receipts")); System.out.println(check("receipts"));
    }
}
