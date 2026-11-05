# AI Trove Java source kit

These are the exact full source units in the local Java lessons, plus build fixtures. Snippets embedded in paragraphs remain in the tutorials. The manifest lists each JDK program, its declared target release, main class and runtimeFlags. Use a compatible JDK (verification uses Corretto 21 and a task-local checksum-verified Corretto 25).

Compile one source unit at a time into an empty output directory; do not compile the whole source tree as one unnamed package. For example:

    javac --release 8 -d out jdk-programs/8/casts/QuantityConversions.java
    java -cp out QuantityConversions

The native-linker fixture also needs its manifest runtime flag: `java --enable-native-access=ALL-UNNAMED -cp out NativeAdjustmentMagnitude`. This grants native access to the classpath; named-module applications should grant only their intended module. The scalar C call was checked on the local ABI, not every platform.

Java 25 source units require that JDK; compact source files keep their manifest file name and use their instance entrypoint.

The manifest's executable field indicates whether the class contains main. Outputs and input limits are in each lesson. Temporary files and loopback ports are used by the I/O projects; no public server or account is involved.

## Dependencies and checked database boundaries

Install Maven 3, use JDK 21, and run `mvn test` in maven-checks. The pom declares JUnit Jupiter 5.11.0, H2 2.3.232 and HikariCP 5.1.0. Sources include the named assertions and parameterized tests from the tutorials. H2 is a local learning database, not evidence that a production database has identical concurrency or isolation behavior. Maven downloads third-party artifacts under their own licences.

## Named modules

From named-modules, compile its four files (POSIX shell command):

    javac --release 11 --module-source-path src -d out $(find src -name '*.java')
    java --module-path out -m in.aitrove.app/in.aitrove.app.Main

Expected output: quote=150. This kit explicitly exports the API package and declares the consumer's requires clause.

## Gradle multi-project fixture

Install Gradle 8.10.2 and JDK 21. From gradle-multi run `gradle :app:run --console=plain`. The application prints 150. No wrapper binary is bundled. The build declares app's dependency on billing and uses only JDK classes.

## JMH benchmark fixture

Use Maven and JDK 21. From jmh run `mvn package`, then `java -jar target/benchmarks.jar -wi 3 -i 5 -f 3`. The pom declares JMH 1.37 and its annotation processor. Review the lesson before interpreting results. A short runner smoke run checks execution only; it is not a publishable timing comparison.

The explanations and learning programs were written for AI Trove. Java/API facts and third-party dependencies do not become exclusively owned by AI Trove. No third-party dependency binaries are included in this ZIP.

## Package-access and heap-capture checks

Run `python3 verify-boundaries.py --jdk-home /path/to/jdk21` from this kit. It compiles the valid cross-package sources, requires three invalid accesses to fail compilation, and captures a histogram and heap dump from the synthetic JVM it starts. The temporary dump is removed on exit; no other JVM is inspected. Use a full JDK with javac, java and jcmd. A managed machine may restrict attaching even to a process you own.
