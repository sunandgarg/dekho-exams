"""Extract the exact published source and create isolated build fixtures."""
import html,json,pathlib,re,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]; OUT=ROOT.parent.parent/'outputs'
entries=json.loads((ROOT/'src/data/fixtures.json').read_text()); lookup={e['path']:e for e in entries}
kit=ROOT/'work/java-finish/source-kit';kit.mkdir(parents=True,exist_ok=True)
def write(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.strip()+'\n')
def source(slug):return html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',lookup['java/'+slug]['body'])[1])
manifest=[];seen=set()
for e in entries:
 if not e['path'].startswith('java/'):continue
 for match in re.finditer(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',e['body']):
  text=html.unescape(match[1]); name=re.search(r'public class (\w+)',text)
  if not name and e['data'].get('java_source_file'):name=['',pathlib.Path(e['data']['java_source_file']).stem]
  if not name or text in seen:continue
  seen.add(text);release=e['data'].get('java_release',8);dep=e['data'].get('java_dependency')
  if dep:continue
  package=re.search(r'^package ([\w.]+);',text,re.M)
  relative=pathlib.Path('jdk-programs')/str(release)/(e['path'].split('/')[-1])/(package[1].replace('.','/') if package else '')/(name[1]+'.java')
  write(kit/relative,text)
  manifest.append({'lesson':e['path'],'source':str(relative),'release':release,'main':(package[1]+'.' if package else '')+name[1],'runtimeFlags':e['data'].get('java_runtime_flags',[]),'executable':'public static void main' in text or e['data'].get('java_entrypoint')=='instance'})
# Same dependencies and tests used to validate the earlier Java batch.
checks=ROOT/'work/java-lesson-checks'
for slug in ['jdbc-interview','database-project','jdbc-reference','database-isolation','versioned-migrations','connection-pool']:
 text=source(slug);name=re.search(r'public class (\w+)',text)[1];write(checks/'src/main/java'/(name+'.java'),text)
write(checks/'src/test/java/PackingBoundaryTest.java',source('parameterized-tests'))
methods=[]
for slug in ['jdbc-interview','database-project','jdbc-reference','database-isolation','versioned-migrations','connection-pool']:
 e=lookup['java/'+slug];text=source(slug);name=re.search(r'public class (\w+)',text)[1]
 expected=html.unescape(re.search(r'<h3>Output</h3><pre><code class="language-text">([\s\S]*?)</code></pre>',e['body'])[1])
 methods.append('    @Test void '+name[0].lower()+name[1:]+'() throws Exception {\n        assertEquals('+json.dumps(expected)+', DatabaseLessonsTest.output(() -> '+name+'.main(new String[0])));\n    }')
write(checks/'src/test/java/RemainingDatabaseTest.java','import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.assertEquals;\npublic class RemainingDatabaseTest {\n'+'\n'.join(methods)+'\n}')
for path in [checks/'pom.xml',*sorted((checks/'src').rglob('*.java'))]:
 write(kit/'maven-checks'/path.relative_to(checks),path.read_text())
# Compile two named modules rather than calling the classpath an explicit module.
module_files={
 'src/in.aitrove.quote/module-info.java':'module in.aitrove.quote { exports in.aitrove.quote.api; }',
 'src/in.aitrove.quote/in/aitrove/quote/api/QuoteApi.java':'package in.aitrove.quote.api;\npublic class QuoteApi { public static long amount() { return 150; } }',
 'src/in.aitrove.app/module-info.java':'module in.aitrove.app { requires in.aitrove.quote; }',
 'src/in.aitrove.app/in/aitrove/app/Main.java':'package in.aitrove.app;\nimport in.aitrove.quote.api.QuoteApi;\npublic class Main { public static void main(String[] args) { System.out.println("quote="+QuoteApi.amount()); } }'}
for path,text in module_files.items():write(kit/'named-modules'/path,text)
# Two Gradle projects, built with a locally installed Gradle 8.10.2 distribution.
gradle={
 'settings.gradle':"rootProject.name = 'aitrove-billing'\ninclude 'billing', 'app'",
 'billing/build.gradle':"plugins { id 'java-library' }\njava { toolchain { languageVersion = JavaLanguageVersion.of(21) } }",
 'app/build.gradle':"plugins { id 'application' }\njava { toolchain { languageVersion = JavaLanguageVersion.of(21) } }\ndependencies { implementation project(':billing') }\napplication { mainClass = 'in.aitrove.app.Main' }",
 'billing/src/main/java/in/aitrove/billing/BillingRule.java':source('gradle-build'),
 'app/src/main/java/in/aitrove/app/Main.java':'package in.aitrove.app;\nimport in.aitrove.billing.BillingRule;\npublic class Main { public static void main(String[] args) { System.out.println(BillingRule.total(3, 50)); } }'}
for path,text in gradle.items():write(kit/'gradle-multi'/path,text)
write(kit/'jmh/src/main/java/in/aitrove/bench/MembershipBenchmark.java',source('jmh-benchmarks'))
write(kit/'jmh/pom.xml','''<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion><groupId>in.aitrove</groupId><artifactId>membership-benchmark</artifactId><version>1.0.0</version>
<properties><maven.compiler.release>21</maven.compiler.release><project.build.sourceEncoding>UTF-8</project.build.sourceEncoding></properties>
<dependencies><dependency><groupId>org.openjdk.jmh</groupId><artifactId>jmh-core</artifactId><version>1.37</version></dependency></dependencies>
<build><finalName>benchmarks</finalName><plugins>
<plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-compiler-plugin</artifactId><version>3.13.0</version><configuration><annotationProcessorPaths><path><groupId>org.openjdk.jmh</groupId><artifactId>jmh-generator-annprocess</artifactId><version>1.37</version></path></annotationProcessorPaths></configuration></plugin>
<plugin><groupId>org.apache.maven.plugins</groupId><artifactId>maven-shade-plugin</artifactId><version>3.5.0</version><executions><execution><phase>package</phase><goals><goal>shade</goal></goals><configuration><createDependencyReducedPom>false</createDependencyReducedPom><transformers><transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer"><mainClass>org.openjdk.jmh.Main</mainClass></transformer></transformers></configuration></execution></executions></plugin>
</plugins></build></project>''')
write(kit/'manifest.json',json.dumps(manifest,indent=2))
write(kit/'README.md','''# AI Trove Java source kit

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
''')
files=[p for p in kit.rglob('*') if p.is_file() and not any(part in {'target','build','.gradle','out'} for part in p.relative_to(kit).parts)]
archive=ROOT/'docs/legacy-kits/aitrove-java-source-kit.zip';archive.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for path in sorted(files):z.write(path,'aitrove-java-source-kit/'+str(path.relative_to(kit)))
shutil.copyfile(archive,OUT/archive.name)
print(json.dumps({'programs':len(manifest),'sourceKitFiles':len(files),'zipBytes':archive.stat().st_size}))
