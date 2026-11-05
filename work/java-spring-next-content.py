"""Append original checked lessons without rewriting earlier batches."""
import copy,datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]; FILE=ROOT/'src/data/fixtures.json'
es=json.loads(FILE.read_text()); lookup={e['path']:e for e in es}; stamp=datetime.datetime.now(datetime.UTC).isoformat(); added=[]
def para(text):
 return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',html.escape(text))+'</p>'
def code(text,lang='java'):return '<pre><code class="language-'+lang+'">'+html.escape(text.strip(),quote=False)+'</code></pre>'
def put(slug,title,definition,sections,source,output,cost,mistakes,related,subject='java-advanced',release=8,spring=False,proof=''):
 path=('spring/' if spring else 'java/')+slug
 body=para(definition)
 body+=para('The downloadable Spring source kit pins Java 21 and Spring Boot 4.0.8 with its managed dependencies. Run mvn test to check the named fixture.' if spring else 'This complete program targets Java '+str(release)+'. Its displayed output is checked by the tutorial validation script.')
 for heading,paragraphs in sections: body+='<h2>'+heading+'</h2>'+''.join(para(p) for p in paragraphs)
 body+='<h2>'+('Checked source' if spring else 'Working program')+'</h2>'+code(source)
 if spring:body+='<h2>Test the boundary</h2>'+para(proof+' checks this contract in the source kit. Excerpts belong to the named classes; use the downloadable files for imports, configuration and assertions.')
 else:body+='<h3>Output</h3>'+code(output,'text')
 body+='<h2>Costs and boundaries</h2>'+para(cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(m)+'</li>' for m in mistakes)+'</ul><h2>Read next</h2>'+para(', '.join('[['+p+'|'+lookup.get(p,{}).get('title',p.split('/')[-1].replace('-',' ').capitalize())+']]' for p in related)+'.')
 hub=next(e for e in es if e['type']=='subject' and e['subject']==subject and e['path'].startswith('spring/' if spring else 'java/'))
 e=copy.deepcopy(lookup['java/casts']); e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,category='Backend Frameworks' if spring else lookup['java/casts']['category'],tags=['spring','spring-boot',slug] if spring else ['java',slug],difficulty='Intermediate',sort_order=650+len(added),status='published',featured=False,published_at=stamp,updated_at=stamp)
 e['data']={'subject_root':'spring/spring-boot' if spring else 'java/java','section_path':hub['path'],'content_format':'html','kind':'tutorial','reading_minutes':max(4,round(len(re.sub('<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-'+('spring' if spring else 'java')+'-source-kit.zip','related':[{'path':p,'title':lookup.get(p,{}).get('title',p.split('/')[-1])} for p in related],'seo_ready':True}
 if spring:e['data'].update(framework_version='Spring Boot 4.0.8 / Spring Framework 7',java_version='21 source-kit baseline',verification_suite=proof)
 else:e['data'].update(java_release=release,java_version=str(release)+'+')
 if path in lookup:es[es.index(lookup[path])]=e
 else:es.append(e)
 lookup[path]=e;added.append(path)

put('strict-utf8','Java UTF-8 decoding: reject malformed bytes before parsing',
'A CharsetDecoder converts bytes to characters and can report malformed input instead of replacing it silently.',[
('Preserve the evidence',['A receipt import accepts UTF-8 bytes, not arbitrary platform text. The input contract rejects an incomplete multibyte sequence. A convenience String constructor can replace bad bytes, leaving a character sequence that looks valid enough for a later parser while no longer matching what arrived. Decode first. Validate the resulting fields separately.','The fixture sends one ordinary amount record and one truncated sequence through the same decoder policy. It reports rejection without printing a payload that could contain personal data. This is a byte-level contract; it does not validate the record schema, numeric range or identity of the sender.']),
('A decoder has state',['Create a decoder per independent operation or manage its reset lifecycle explicitly. Decoder instances are mutable and should not be shared by concurrent requests. The one-shot decode method handles the end of the supplied buffer; incremental imports need an explicit final decode and flush while retaining incomplete bytes between chunks.','Cap the incoming bytes before decoding. Checking character count afterward does not prevent allocating an enormous byte buffer. A streaming reader can bound retained memory, but its chunk boundaries must not be mistaken for character boundaries. [[java/unicode-encoding|Encoding rules]] and [[spring/rest-validation|HTTP field validation]] handle different layers.'])],'''import java.nio.ByteBuffer;
import java.nio.charset.*;
public class ReceiptUtf8Boundary {
    static String decode(byte[] bytes) throws CharacterCodingException {
        if (bytes.length > 4096) throw new IllegalArgumentException("record too large");
        return StandardCharsets.UTF_8.newDecoder()
            .onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT)
            .decode(ByteBuffer.wrap(bytes)).toString();
    }
    public static void main(String[] args) throws Exception {
        System.out.println(decode("amount=125".getBytes(StandardCharsets.UTF_8)));
        try { decode(new byte[]{(byte)0xE2, (byte)0x82}); }
        catch (CharacterCodingException rejected) { System.out.println("malformed rejected"); }
    }
}''','amount=125\nmalformed rejected','For b input bytes, this one-shot conversion takes O(b) time and O(b) character storage in the worst case. The 4096-byte limit applies to this record format, not every import. Separate parsing and authentication costs remain outside the decoder.',
['Do not use replacement decoding for an import that must reject corrupted bytes.','Do not share one mutable decoder across threads.','Bound bytes before allocating the full payload.'],['java/unicode-encoding','java/byte-streams','spring/rest-validation'])

put('strict-date-parsing','Java strict date parsing: reject impossible calendar input',
'A DateTimeFormatter with STRICT resolution rejects invalid calendar combinations rather than adjusting them to a valid date.',[
('A parsed shape is not a valid date',['A delivery request sends an ISO-shaped local date. Four digits, a dash and two numeric fields are insufficient: 29 February must be checked against the selected year. The fixture accepts the leap-year date and rejects the same day in a non-leap year. That distinction belongs at the request boundary.','Use uuuu for a proleptic year in this formatter. yyyy denotes year-of-era and can need an era to resolve under strict rules. A convenient formatter that normalizes an impossible day can move a booking away from the value a person submitted.']),
('Dates do not contain deadlines',['A LocalDate has no time or offset. Converting it to a deadline requires a zone and a rule for which instant ends the allowed period. [[java/zone-transitions|Zone gaps and overlaps]] are separate from calendar validity, and a valid local date does not resolve them.','The immutable formatter can be reused. Do not replace it with a shared mutable legacy date parser. Exception messages may include user input; a public API should return a bounded error contract rather than exposing its entire parsing exception. [[spring/problem-details|Problem details]] supplies that response boundary.'])],'''import java.time.LocalDate;
import java.time.format.*;
import java.util.Locale;
public class DeliveryDateInput {
    static final DateTimeFormatter INPUT = DateTimeFormatter.ofPattern("uuuu-MM-dd", Locale.ROOT)
        .withResolverStyle(ResolverStyle.STRICT);
    public static void main(String[] args) {
        System.out.println(LocalDate.parse("2024-02-29", INPUT));
        try { LocalDate.parse("2023-02-29", INPUT); }
        catch (DateTimeParseException rejected) { System.out.println("invalid day rejected"); }
    }
}''','2024-02-29\ninvalid day rejected','Parsing takes time proportional to the bounded input length and returns one date object. The formatter can be shared because it is immutable. This program does not test time-zone conversion or a database date column.',
['Do not silently repair a booking date.','Use the year field that matches the intended resolution contract.','A valid LocalDate is not an absolute instant.'],['java/date-time','java/zone-transitions','spring/problem-details'],subject='java')

put('decimal-parse-boundary','Java DecimalFormat: reject trailing input and pin the locale',
'DecimalFormat parses locale-dependent numbers, and ParsePosition exposes how much of the input was consumed.',[
('Require the whole field',['An invoice amount parser must reject 125.50INR when its contract accepts a numeric field only. DecimalFormat can parse a valid prefix, so getting a Number is weaker than validating the whole field. Check the final parse index against input length and reject an empty or failed parse.','The program fixes US symbols, disables grouping and requests BigDecimal output. It then applies scale two with UNNECESSARY rounding, making fractional precision a visible boundary. Locale-dependent punctuation is a user interface policy; a machine API should define its own numeric grammar.']),
('Parsing is not complete domain validation',['A positive amount and a finite scale still do not identify a currency. Store the currency or minor-unit contract separately. Locale data is not evidence that every textual variation is acceptable. If the input must match a narrow ASCII wire format, validate that grammar explicitly before DecimalFormat.','DecimalFormat is mutable. This fixture creates it locally rather than putting one parser in a singleton service. Shared parser reuse can turn a predictable format rule into a thread-safety problem. [[java/bigdecimal|BigDecimal arithmetic]] handles later calculations; [[spring/configuration-properties|Typed configuration]] handles startup values.'])],'''import java.math.*;
import java.text.*;
import java.util.Locale;
public class InvoiceAmountInput {
    static BigDecimal parse(String input) {
        if (input.length() > 32) throw new IllegalArgumentException("amount too long");
        DecimalFormat format = new DecimalFormat("0.00", DecimalFormatSymbols.getInstance(Locale.US));
        format.setGroupingUsed(false); format.setParseBigDecimal(true);
        ParsePosition position = new ParsePosition(0);
        Number parsed = format.parse(input, position);
        if (!(parsed instanceof BigDecimal) || position.getIndex() != input.length())
            throw new IllegalArgumentException("complete decimal required");
        BigDecimal amount = ((BigDecimal) parsed).setScale(2, RoundingMode.UNNECESSARY);
        if (amount.signum() <= 0) throw new IllegalArgumentException("positive amount required");
        return amount;
    }
    public static void main(String[] args) {
        System.out.println(parse("125.50"));
        try { parse("125.50INR"); }
        catch (IllegalArgumentException rejected) { System.out.println("suffix rejected"); }
    }
}''','125.50\nsuffix rejected','Parsing and BigDecimal allocation grow with the digit count, bounded here by 32 characters. Creating a local formatter avoids shared mutable state at an allocation cost. This parser deliberately does not implement every currency or strict ASCII notation.',
['Do not treat a valid prefix as a valid amount field.','Pin the locale instead of inheriting the machine default.','Do not share DecimalFormat without an ownership policy.'],['java/bigdecimal','java/resource-bundles','spring/configuration-properties'])

put('serialization-filter','Java serialization filters: constrain classes and object graphs',
'An ObjectInputFilter can reject deserialized classes and graph sizes before ObjectInputStream returns an object.',[
('Limit the specific legacy contract',['A legacy migration file is expected to contain one small primitive int array. The fixture allows only int[] and caps its length, graph depth, references and reported bytes. It also caps the input byte array before opening the stream. A larger array and a different primitive array class are rejected independently.','This deliberately narrow filter has no application-defined serializable classes and no callbacks. Accepting an entire package would enlarge the trusted code surface. Prefer an explicit data format for new boundaries; a filter is a constraint on an existing serialization path, not a reason to accept arbitrary object streams.']),
('Validate the returned value too',['A filter receives graph information and sometimes no class. Return UNDECIDED for a metric-only callback after checking bounds, and reject unknown non-null classes. After reading, check the root type and application values. A class allowlist does not prove that an accepted array contains a valid business record.','The fixture checks complete locally generated files, not hostile network fuzzing. Stream metrics are not a substitute for a transport byte limit: filtering callbacks are not guaranteed to occur at every byte. [[java/byte-streams|Bounded byte input]] should be designed before the object stream is constructed.'])],'''import java.io.*;
public class LegacyBatchFilter {
    static byte[] encode(Object value) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) { out.writeObject(value); }
        return bytes.toByteArray();
    }
    static int[] read(byte[] bytes) throws Exception {
        if (bytes.length > 1024) throw new IOException("byte limit");
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            in.setObjectInputFilter(info -> {
                if (info.depth() > 2 || info.references() > 8 || info.streamBytes() > 1024 || info.arrayLength() > 4)
                    return ObjectInputFilter.Status.REJECTED;
                Class<?> type = info.serialClass();
                return type == null ? ObjectInputFilter.Status.UNDECIDED
                    : type == int[].class ? ObjectInputFilter.Status.ALLOWED : ObjectInputFilter.Status.REJECTED;
            });
            Object value = in.readObject();
            if (!(value instanceof int[])) throw new IOException("root type");
            return (int[]) value;
        }
    }
    public static void main(String[] args) throws Exception {
        System.out.println(read(encode(new int[]{12, 18})).length);
        try { read(encode(new int[5])); }
        catch (InvalidClassException rejected) { System.out.println("length rejected"); }
        try { read(encode(new long[]{12})); }
        catch (InvalidClassException rejected) { System.out.println("class rejected"); }
    }
}''','2\nlength rejected\nclass rejected','Serialization walks the accepted object graph and allocates reconstructed values. The fixture bounds the byte array and array length; it does not establish a universal CPU limit or sandbox code in accepted classes. Do not deserialize untrusted objects merely because a filter exists.',
['Avoid broad package allowlists for a narrow migration format.','Cap transport input independently of filter callbacks.','Validate the root and its values after reading.'],['java/byte-streams','java/try-with-resources','spring/rest-validation'],release=11)

put('shared-arena','Java shared Arena: coordinate access before closing memory',
'A shared Arena permits multiple threads to access its memory segments while retaining an explicit lifetime that ends on close.',[
('Sharing access does not order writes',['The import worker writes one native-memory integer. The main thread joins that worker before reading and before closing the arena. The join supplies the ordering boundary. A shared arena removes thread confinement; it does not turn ordinary memory reads and writes into an application-level synchronization protocol.','The fixture chooses one writer and one reader rather than concurrent conflicting updates. Its segment remains inside the owner scope, and closing happens only after the worker completes. Passing a segment to an executor without tracking outstanding tasks would create a use-after-close path.']),
('The owner closes after the users finish',['Native storage is not Java heap storage. The segment object can stay reachable after its arena has been closed, but access through that segment then fails. This program retains the object only to check that failure, not to continue using released memory.','If a worker fails, joining still completes but the owner must inspect its failure before trusting the result. Larger import systems need an explicit task-completion and cancellation policy. [[java/executors|Executor lifetime]] and [[spring/lifecycle-cleanup|Container cleanup]] connect to the same ownership question.'])],'''import java.lang.foreign.*;
public class SharedImportMemory {
    public static void main(String[] args) throws Exception {
        MemorySegment retained;
        try (Arena arena = Arena.ofShared()) {
            retained = arena.allocate(ValueLayout.JAVA_INT);
            Thread worker = new Thread(() -> retained.set(ValueLayout.JAVA_INT, 0, 125));
            worker.start(); worker.join();
            System.out.println(retained.get(ValueLayout.JAVA_INT, 0));
        }
        try { retained.get(ValueLayout.JAVA_INT, 0); }
        catch (IllegalStateException closed) { System.out.println("closed access rejected"); }
    }
}''','125\nclosed access rejected','The fixture allocates one integer outside the Java heap plus a segment wrapper and one thread. Thread startup dominates this small operation. Larger buffers scale native memory with allocated bytes; a shared arena does not impose an import-size limit.',
['Do not close the arena while queued tasks still hold its segments.','Shared access does not prevent data races.','Handle worker failures before accepting their output.'],['java/foreign-memory','java/executors','spring/lifecycle-cleanup'],release=25)

put('phaser-registration','Java Phaser: deregister workers so a phase can complete',
'A Phaser coordinates a registered set of participants across numbered phases and permits participants to deregister.',[
('Registration is a completion obligation',['An import coordinator registers itself and two workers. Every registered party must arrive before the phase advances. A failed worker that leaves without arriving can keep the coordinator waiting forever. The fixture puts arrival and deregistration in finally so its registration is released even if work throws.','Register before starting the worker. Registering inside a thread can race with the coordinator arriving and advancing before the intended participant exists. The initial party count makes this fixture’s starting boundary explicit.']),
('A barrier is not an error report',['The workers increment a thread-safe completed counter. The barrier says both released their phase obligations; it does not say their business operations succeeded. Keep failures separately and inspect them after the phase when the task contract requires all records to pass.','This program waits without a timeout because its workers do bounded local work. Production coordination needs an interruption or deadline policy and a way to stop remaining tasks. [[java/cancellation|Cancellation]] does not automatically roll back effects already committed by another worker.'])],'''import java.util.concurrent.Phaser;
import java.util.concurrent.atomic.AtomicInteger;
public class ImportPhaseCompletion {
    public static void main(String[] args) throws Exception {
        Phaser phase = new Phaser(3);
        AtomicInteger completed = new AtomicInteger();
        Runnable task = () -> { try { completed.incrementAndGet(); } finally { phase.arriveAndDeregister(); } };
        Thread first = new Thread(task), second = new Thread(task);
        first.start(); second.start();
        phase.arriveAndAwaitAdvance();
        first.join(); second.join();
        System.out.println("completed=" + completed.get());
        System.out.println("remaining=" + phase.getRegisteredParties());
        phase.arriveAndDeregister();
        System.out.println("terminated=" + phase.isTerminated());
    }
}''','completed=2\nremaining=1\nterminated=true','The coordinator stores participant counts rather than one result per participant. This fixture creates two threads and one counter. A barrier does not bound task duration, and retaining worker results or failures adds application storage proportional to the worker count.',
['Release registration in finally when a worker exits.','Register before work can race with phase advancement.','Do not interpret arrival as business success.'],['java/threads','java/cancellation','spring/async-boundaries'])

put('linkedlist-cursor','Java LinkedList ListIterator: edit at a cursor without repeated searches',
'A ListIterator tracks a position between list elements and supports controlled insertion, replacement and removal during traversal.',[
('Use the cursor as the edit location',['A review queue contains Read, Code and Ship. The cursor moves over Read, inserts Test after it, then moves over Code and removes it. Insertion uses the cursor gap; removal uses the last element returned by traversal. The resulting queue is Read, Test, Ship.','After add, remove cannot be called until next or previous establishes a new last-returned element. The second part of the fixture checks that state rule explicitly. A cursor is more than an integer index: its allowed operations depend on the last traversal and edit.']),
('Do not pay for a new search on every step',['A loop that repeatedly calls get(index) on a linked list revisits nodes and can take quadratic total time. Once positioned, the iterator can traverse and edit without starting a new search for every element. Obtaining listIterator(index) can still require locating that position.','The fixture has one thread and edits through the iterator itself. External structural mutation invalidates its assumptions; best-effort fail-fast detection cannot protect a shared queue. For concurrent production work, choose the appropriate [[java/blocking-queues|queue contract]] and define ownership rather than relying on an exception.'])],'''import java.util.*;
public class ReviewQueueCursor {
    public static void main(String[] args) {
        LinkedList<String> queue = new LinkedList<>(Arrays.asList("Read", "Code", "Ship"));
        ListIterator<String> cursor = queue.listIterator();
        cursor.next(); cursor.add("Test"); cursor.next(); cursor.remove();
        System.out.println(queue);
        cursor.add("Audit");
        try { cursor.remove(); }
        catch (IllegalStateException rejected) { System.out.println("cursor state rejected"); }
    }
}''','[Read, Test, Ship]\ncursor state rejected','Walking n elements through one cursor takes O(n) time. Positioning at an arbitrary index can take O(n), while cursor-local node edits have constant structural work. Each stored element requires a linked node; this is not evidence that LinkedList beats an array-backed queue for the workload.',
['Do not call remove immediately after add without a traversal step.','Avoid indexed loops over a linked list.','Do not treat fail-fast detection as synchronization.'],['java/linkedlist','java/iterators','java/arraydeque'],subject='java-collections')

put('lazy-segment-tree','Java lazy segment tree: add to ranges and query sums',
'A lazy segment tree records a deferred update on a covered interval so range additions do not visit every element immediately.',[
('Store both the aggregate and the deferred work',['A capacity ledger needs to add the same reservation adjustment to every slot in an interval and read interval totals. Each tree node stores its sum and a pending addition for its descendants. Covering a node updates its sum by delta times interval length and records the deferred delta.','Before visiting part of a covered node, push its deferred addition to both children. Otherwise a later partial query reads old child sums even though the parent looks correct. Zero is the identity for an absent contribution, not a missing-value sentinel.']),
('Specify the arithmetic boundary',['The implementation accepts nonempty arrays up to 100000 elements and half-open intervals with at least one element. It uses long sums and requires callers to keep every intermediate sum and product within long range. The code does not detect overflow; wrapping invalidates the result. Production ledgers need an overflow or wider-number policy before using this model.','Queries can push deferred updates, so they mutate internal representation even though the logical values remain unchanged. Do not expose this tree to concurrent readers without synchronization. Compare it with [[java/segment-tree|point-update trees]] and [[java/fenwick-tree|Fenwick sums]] before choosing the state you need.'])],'''public class CapacityRangeTree {
    private final int count;
    private final long[] sums, pending;
    CapacityRangeTree(long[] values) {
        if (values.length == 0 || values.length > 100000) throw new IllegalArgumentException("size");
        count = values.length; sums = new long[4 * count]; pending = new long[4 * count];
        build(1, 0, count, values);
    }
    private void build(int node, int left, int right, long[] values) {
        if (right-left == 1) { sums[node] = values[left]; return; }
        int middle = left + (right-left)/2;
        build(node*2,left,middle,values); build(node*2+1,middle,right,values);
        sums[node] = sums[node*2] + sums[node*2+1];
    }
    private void apply(int node,int length,long delta) { sums[node] += delta * length; pending[node] += delta; }
    private void push(int node,int left,int right) {
        int middle = left + (right-left)/2;
        apply(node*2,middle-left,pending[node]); apply(node*2+1,right-middle,pending[node]); pending[node]=0;
    }
    private void bounds(int left,int right) {
        if (left<0 || right>count || left>=right) throw new IllegalArgumentException("range");
    }
    void add(int left,int right,long delta) { bounds(left,right); add(1,0,count,left,right,delta); }
    private void add(int node,int left,int right,int from,int until,long delta) {
        if (until<=left || right<=from) return;
        if (from<=left && right<=until) { apply(node,right-left,delta); return; }
        push(node,left,right); int middle=left+(right-left)/2;
        add(node*2,left,middle,from,until,delta); add(node*2+1,middle,right,from,until,delta);
        sums[node]=sums[node*2]+sums[node*2+1];
    }
    long sum(int left,int right) { bounds(left,right); return sum(1,0,count,left,right); }
    private long sum(int node,int left,int right,int from,int until) {
        if (until<=left || right<=from) return 0;
        if (from<=left && right<=until) return sums[node];
        push(node,left,right); int middle=left+(right-left)/2;
        return sum(node*2,left,middle,from,until)+sum(node*2+1,middle,right,from,until);
    }
    public static void main(String[] args) {
        CapacityRangeTree ledger=new CapacityRangeTree(new long[]{10,20,30,40});
        ledger.add(1,4,5); System.out.println(ledger.sum(0,4));
        ledger.add(0,2,-3); System.out.println(ledger.sum(1,3));
        try { ledger.sum(2,2); } catch (IllegalArgumentException rejected) { System.out.println("empty range rejected"); }
    }
}''','115\n57\nempty range rejected','Construction costs O(n) time and O(n) storage. Each interval addition or sum query takes O(log n) time with O(log n) recursion depth. The bound is for one contiguous interval; arbitrary disjoint batches add more operations. This implementation is not persistent or thread-safe.',
['Push pending work before descending into part of an interval.','Use one interval convention consistently.','Do not assume long arithmetic cannot overflow.'],['java/segment-tree','java/fenwick-tree','java/tabulation'],subject='java-dsa')

# Spring calls are added below before final publication.

def spring(slug,title,definition,sections,source,cost,mistakes,related,subject,proof):
 put(slug,title,definition,sections,source,'',cost,mistakes,related,subject=subject,spring=True,proof=proof)
def kit(name,test=False):
 return (ROOT/'work/spring-kit'/('src/test/java' if test else 'src/main/java')/'in/aitrove/contracts'/(name+'.java')).read_text()

spring('jpa-entity-lifecycle','Spring JPA entity lifecycle: managed changes and detached objects',
'A JPA persistence context tracks managed entity identity and changes; an ordinary detached object no longer writes its field changes to the database.',[
('Observe the ownership transition',['The stock fixture creates three accounts, then changes the first account through an EntityManager bound to a Spring JpaTransactionManager transaction. A fresh manager reads 80 after commit. The test does not call a repository save method because the object is already managed within that transaction.','The second test closes the manager before changing an account to seven. A fresh read still returns 100. Java object mutation happened, but database mutation did not. Keep that distinction visible when returning entities from a service; a caller holding an object is not evidence that its edits are being tracked.']),
('Flush is not commit',['The source kit assembles LocalContainerEntityManagerFactoryBean explicitly, scans only the isolated contract package and uses create-drop against a unique in-memory H2 database. This setup exists to test mapping behavior. Never turn that schema setting into a production migration strategy.','A flush can send changes to the database before commit, while the transaction can still fail or roll back. Query timing and transaction scope therefore matter even when code contains no explicit update call. [[spring/transactions|Transaction boundaries]] and [[java/jdbc-transactions|JDBC commit behavior]] are prerequisites for reasoning about these effects.'])],'''var transactions = new TransactionTemplate(new JpaTransactionManager(kit.factory));
transactions.executeWithoutResult(status -> {
    EntityManager manager = EntityManagerFactoryUtils.getTransactionalEntityManager(kit.factory);
    manager.find(JpaContracts.StockAccount.class, 1L).available = 80;
});''','A context retains managed objects and provider bookkeeping until they are detached or the context closes. Loading n entities can retain O(n) application objects; SQL and dirty-check costs depend on mappings and the provider. The fixture verifies one update, not a bulk-import memory budget.',
['Do not confuse detached mutation with persistence.','Do not treat flush as successful commit.','Do not use create-drop for a deployed database.'],['spring/jpa-fetch-plans','spring/jpa-optimistic-locking','spring/transactions','java/classes-objects'],'spring-data','JpaBoundaryTest.managedMutationFlushesOnCommit and detachedMutationDoesNotWriteItself')

spring('jpa-fetch-plans','Spring JPA fetch plans: measure N+1 queries before changing mappings',
'A fetch plan determines which related entity state a query loads, and lazy relationship traversal can issue extra statements after the root query.',[
('Count statements in a fresh context',['The fixture stores three stock lines, each linked to a distinct account. One query loads the lines, then reading each account’s available count produces three extra statements. The assertion checks four prepared statements after clearing Hibernate statistics. This makes the cost visible instead of inferring it from a method name.','Read account state through the getter: direct public-field access on a lazy proxy does not trigger its loading method. The test checks that distinction before traversal. A second test uses a new context and a join fetch for the single-valued account association. The same total, 300, now requires one statement. The fresh context matters: reusing already-loaded account objects could hide the extra queries and make an inefficient traversal appear cheap.']),
('Fetch only what the operation needs',['Switching every relationship to eager loading can move extra work to requests that never need it. Choose a query for the actual response contract, or return a projection that contains just the required fields. Query count is one measure; row width, transferred bytes and execution plans still matter.','This example fetches a many-to-one association. Fetching a collection can multiply result rows, and applying page limits to such a join needs separate reasoning. [[spring/pagination-bounds|Offset bounds]] do not prove collection fetch pagination is correct. The lesson does not claim that its single statement is the best plan for every database.'])],'''var lines = manager.createQuery(
    "select line from StockLine line join fetch line.account order by line.id",
    JpaContracts.StockLine.class).getResultList();
int total = 0;
for (var line : lines) total += line.account.getAvailable();
assertEquals(300, total);
assertEquals(1, kit.statistics().getPrepareStatementCount());''','The checked traversal reads three lines and three accounts. The lazy path has 1+n statements for n distinct unloaded accounts in this mapping; the fetch path has one statement but still transfers and retains the required rows. Both counts are isolated local measurements, not latency benchmarks.',
['Clear provider statistics and use a fresh context before comparing query counts.','Do not make every relationship eager to fix one request.','Do not apply collection-fetch pagination rules to a single-valued join blindly.'],['spring/jpa-entity-lifecycle','spring/pagination-bounds','spring/jpa-optimistic-locking','java/jmh-benchmarks'],'spring-data','JpaBoundaryTest.lazyTraversalCountsOneQueryPerDistinctAccount and fetchJoinLoadsAccountsInOneStatement')

spring('jpa-optimistic-locking','Spring JPA optimistic locking: reject a stale stock update',
'A versioned JPA entity detects an update based on an older revision so one writer cannot silently overwrite a newer committed revision.',[
('Construct two independent views',['Two EntityManagers load the same stock account before either changes it. The first writer commits 90 available units. The second still holds the earlier revision and tries to write 70. The test expects OptimisticLockException at flush, then rolls back the failed transaction.','The entity has one Long version field marked Version. Application code changes available, not the version. This fixture performs an ordered two-view experiment; it reproduces a stale write without claiming to simulate every possible concurrency schedule or database isolation level.']),
('A retry must repeat the decision',['Catching the exception and resubmitting the old desired value can still discard the business intent behind a competing update. Reload current stock and recompute the reservation under the intended contract, with a bounded retry policy. A failed transaction’s persistence context should not be reused as though it were healthy.','Versioning one account does not protect an invariant spanning several unversioned rows. It also does not stop duplicate external side effects from a retry. [[java/multi-index-invariants|Multi-object invariants]] and [[spring/transaction-propagation|Transaction scope]] need explicit treatment before applying this to a real inventory service.'])],'''try (var first = kit.factory.createEntityManager();
     var second = kit.factory.createEntityManager()) {
    var current = first.find(JpaContracts.StockAccount.class, 1L);
    var stale = second.find(JpaContracts.StockAccount.class, 1L);
    first.getTransaction().begin();
    current.available = 90;
    first.getTransaction().commit();
    second.getTransaction().begin();
    stale.available = 70;
    assertThrows(OptimisticLockException.class, second::flush);
    second.getTransaction().rollback();
}''','A version check adds revision data to the update predicate and failure handling to the application. Contention can increase retries and database work. The local test proves rejection for one stale account update; it does not prove multi-row serializability or quantify throughput.',
['Do not edit the version manually.','Roll back after a failed flush.','Do not retry a stale decision without re-reading the state it depends on.'],['spring/jpa-entity-lifecycle','spring/transaction-propagation','java/database-isolation','java/multi-index-invariants'],'spring-data','JpaBoundaryTest.staleVersionRejectsSecondWriter')

spring('transaction-propagation','Spring transaction propagation: joined rollback and independent commit',
'Transaction propagation determines whether a call joins an existing transaction or runs with another transaction boundary.',[
('Joined work shares rollback fate',['TransactionContracts starts a REQUIRED outer transaction and inserts a pending journal row. An inner REQUIRED template marks its status rollback-only. The outer callback returns normally, but its attempted commit raises UnexpectedRollbackException and the table stays empty. Catching an inner application exception would not necessarily make the transaction committable.','The fixture uses templates so the propagation boundary is visible without proxy routing. An annotation-based service needs the call to cross the appropriate proxy; self-invocation can bypass the intended interception. Read [[spring/transaction-proxies|Transaction proxies]] before translating this template into service annotations.']),
('Independent work has an independent consequence',['The second path inserts a pending row in the outer transaction, suspends it for REQUIRES_NEW, and commits a different audit row. The outer then rolls back. Only the audit row remains. That behavior is appropriate only if an audit entry is intended to survive a failed import.','An independent transaction can need another connection while the outer one remains held. The fixture uses separate H2 connections and unrelated primary keys. A bounded pool or shared locked row can change failure behavior; nesting REQUIRES_NEW under load needs a pool-capacity and lock analysis. [[java/connection-pool|Connection-pool boundaries]] provide that context.'])],kit('TransactionContracts'),'The test verifies two propagation paths, not every database schedule. Suspending a transaction retains its resources until resumed. An inner independent transaction adds connection demand and cannot be assumed to avoid deadlocks merely because it has a separate name.',
['Do not assume an outer commit succeeds after joined work marked rollback-only.','Choose intentionally whether an audit must survive rollback.','Budget extra connections for independent nested transactions.'],['spring/transactions','spring/transaction-proxies','spring/transaction-events','java/connection-pool'],'spring-data','FrameworkBoundaryTest.requiresNewAuditSurvivesOuterRollback and requiredInnerRollbackRejectsOuterCommit')

spring('transaction-events','Spring transaction events: run a listener after commit without claiming durability',
'A TransactionalEventListener can defer an event callback until a selected transaction phase, such as AFTER_COMMIT.',[
('Publish in the transaction you mean',['The event fixture publishes an imported receipt three ways: outside a transaction, inside a rolled-back transaction, and inside a committed transaction. With default fallback behavior, only the committed event reaches the AFTER_COMMIT list. The test checks the final list contains the third receipt alone.','The list is ordinary process-local state and the listener runs in the test thread. This makes the phase contract inspectable. It does not provide a queue, durable log, separate worker or cross-process delivery mechanism. [[spring/application-events|Ordinary application events]] and transaction-bound listeners have different timing rules.']),
('A completed commit cannot be undone by the listener',['When the listener starts after commit, the original database transaction has already succeeded. A listener failure must be handled as a post-commit failure; presenting it as though the original insert rolled back would lie to the caller. A fresh database write from this phase needs its own explicit transaction design.','A process can stop after committing a row and before delivering an in-memory callback. An outbox design addresses that gap by writing delivery intent with the business transaction and processing it separately. This lesson identifies the gap; it does not ship a durable outbox or an exactly-once consumer.'])],kit('CommitEvents'),'The callback list grows with observed events and is unbounded in this teaching fixture. A production listener needs retention, concurrency and failure policies. AFTER_COMMIT describes timing; it supplies neither durable storage nor a latency limit.',
['Do not treat an in-memory callback as durable message delivery.','Do not assume a listener failure can roll back an already committed transaction.','Do not rely on default delivery outside a transaction.'],['spring/application-events','spring/transaction-propagation','spring/async-boundaries','java/jdbc-transactions'],'spring-core','FrameworkBoundaryTest.afterCommitDoesNotRunOnRollbackOrWithoutTransaction')

spring('method-authorization','Spring method authorization: test the proxied service boundary',
'Method authorization intercepts a service invocation and evaluates an access rule before the protected method executes.',[
('Protect the service operation',['AuthorizedReceiptRead requires receipt:read through PreAuthorize. The configuration explicitly enables method security, then the test obtains the bean from the context. A caller with that authority receives receipt:7; an authenticated caller without it receives AccessDeniedException. Authentication and authorization are separate questions.','The test installs a SecurityContext only for its local invocation and clears it in finally. It does not verify a login flow, tokens, sessions or a persistent identity store. [[spring/security-filter-chain|HTTP filter rules]] remain necessary because they govern the request boundary that calls this service.']),
('An annotation does not protect every Java object',['The test also constructs AuthorizedReceiptRead directly. That object returns the receipt because it has no method-security proxy. This is intentional evidence of the boundary: an annotation is metadata, while interception supplies the enforcement path. Do not expose an unproxied copy of the service as a bypass.','The authority rule permits reading receipts in general. It does not prove ownership of receipt seven or enforce tenant membership. Add resource-specific authorization using trusted identity and repository state when the domain requires it. A route parameter supplied by the caller is not evidence of permission.'])],kit('AuthorizedReceiptRead'),'Each call evaluates a rule through the configured interceptor. A rule consulting a database adds its own latency and failure path. This local authority check contains no tenant query and should not be advertised as object-level access control.',
['Enable method security and test the bean obtained from the context.','Do not assume direct construction enforces the annotation.','Do not confuse a general authority with ownership of a particular record.'],['spring/security-filter-chain','spring/proxy-self-invocation','spring/testing-boundaries','java/interfaces'],'spring-security','FrameworkBoundaryTest.methodProxyChecksAuthorityAndDirectObjectDoesNot')

spring('metric-cardinality','Spring Boot metrics: bound tag values instead of tracking each receipt',
'A Micrometer meter identity includes its name and tags, so a new tag value can create another series rather than another sample in the same series.',[
('Model a finite outcome set',['The import metric has two outcomes: ACCEPTED and REJECTED. BoundedImportMetrics receives that enum rather than arbitrary strings. Recording one hundred accepted records and one rejected record creates exactly two local meters, with the accepted counter at one hundred.','The test uses SimpleMeterRegistry so the identity count is visible without a remote backend. Adding receipt IDs, email addresses or request paths containing identifiers would change both retained state and exported series count. Such values also risk placing sensitive data in telemetry.']),
('Local meter count is not backend cost',['A remote monitoring system may retain older time series after an application stops exporting them. Multiplying finite tag dimensions can still create many combinations: tenant, region and outcome counts must be budgeted together. A bounded enum only constrains the dimension it owns.','Use logs or traces with an explicit retention and privacy policy when investigating a specific record. Do not solve cardinality by silently dropping a business metric without checking what operations needs to answer. [[spring/actuator-health|Health probes]] tell a different story from import counters.'])],kit('BoundedImportMetrics'),'The fixture retains two counter identities and increments in constant application work. Real exporter buffering, scraping and backend retention add costs not measured by this test. No remote metrics endpoint, dashboard or production alert threshold is supplied.',
['Do not use receipt IDs as metric tags.','Bound the product of tag dimensions, not only one dimension.','Do not infer backend retention cost from a local registry test.'],['spring/actuator-health','spring/cache-keys','spring/async-boundaries','java/long-adder'],'spring-production','FrameworkBoundaryTest.enumOutcomeBoundsMeterIdentities')

spring('reactive-demand','Spring reactive foundations: request values and cancel a subscription',
'Reactive demand is a subscriber’s request for a bounded number of values from a publisher, while cancellation ends that subscription’s interest in further signals.',[
('Begin with zero demand',['The Reactor fixture supplies five integer receipt markers. StepVerifier subscribes with an initial request of zero, asks for two values, expects one and two, then cancels. A separate assertion checks the cancellation hook. Another test requests all five and observes completion.','This is a Reactor Core sequence, not a WebFlux HTTP endpoint. Keeping that distinction explicit avoids claiming a transport, request-body buffer limit or network backpressure policy from a small in-memory publisher test. The sequence runs without a scheduler switch or blocking database call.']),
('Demand is not a universal resource limit',['An operator can prefetch or buffer upstream work, so a downstream request of two does not imply every upstream resource holds exactly two items. Cancellation also cannot undo a payment or database commit that already happened. Design cleanup and side-effect boundaries independently.','A blocking repository call inside a reactive callback still blocks its executing thread. Replacing an MVC return type with a publisher does not convert that repository into nonblocking I/O. [[spring/async-boundaries|Worker capacity]] and [[java/cancellation|Cancellation rules]] remain relevant before moving this model into an HTTP service.'])],kit('ReactiveReceiptDemand'),'Flux.range emits a fixed bounded sequence here; the test requests only two or five values. Buffering, scheduler queues, upstream I/O and concurrent subscriptions are outside this fixture. No throughput or end-to-end memory guarantee follows from passing it.',
['Do not treat demand as a rollback mechanism.','Do not hide blocking I/O behind a publisher return type.','Test cancellation cleanup separately from normal completion.'],['spring/async-boundaries','spring/web-apis','java/cancellation','java/blocking-queues'],'spring-web','FrameworkBoundaryTest.demandGatesValuesAndCancelStopsSubscription and completeDemandReceivesAllValues')

# Append one named module per affected section. Existing lessons and quiz banks survive.
for subject in sorted({lookup[path]['subject'] for path in added}):
 hub=next(e for e in es if e['type']=='subject' and e['subject']==subject)
 name={'java':'Strict calendar input','java-advanced':'Input limits and shared task ownership','java-collections':'Cursor-local edits','java-dsa':'Deferred range updates','spring-data':'Persistence and competing transaction boundaries','spring-core':'Commit-phase callbacks','spring-security':'Service authorization','spring-production':'Bounded metric identities','spring-web':'Reactive demand foundations'}[subject]
 hub['data']['modules']=[m for m in hub['data']['modules'] if m['title']!=name]
 hub['data']['modules'].append({'title':name,'summary':'Inspect the state boundary and run its checked fixture.','lessons':[p for p in added if lookup[p]['subject']==subject]})
 hub['updated_at']=stamp
# Reciprocal contextual links, limited to contracts that the new lesson extends.
reverse={
 'java/unicode-encoding':['java/strict-utf8'], 'java/date-time':['java/strict-date-parsing'],
 'java/bigdecimal':['java/decimal-parse-boundary'], 'java/foreign-memory':['java/shared-arena'],
 'java/linkedlist':['java/linkedlist-cursor'], 'java/segment-tree':['java/lazy-segment-tree'],
 'java/jdbc-transactions':['spring/transaction-propagation','spring/jpa-entity-lifecycle'],
 'java/interfaces':['spring/method-authorization'], 'java/cancellation':['spring/reactive-demand'],
 'spring/transactions':['spring/transaction-propagation','spring/jpa-entity-lifecycle'],
 'spring/jdbc-template':['spring/jpa-fetch-plans','spring/jpa-optimistic-locking'],
 'spring/application-events':['spring/transaction-events'],
 'spring/security-filter-chain':['spring/method-authorization'],
 'spring/actuator-health':['spring/metric-cardinality'],
 'spring/async-boundaries':['spring/reactive-demand','java/phaser-registration'],
 'spring/rest-validation':['java/strict-utf8','java/strict-date-parsing'],
 'spring/configuration-properties':['java/decimal-parse-boundary']}
for path,targets in reverse.items():
 e=lookup[path];marker='<h2>Extend this boundary</h2>'
 # This batch owns only this trailing section; earlier body text is preserved.
 e['body']=e['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 e['updated_at']=stamp
# Refresh overview counts from the preserved section modules, not stale preview copy.
for hub in es:
 if hub['type']=='subject' and hub['path'].startswith(('java/','spring/')):
  paths={p for m in hub['data'].get('modules',[]) for p in m['lessons']}
  hub['body']=re.sub(r'This section contains \d+ (?:published |checked )?(?:lessons|pages)', 'This section contains '+str(len(paths))+' published lessons',hub['body'])
  if hub['path'].startswith('spring/'):
   lesson_links='<ul>'+''.join('<li><a href="/'+path+'">'+html.escape(lookup[path]['title'])+'</a></li>' for m in hub['data']['modules'] for path in m['lessons'])+'</ul>'
   hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda match:match[1]+lesson_links+match[2],hub['body'])

FILE.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n')
(ROOT.parent.parent/'outputs/java-spring-next-additions.json').write_text(json.dumps({'added':added,'java':[p for p in added if p.startswith('java/')],'spring':[p for p in added if p.startswith('spring/')],'reciprocalPagesUpdated':len(reverse)},indent=2))
print('Added',len(added),'pages; reciprocal links updated on',len(reverse),'existing pages')
