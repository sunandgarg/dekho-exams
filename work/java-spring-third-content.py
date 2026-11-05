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

put('native-linker','Java native Linker: declare a C call and reject undefined input',
'A native Linker creates a method handle for a foreign function using a descriptor that matches the platform calling convention.',[
('Match the foreign signature',['The fixture calls the platform C abs function for a bounded signed adjustment. It obtains the canonical C int layout from the linker instead of assuming that every foreign integer type has the Java long layout. A signature mismatch at this boundary can corrupt execution rather than produce an ordinary type error.','The program rejects Integer.MIN_VALUE before entering C, because its positive magnitude does not fit the same signed int representation. That condition is an input rule, not an exception the native function is expected to throw back into Java. The checked fixture uses a Java int carrier on this platform.']),
('Grant access deliberately',['Run the downloaded class with --enable-native-access=ALL-UNNAMED because this kit uses the classpath. A named-module application should grant the intended module rather than copying that flag indiscriminately. Native access is a trust decision; it does not validate a function descriptor or make foreign code memory-safe.','The checked call has no pointers or allocated foreign buffers. Larger APIs need an ownership rule for each pointer and callback, including how long the callee retains it. [[java/foreign-memory|Memory segments]] and [[java/shared-arena|Shared arena lifetime]] cover separate parts of that contract.'])],'''import java.lang.foreign.*;
import java.lang.invoke.MethodHandle;
public class NativeAdjustmentMagnitude {
    static int magnitude(MethodHandle operation,int adjustment) throws Throwable {
        if (adjustment == Integer.MIN_VALUE) throw new IllegalArgumentException("magnitude exceeds signed int");
        return (int) operation.invokeExact(adjustment);
    }
    public static void main(String[] args) throws Throwable {
        Linker linker=Linker.nativeLinker();
        MemoryLayout integer=linker.canonicalLayouts().get("int");
        if (!(integer instanceof ValueLayout.OfInt)) throw new UnsupportedOperationException("C int carrier");
        MethodHandle operation=linker.downcallHandle(linker.defaultLookup().find("abs").orElseThrow(),
            FunctionDescriptor.of(integer,integer));
        System.out.println(magnitude(operation,-125));
        System.out.println(magnitude(operation,0));
        try {magnitude(operation,Integer.MIN_VALUE);}
        catch(IllegalArgumentException rejected){System.out.println("range rejected");}
    }
}''','125\n0\nrange rejected','The scalar operation has bounded work, but downcall setup and foreign-transition costs are not measured here. The example is checked on the local platform, not every ABI. It does not make a claim that native abs is a better choice than Java arithmetic.',
['Match the actual C signature and carrier.','Reject values outside the foreign function contract before calling it.','Native access does not sandbox a foreign library.'],['java/foreign-memory','java/shared-arena','java/varhandles'],release=25)
lookup['java/native-linker']['data']['java_runtime_flags']=['--enable-native-access=ALL-UNNAMED']

put('flow-demand','Java Flow: request items and observe publisher completion',
'Flow separates publishers, subscribers and subscriptions so a subscriber can request a number of items rather than accepting an unspecified push rate.',[
('Completion belongs to the subscription',['The receipt subscriber requests one amount at subscription time and requests another after each received amount. The publisher sends ten and twenty, then closes. The completion future is joined before the total is read, making successful completion distinct from merely calling submit twice.','SubmissionPublisher owns buffering and delivery behavior. This fixture chooses a direct executor for deterministic local observation; it does not represent a worker pool or network transport. A one-at-a-time request policy here does not prove that a remote importer retains only one record.']),
('Keep errors visible',['onError completes the same future exceptionally so join cannot return a successful total after a delivery failure. Production callbacks should define cancellation and downstream failure handling without throwing errors into unrelated application work. Do not treat normal close as a way to repair a failed record.','The atomic total avoids relying on an undocumented thread choice in the subscriber. A real payment amount needs a unit and overflow policy too. Compare this API-level contract with [[spring/reactive-demand|Reactor demand]] before assuming they provide an identical set of operators or runtime services.'])],'''import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class ReceiptFlowTotal {
    public static void main(String[] args) {
        AtomicInteger total=new AtomicInteger();
        CompletableFuture<Void> finished=new CompletableFuture<>();
        try(SubmissionPublisher<Integer> publisher=new SubmissionPublisher<>(Runnable::run,8)) {
            publisher.subscribe(new Flow.Subscriber<Integer>() {
                Flow.Subscription subscription;
                public void onSubscribe(Flow.Subscription value){subscription=value;subscription.request(1);}
                public void onNext(Integer amount){total.addAndGet(amount);subscription.request(1);}
                public void onError(Throwable failure){finished.completeExceptionally(failure);}
                public void onComplete(){finished.complete(null);}
            });
            publisher.submit(10);publisher.submit(20);
        }
        finished.join();System.out.println(total.get());
    }
}''','30','The fixture processes two integers with a configured buffer capacity and direct delivery. Application storage depends on retained subscriptions, buffered items and callbacks. A blocking submit or slow subscriber can affect caller latency; no throughput measurement is provided.',
['Request demand through the subscription.','Read results after observing completion or failure.','Do not infer a network buffer limit from this local sequence.'],['java/completable-future','java/blocking-queues','spring/reactive-demand'],release=11)

put('lru-cache','Java LinkedHashMap LRU cache: access order changes eviction',
'An access-ordered LinkedHashMap tracks recently accessed entries so a bounded cache can remove the least recently used entry after insertion.',[
('A read changes the eviction order',['A document cache has space for two keys. It inserts invoice and receipt, reads invoice, then inserts statement. Receipt is evicted because the read promoted invoice to the most recent position. The printed key order makes that policy visible.','The capacity check belongs to removeEldestEntry and runs after insertion. The constructor rejects non-positive capacity rather than letting a zero-sized cache conceal a configuration error. This is a count bound, not a byte-size bound: one enormous document can still consume too much memory.']),
('Define what the cache does not own',['This fixture stores immutable strings in one thread. It has no expiry clock, fetch coalescing or persistence. A synchronized wrapper can serialize individual calls, but a lookup-then-load-then-put workflow needs its own coordination if duplicate remote work matters.','An access-ordered get changes iteration order. Do not assume that a read is harmless while another thread walks the keys. For a framework cache, [[spring/cache-keys|Key identity]] and invalidation rules still determine whether a returned document belongs to the intended tenant.'])],'''import java.util.*;
public class DocumentLruCache extends LinkedHashMap<String,String> {
    private final int capacity;
    DocumentLruCache(int capacity) {
        super(16,0.75f,true);
        if(capacity<1)throw new IllegalArgumentException("capacity");
        this.capacity=capacity;
    }
    protected boolean removeEldestEntry(Map.Entry<String,String> eldest){return size()>capacity;}
    public static void main(String[] args) {
        DocumentLruCache cache=new DocumentLruCache(2);
        cache.put("invoice","I");cache.put("receipt","R");cache.get("invoice");cache.put("statement","S");
        System.out.println(cache.keySet());System.out.println(cache.containsKey("receipt"));
        try{new DocumentLruCache(0);}catch(IllegalArgumentException rejected){System.out.println("capacity rejected");}
    }
}''','[invoice, statement]\nfalse\ncapacity rejected','Expected hash lookup and access-order maintenance are constant work under ordinary key behavior. The cache retains at most capacity entries after insertion returns, plus a temporary new entry during the operation. Key/value sizes and hash quality remain part of the memory and latency budget.',
['Access ordering requires the access-order constructor setting.','A count limit is not a byte limit.','Do not assume cache get leaves iteration order unchanged.'],['java/linkedhashmap','java/collection-views','spring/cache-keys'],subject='java-collections')

put('navigable-map-ranges','Java NavigableMap ranges: distinguish a live window from a snapshot',
'A NavigableMap exposes ordered boundary lookups and range views whose contents can remain connected to the backing map.',[
('A view is still the same data owner',['A dispatch ledger stores timestamps ten, twenty and thirty. The half-open window from ten to thirty excludes the record at thirty. Replacing twenty through that window replaces it in the original ledger as well. A TreeMap copy captures the selected entries at that moment and does not observe a later insert.','The fixture also asks floorEntry for twenty-four and receives the entry at twenty. That is a predecessor lookup, not exact equality. Pick floor, ceiling, lower or higher from the boundary rule instead of adding ad hoc off-by-one arithmetic to an exact-key lookup.']),
('The window rejects outside writes',['Inserting forty into the selected window raises IllegalArgumentException. That is a range restriction on the view, not proof of a domain-level permission check. A different reference to the backing map can still write forty.','Copying the map copies entry references rather than making mutable values independent. Here strings make the snapshot distinction straightforward; a mutable dispatch record needs a separate copy policy. [[java/collection-views|View ownership]] and [[spring/pagination-bounds|Response snapshots]] explain why returning a view can expose more ownership than intended.'])],'''import java.util.*;
public class DispatchRangeWindow {
    public static void main(String[] args) {
        NavigableMap<Integer,String> ledger=new TreeMap<>();
        ledger.put(10,"queued");ledger.put(20,"review");ledger.put(30,"sent");
        NavigableMap<Integer,String> window=ledger.subMap(10,true,30,false);
        NavigableMap<Integer,String> snapshot=new TreeMap<>(window);
        window.put(20,"approved");ledger.put(25,"packed");
        System.out.println(window);System.out.println(snapshot);System.out.println(ledger.floorEntry(24).getKey());
        try{window.put(40,"outside");}catch(IllegalArgumentException rejected){System.out.println("range rejected");}
    }
}''','{10=queued, 20=approved, 25=packed}\n{10=queued, 20=review}\n20\nrange rejected','TreeMap predecessor lookup and insertion take O(log n) time. A live range view does not copy all matching entries, while building a snapshot retains O(k) entry data for k selected entries. Iterating the range still visits the entries requested.',
['State whether each endpoint is inclusive.','Do not describe a live view as an independent snapshot.','A range restriction is not an authorization policy.'],['java/treemap','java/collection-views','spring/pagination-bounds'],subject='java-collections')

put('bytebuffer-order','Java ByteBuffer byte order: decode the protocol before reading integers',
'A ByteBuffer byte order determines how multi-byte primitive values are assembled from their stored bytes.',[
('The bytes have a format, not a machine preference',['The receipt header uses four bytes with the value one in little-endian order. Reading the same bytes with the default big-endian order produces 16777216. Both reads are mechanically valid; only one matches the protocol. Set the agreed order explicitly before reading an integer.','The duplicate shares the same bytes but has its own position and order setting. The fixture changes the original to little-endian and observes that the duplicate still reads its own configured order. A buffer view is not a decoded value, and sharing storage is different from sharing cursor state.']),
('Bound the header first',['The parser rejects a header that is not exactly four bytes before reading. A larger message needs bounds for each field, declared payload length and total retained bytes. Treating a transmitted length as a trusted allocation request can turn an ordinary header parser into an oversized allocation path.','An unsigned field also needs a deliberate Java representation. Byte order does not solve signedness. See [[java/byte-streams|Byte input]] before assuming that an integer read validates a complete packet or verifies who sent it.'])],'''import java.nio.*;
public class ReceiptHeaderOrder {
    static int read(byte[] header) {
        if(header.length!=4)throw new IllegalArgumentException("four-byte header required");
        return ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN).getInt();
    }
    public static void main(String[] args) {
        byte[] bytes={1,0,0,0};ByteBuffer original=ByteBuffer.wrap(bytes);
        ByteBuffer view=original.duplicate();original.order(ByteOrder.LITTLE_ENDIAN);
        System.out.println(original.getInt());System.out.println(view.getInt());System.out.println(read(bytes));
        try{read(new byte[3]);}catch(IllegalArgumentException rejected){System.out.println("length rejected");}
    }
}''','1\n16777216\n1\nlength rejected','The fixed four-byte read has bounded time and storage. Wrapping shares the supplied byte array; it is not a defensive copy. Larger protocols must budget retained byte buffers and reject lengths before allocating or reading their declared payloads.',
['Use protocol byte order, not host assumptions.','Configure each view according to its read contract.','Validate field length before primitive access.'],['java/byte-streams','java/file-channels','java/foreign-memory'])

put('crc32-boundary','Java CRC32: detect a byte change without claiming authenticity',
'CRC32 computes a checksum of a byte sequence for detecting accidental changes; it is not proof of who produced that sequence.',[
('Compare the same encoded bytes',['The manifest fixture calculates the checksum of a UTF-8 record, checks it again without changing the bytes, then changes one byte and observes a different value. The comparison is on encoded bytes, not characters, because encoding and line-ending changes alter the stored representation.','A checksum match is useful evidence that an accidental transmission change was not observed by that check. It is not a guarantee that two different messages cannot share a checksum. A sender can also replace a payload and its unchecked checksum together.']),
('Choose the trust boundary separately',['The checksum object keeps mutable running state. Reset or create a fresh instance for an independent record, otherwise the result includes earlier bytes. The fixture uses a new instance per call so the record boundary is explicit.','When adversarial modification matters, define a signature or keyed authentication design and key ownership instead of upgrading a checksum label. [[java/secure-random-tokens|Random token material]] and authenticated transport solve other problems; neither makes an untrusted supplied CRC an authentication mechanism.'])],'''import java.nio.charset.StandardCharsets;
import java.util.zip.CRC32;
public class ManifestChecksum {
    static long checksum(byte[] bytes){CRC32 crc=new CRC32();crc.update(bytes);return crc.getValue();}
    public static void main(String[] args) {
        byte[] manifest="receipt=125".getBytes(StandardCharsets.UTF_8);
        long expected=checksum(manifest);System.out.println(expected==checksum(manifest));
        byte[] changed=manifest.clone();changed[changed.length-1]=(byte)'6';
        System.out.println(expected==checksum(changed));
    }
}''','true\nfalse','Checksum calculation takes O(b) time for b bytes and bounded checksum state. The fixture already holds the byte array; a streaming calculation can avoid retaining the entire file. No collision-resistance or authenticity guarantee is made.',
['Calculate over the exact bytes whose integrity you want to check.','Do not reuse running state across unrelated records accidentally.','Do not use an untrusted CRC as an authentication decision.'],['java/byte-streams','java/zip-path-validation','java/secure-random-tokens'])

put('messageformat-quotes','Java MessageFormat apostrophes: keep placeholders visible to the parser',
'MessageFormat interprets apostrophes as quoting syntax, so literal apostrophes in a message pattern require the correct escaping.',[
('Message text is a pattern',['The receipt pattern doubles its apostrophe so the final text reads Customer’s receipt with the customer’s identifier inserted at the placeholder. A second pattern deliberately quotes the placeholder braces and returns them literally. Translators editing that text are editing a small grammar, not an arbitrary string.','The sample uses an ASCII apostrophe in the actual pattern. A typographic apostrophe is another character and should not be substituted as a hidden parser fix. Test the exact pattern that will be shipped in the resource bundle.']),
('Formatting does not escape the output context',['The fixture inserts plain record labels and prints them as text. If a formatted message is later inserted into HTML or an SQL statement, MessageFormat does not supply the escaping or binding required for that different sink. Render text safely and keep database parameters separate.','Pin the locale when output stability matters, and avoid sharing a mutable formatter without a thread-ownership policy. [[java/resource-bundles|Resource bundles]] organize localized patterns; they do not validate every placeholder or automatically execute your translation tests.'])],'''import java.text.MessageFormat;
import java.util.Locale;
public class ReceiptMessagePattern {
    public static void main(String[] args) {
        MessageFormat receipt=new MessageFormat("Customer''s receipt: {0}",Locale.ROOT);
        MessageFormat literal=new MessageFormat("Pending '{0}'",Locale.ROOT);
        System.out.println(receipt.format(new Object[]{"R125"}));
        System.out.println(literal.format(new Object[]{"R125"}));
    }
}''',"Customer's receipt: R125\nPending {0}",'Pattern parsing and formatting depend on pattern size, argument count and chosen subformats. A single local formatter avoids shared mutable state but still allocates formatting objects. This fixture checks quoting, not an entire locale catalogue.',
['Double literal apostrophes in the pattern where required.','Test the actual translated patterns.','Formatting is not HTML escaping or SQL parameter binding.'],['java/resource-bundles','java/decimal-parse-boundary','spring/problem-details'])

put('countdown-latch','Java CountDownLatch: completion counting does not count successful work',
'A CountDownLatch releases waiting threads when its count reaches zero and cannot be reset for another batch.',[
('Release the obligation on every exit',['The import batch has two worker obligations. One succeeds and increments accepted; the other fails and records failure. Both decrement the latch in finally. The coordinator can then report one accepted record and one failed record without waiting forever for the failed worker.','The latch count records completion obligations, not business success. A loop that decrements only after a successful operation can hang when an exception exits the worker. Keep a separate result or failure channel so reaching zero cannot be mistaken for a successful import.']),
('Bound the wait in the actual service',['This program starts two small local threads and joins them after the latch completes. A real import needs a deadline and an interruption policy for stuck I/O. A timed-out coordinator cannot assume the workers stopped or their committed effects disappeared.','Reuse requires a new latch for a new batch. If participants change across several phases, [[java/phaser-registration|Phaser]] may describe the coordination better. Either primitive still needs an explicit [[java/cancellation|cancellation contract]] around tasks and external effects.'])],'''import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
public class ImportCompletionCount {
    public static void main(String[] args) throws Exception {
        CountDownLatch completed=new CountDownLatch(2);
        AtomicInteger accepted=new AtomicInteger(),failed=new AtomicInteger();
        Thread first=new Thread(()->{try{accepted.incrementAndGet();}finally{completed.countDown();}});
        Thread second=new Thread(()->{try{throw new IllegalStateException("bad record");}
            catch(IllegalStateException failure){failed.incrementAndGet();}finally{completed.countDown();}});
        first.start();second.start();completed.await();first.join();second.join();
        System.out.println("accepted="+accepted.get());System.out.println("failed="+failed.get());
        System.out.println("remaining="+completed.getCount());
    }
}''','accepted=1\nfailed=1\nremaining=0','The latch holds bounded coordination state while the fixture creates two threads and two counters. Waiting duration depends on worker completion; the latch supplies no deadline on its own. Retaining all individual failures would add storage proportional to the batch size.',
['Count down in finally for every registered completion obligation.','Keep success and failure evidence separately.','Do not reuse a completed latch for a second batch.'],['java/phaser-registration','java/cancellation','spring/async-boundaries'])

put('record-defensive-copy','Java records with arrays: copy on input and output',
'A record makes its component references final, but an array component remains mutable unless the record defines a defensive-copy policy.',[
('Protect both directions',['The batch record clones its incoming amounts array in the compact constructor. A caller then changes the original array without changing the record’s stored amount. The accessor also returns a clone, preventing a later caller from changing the record through the returned array.','Copying only in the constructor protects against the original reference but leaves the accessor as a mutation path. Copying only in the accessor leaves the caller’s original input reference connected to the stored array. Both directions are part of this ownership contract.']),
('Equality needs its own decision',['The fixture checks retained values and prints false when comparing two batches containing equal array values. The generated equality method treats an array component as an array object rather than promising element-by-element value equality for the batch. Decide whether that is appropriate before putting such records into sets or caches.','A clone of a primitive array copies its values. An object-array clone copies references, so nested mutable values need another policy. [[java/equals-hashcode|Equality contracts]] and [[java/collection-views|Shallow ownership]] become relevant when replacing the amounts with richer business objects.'])],'''public class DefensiveReceiptBatch {
    record Batch(int[] amounts) {
        Batch {amounts=amounts.clone();}
        public int[] amounts(){return amounts.clone();}
    }
    public static void main(String[] args) {
        int[] input={125,75};Batch batch=new Batch(input);input[0]=0;
        int[] output=batch.amounts();output[1]=0;
        System.out.println(batch.amounts()[0]);System.out.println(batch.amounts()[1]);
        System.out.println(batch.equals(new Batch(new int[]{125,75})));
    }
}''','125\n75\nfalse','Construction and each accessor call take O(n) time and allocate an O(n) array. Repeated accessor calls inside a loop can turn one traversal into repeated copying. A scalar query or explicitly immutable representation may fit a large batch better.',
['Final references do not make array contents immutable.','Copy both entry and exit paths when that is the ownership contract.','Do not assume generated array equality is element-wise.'],['java/records','java/equals-hashcode','spring/pagination-bounds'],release=17)

put('z-pattern-search','Java Z algorithm: find overlapping pattern matches in linear time',
'The Z algorithm records how many values at each position match the prefix of a sequence, allowing pattern matches to reuse earlier comparison work.',[
('Keep the pattern boundary unambiguous',['The search builds one integer sequence from the pattern, a negative separator and the text. UTF-16 code units are nonnegative, so the separator cannot be mistaken for part of either input. A literal character chosen as a separator could already occur in a user’s text and break the boundary.','The stored matching interval supplies a lower bound for comparisons inside it. The algorithm extends beyond that interval only when necessary. A match is reported when the prefix length reaches the entire pattern, so overlapping occurrences such as aba in ababa are retained.']),
('State what an offset measures',['Returned offsets count Java UTF-16 code units. They are not grapheme positions for a user-visible caret. The program rejects an empty pattern and caps both input lengths before allocating the combined sequence. Another API can choose an empty-pattern convention, but it must state it rather than inherit it accidentally.','The implementation materializes the input sequence and the Z array, then stores every match. A caller processing enormous text needs a different retention strategy. [[java/kmp-search|KMP search]] is useful when evaluating a streaming pattern workflow, while [[java/grapheme-boundaries|Grapheme boundaries]] address display offsets.'])],'''import java.util.*;
public class ReceiptPatternOffsets {
    static List<Integer> find(String pattern,String text) {
        if(pattern.isEmpty() || pattern.length()>100000 || text.length()>100000)throw new IllegalArgumentException("input bounds");
        int boundary=pattern.length();int[] values=new int[boundary+1+text.length()];
        for(int i=0;i<boundary;i++)values[i]=pattern.charAt(i);values[boundary]=-1;
        for(int i=0;i<text.length();i++)values[boundary+1+i]=text.charAt(i);
        int[] matched=new int[values.length];int left=0,right=0;
        List<Integer> offsets=new ArrayList<>();
        for(int index=1;index<values.length;index++) {
            if(index<right)matched[index]=Math.min(right-index,matched[index-left]);
            while(index+matched[index]<values.length && values[matched[index]]==values[index+matched[index]])matched[index]++;
            if(index+matched[index]>right){left=index;right=index+matched[index];}
            if(index>boundary && matched[index]>=boundary)offsets.add(index-boundary-1);
        }
        return offsets;
    }
    public static void main(String[] args) {
        System.out.println(find("aba","ababa"));System.out.println(find("#","a##"));
        try{find("","receipt");}catch(IllegalArgumentException rejected){System.out.println("empty pattern rejected");}
    }
}''','[0, 2]\n[1, 2]\nempty pattern rejected','For pattern length m and text length n, construction and matching take O(m+n) time and O(m+n) working storage. Storing k returned offsets takes O(k) more space. This is an in-memory search over code units, not a streaming or grapheme-aware implementation.',
['Use a separator outside the input alphabet.','Retain overlapping matches if the contract requires them.','Do not label UTF-16 offsets as user-visible character positions.'],['java/kmp-search','java/strings','java/grapheme-boundaries'],subject='java-dsa')

put('graph-bridges','Java graph bridges: track edge identity when parallel edges exist',
'A bridge is an undirected edge whose removal increases the number of connected components in the graph.',[
('Skip the parent edge, not the parent vertex',['The transport graph assigns one identity to each undirected edge and uses that identity on both adjacency entries. DFS skips only the exact edge used to reach the current vertex. If two parallel links connect the same vertices, the other link remains a valid return path and neither is a bridge.','Discovery order and the lowest reachable discovery order supply the bridge test. After visiting an unvisited neighbor, its low value is compared with the current discovery value. The fixture starts a new DFS for every unvisited vertex so a disconnected component is not silently omitted.']),
('The recursion limit is part of this implementation',['The API caps vertices at five hundred and edges at five thousand, validates both endpoints and returns sorted original edge IDs. It supports self-loops and parallel links. Larger graphs need an explicit stack or a measured recursion policy; changing the input bound without that review changes the failure risk.','A bridge describes graph connectivity, not a guarantee that a real network fails when that connection stops. Routing, capacity and external paths are different evidence. [[java/graph-dfs|DFS traversal]] and [[java/strong-components|Directed components]] answer related but distinct graph questions.'])],'''import java.util.*;
public class TransportBridgeEdges {
    static class Edge {final int target,id;Edge(int target,int id){this.target=target;this.id=id;}}
    static void visit(int vertex,int parentEdge,List<List<Edge>> graph,int[] discovered,int[] low,int[] clock,List<Integer> bridges) {
        discovered[vertex]=low[vertex]=++clock[0];
        for(Edge edge:graph.get(vertex)) {
            if(edge.id==parentEdge)continue;
            if(discovered[edge.target]==0) {
                visit(edge.target,edge.id,graph,discovered,low,clock,bridges);
                low[vertex]=Math.min(low[vertex],low[edge.target]);
                if(low[edge.target]>discovered[vertex])bridges.add(edge.id);
            } else low[vertex]=Math.min(low[vertex],discovered[edge.target]);
        }
    }
    static List<Integer> bridges(int vertices,int[][] links) {
        if(vertices<1 || vertices>500 || links.length>5000)throw new IllegalArgumentException("graph bounds");
        List<List<Edge>> graph=new ArrayList<>();for(int i=0;i<vertices;i++)graph.add(new ArrayList<>());
        for(int id=0;id<links.length;id++) {
            int[] edge=links[id];if(edge.length!=2 || edge[0]<0 || edge[0]>=vertices || edge[1]<0 || edge[1]>=vertices)throw new IllegalArgumentException("endpoint");
            graph.get(edge[0]).add(new Edge(edge[1],id));graph.get(edge[1]).add(new Edge(edge[0],id));
        }
        List<Integer> critical=new ArrayList<>();int[] discovered=new int[vertices],low=new int[vertices],clock={0};
        for(int vertex=0;vertex<vertices;vertex++)if(discovered[vertex]==0)visit(vertex,-1,graph,discovered,low,clock,critical);
        Collections.sort(critical);return critical;
    }
    public static void main(String[] args) {
        System.out.println(bridges(4,new int[][]{{0,1},{1,2},{2,0},{1,3}}));
        System.out.println(bridges(2,new int[][]{{0,1},{0,1}}));
    }
}''','[3]\n[]','DFS and adjacency construction take O(v+e) time and storage. Sorting b returned bridge IDs adds O(b log b) time. Recursive stack depth can reach v, which is why this fixture bounds vertices; a simple path is an adversarial depth case.',
['Skip the exact parent edge when parallel links are allowed.','Visit every disconnected component.','Do not omit stack depth from the input contract.'],['java/graph-dfs','java/strong-components','java/union-find'],subject='java-dsa')

put('matrix-chain','Java matrix-chain DP: minimize multiplication work without reordering matrices',
'Matrix-chain interval DP chooses the multiplication parentheses that minimize scalar work while preserving matrix order.',[
('Order is fixed, grouping is not',['The dimension sequence ten, twenty, thirty, forty describes three compatible matrices. Multiplying the first two before the third costs 18000 scalar multiplications; the other grouping costs 32000. The recurrence considers every split of an interval instead of applying a local cheapest-pair rule.','An interval containing one matrix costs zero because no multiplication is required. Larger intervals combine the two smaller interval costs with the product of their outer and split dimensions. The program returns the cost, not the parenthesized expression or the numeric matrix result.']),
('Bound arithmetic before allocating state',['The fixture accepts at most ten matrices and dimensions between one and one thousand. Multiplication is promoted to long before the product is formed. Those declared bounds keep every candidate cost within long; unrestricted dimensions would need checked arithmetic or a wider representation.','The algorithm assumes ordinary dense matrix multiplication as its cost model. Cache behavior, sparsity and different multiplication algorithms can change real runtime. [[java/jmh-benchmarks|Benchmark boundaries]] prevent an operation-count model from being mistaken for a measured performance ranking.'])],'''public class MatrixPlanCost {
    static long minimum(int[] dimensions) {
        if(dimensions.length<2 || dimensions.length>11)throw new IllegalArgumentException("chain size");
        for(int dimension:dimensions)if(dimension<1 || dimension>1000)throw new IllegalArgumentException("dimension");
        int count=dimensions.length-1;long[][] cost=new long[count][count];
        for(int length=2;length<=count;length++)for(int left=0;left+length<=count;left++) {
            int right=left+length-1;cost[left][right]=Long.MAX_VALUE;
            for(int split=left;split<right;split++) {
                long candidate=cost[left][split]+cost[split+1][right]
                    +(long)dimensions[left]*dimensions[split+1]*dimensions[right+1];
                cost[left][right]=Math.min(cost[left][right],candidate);
            }
        }
        return cost[0][count-1];
    }
    public static void main(String[] args) {
        System.out.println(minimum(new int[]{10,20,30,40}));System.out.println(minimum(new int[]{10,20}));
        try{minimum(new int[]{10,0,20});}catch(IllegalArgumentException rejected){System.out.println("dimension rejected");}
    }
}''','18000\n0\ndimension rejected','For n matrices the recurrence takes O(n cubed) time and O(n squared) storage. Returning the actual grouping needs split storage and reconstruction. This fixture caps n at ten and does not allocate or multiply the matrices themselves.',
['Preserve matrix order while changing parentheses.','Promote before multiplying dimensions.','Do not interpret a scalar-count estimate as a runtime benchmark.'],['java/tabulation','java/zero-one-knapsack','java/jmh-benchmarks'],subject='java-dsa')

def spring(slug,title,definition,sections,source,cost,mistakes,related,subject,proof):
 put(slug,title,definition,sections,source,'',cost,mistakes,related,subject=subject,release=21,spring=True,proof=proof)
def kit(name):return (ROOT/'work/spring-kit/src/main/java/in/aitrove/contracts'/f'{name}.java').read_text()

spring('spring-data-repositories','Spring Data JPA repositories: derive a query from mapped properties',
'A Spring Data JPA repository creates a proxy that implements persistence operations and query methods against mapped entity properties.',[
('Make the predicate readable',['StockRepository declares findByAvailableGreaterThanOrderByIdAsc. The suffix describes a strict greater-than predicate and an ascending identifier order; it refers to the Java entity property, not an arbitrary database column alias. The fixture changes account two to thirty available units, then a threshold of fifty returns accounts one and three. A threshold of one hundred returns no rows.','The repository is created with JpaRepositoryFactory and a shared EntityManager so its boundary is visible in a small fixture. The shared manager resolves the transaction-bound persistence context; it is not one manually shared mutable EntityManager used by multiple request threads. A Boot application normally registers repositories through its configured scanning path.']),
('Writes need a transaction policy',['The stock change executes within TransactionTemplate and becomes a dirty-checking update when the transaction commits. Fetching an entity and changing it after its context has closed does not imply the same outcome. [[spring/jpa-entity-lifecycle|Entity lifecycle]] explains managed and detached state.','A convenient method name does not prove an acceptable query plan. The result list in this fixture is small; a production stock search needs a limit, an index analysis and an explicit access policy. If the predicate grows into a long business sentence, a reviewed explicit query can be easier to maintain than an increasingly complicated derived name.'])],kit('StockRepository'),
'The test uses three H2 rows and checks values and ordering. Materializing r full entities retains O(r) application objects plus persistence-context state while managed. Actual database search cost depends on indexes, selectivity and the generated SQL; no production database plan is asserted.',
['Use mapped property names rather than guessing column names.','Do not assume changes to a detached entity are automatically committed.','Bound collection-returning queries before exposing them to arbitrary input.'],['spring/jpa-entity-lifecycle','spring/spring-data-projections','spring/keyset-pagination','java/interfaces'],'spring-data','RepositoryQueryTest.derivedPredicateUsesMappedPropertyAndOrder')

spring('spring-data-projections','Spring Data JPA projections: return selected fields without a full entity',
'A closed interface projection exposes selected mapped properties through accessor methods instead of returning a complete entity instance.',[
('Ask for the values the caller needs',['StockSummary exposes id and available. Its query still filters by available and orders by id, but the caller receives an interface view of the selected values. The test checks three results, the first identifier and its available count, then inspects Hibernate statistics: one prepared statement and zero loaded entities for that operation.','Those statistics are reset after seeding and belong to the pinned fixture. They establish that this query path avoids full entity loading here; they are not a promise that every interface projection, relationship accessor or expression-backed projection has identical SQL behavior. Inspect the actual path you deploy.']),
('A read shape is not an aggregate',['The projection is suitable for a bounded stock summary response. It has no business mutation method and is not a replacement for loading an aggregate when an operation requires its invariants. Read [[spring/jpa-fetch-plans|Fetch plans]] before adding nested associations, because a smaller Java interface alone does not establish smaller database work.','Projection getters use the entity property vocabulary. Returning selected values also does not authorize their disclosure: a caller still needs permission to read the stock record. [[spring/method-authorization|Service authorization]] belongs outside the choice of query return shape.'])],'''interface StockSummary {Long getId(); int getAvailable();}
List<StockSummary> findSummaryByAvailableGreaterThanOrderByIdAsc(int minimum);''',
'The fixture selects two values for each of three rows and verifies its Hibernate counters. Returning r projections retains O(r) result objects. Network size and database work can still grow with r. No nested-projection query, production plan or mutation-through-projection behavior is claimed.',
['Do not assume every projection avoids every entity load.','Measure nested relationship access separately.','Choose an aggregate boundary for writes rather than editing a summary view.'],['spring/spring-data-repositories','spring/jpa-fetch-plans','spring/method-authorization','java/records'],'spring-data','RepositoryQueryTest.projectionReadsValuesWithoutCreatingAFullEntity')

spring('keyset-pagination','Spring Data keyset pagination: continue after the last stable identifier',
'Keyset pagination resumes an ordered query after a cursor value instead of skipping an increasing number of earlier rows.',[
('Use a unique ordering key',['The fixture orders stock summaries by their unique ascending id and returns at most two with findTop2ByIdGreaterThanOrderByIdAsc. Starting after zero yields one and two; starting after two yields three; starting after three yields an empty result. The next cursor comes from the final returned row, not the number of items seen across earlier pages.','This is a deliberately narrow keyset: one non-null unique identifier. Sorting by a repeated timestamp alone would need another tie-breaking key and a predicate that agrees with the entire ordering. Changing the sort direction without changing the cursor predicate produces missing or repeated records.']),
('Do not imply a frozen snapshot',['Separate requests can observe inserts, deletes and changed filters between pages. A monotonic id cursor avoids offset shifting but does not create snapshot isolation. If the product promises a fixed export, define a snapshot or watermark contract rather than describing all pagination as equivalent. [[java/database-isolation|Transaction visibility]] covers a different boundary.','The repository has a fixed limit of two to make the test inspectable. An HTTP endpoint needs validation for cursor syntax, range and authorization; if it encodes multiple cursor fields, reject ambiguous or tampered representations. [[spring/pagination-bounds|Request bounds]] handles the earlier input layer.'])],'''List<StockSummary> findTop2ByIdGreaterThanOrderByIdAsc(long afterId);
// First request: afterId = 0. Continue with the last returned id.
// The source-kit test verifies [1, 2], then [3], then [].''',
'This method materializes at most two projection rows per call. A suitable index can support seeking by id, but the fixture checks results, not a production query plan or throughput. Arbitrary sorting, total counts, concurrent export consistency and signed cursor encoding remain separate features.',
['Include a unique tie-breaker when ordering values can repeat.','Build the next cursor from the last returned row.','Do not promise snapshot consistency across independent requests.'],['spring/spring-data-repositories','spring/spring-data-projections','spring/pagination-bounds','java/database-isolation'],'spring-data','RepositoryQueryTest.cursorKeepsIdOrderAndMovesPastThePreviousLastId')

spring('auto-configuration-registration','Spring Boot auto-configuration: register imports and let a user bean win',
'Boot auto-configuration contributes beans from registered configuration classes while conditions decide whether defaults should be supplied.',[
('Registration is part of the artifact',['ReceiptLabelAutoConfiguration supplies a ReceiptLabel bean with a default Receipt prefix. Its class name appears in META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports. The source kit includes that resource so registration can be checked instead of relying on a class that happens to be reached by component scanning.','ApplicationContextRunner tests the configuration in a small context. One test sees the default label, another supplies an Invoice label and checks that exactly one label bean remains. A third loads Boot import candidates and checks that the class is registered in the kit resource. These are distinct assertions.']),
('A default must have a replacement boundary',['ConditionalOnMissingBean makes the default back off when the user supplies the relevant type. That behavior is useful only if the library documents which bean can be replaced and what contract the replacement must satisfy. Broad scanning of library packages can register the same default through an unintended path.','This fixture has one configuration and one type. Real libraries with optional dependencies need classpath conditions, ordering rules and tests for absent dependencies. [[spring/auto-configuration|Condition basics]] introduces those decisions; [[spring/configuration-properties|Typed properties]] is a separate input boundary. The kit has not been published as a separately versioned starter.'])],kit('ReceiptLabelAutoConfiguration'),
'The context tests establish registration, default selection and back-off for the pinned Boot version. They do not test every competing library, classpath combination or packaged starter release. The bean retains one short prefix string; business work and dependency initialization are outside this fixture.',
['Include the import resource in the packaged artifact.','Test user-bean back-off rather than only default creation.','Keep auto-configuration out of broad component scanning.'],['spring/auto-configuration','spring/application-context','spring/configuration-properties','java/service-discovery'],'spring-boot','AutoConfigurationContractTest.defaultBeanRendersLabel, userBeanMakesDefaultBackOff and importsResourceRegistersTheConfiguration')

spring('webflux-sse','Spring WebFlux SSE: emit bounded receipt events and test HTTP encoding',
'A WebFlux controller can return a Flux of ServerSentEvent values that the HTTP message writer encodes as an event stream.',[
('Define the event contract',['ReactiveReceiptController accepts a count from one through five and emits R1 onward with an id and a receipt event name. Invalid counts throw a bad-request response before the Flux is returned. The mock HTTP test checks status, event-stream content type, ordered ids and data, and normal completion after three events.','The range emits a finite sequence with a ten-millisecond delay between items, not a durable event source. The delay has no production latency meaning. A raw Flux.interval can fail when downstream requests arrive slower than its ticks; this fixture uses a demand-aware finite range instead. This endpoint supplies neither persisted positions nor replay after a reconnect; a browser Last-Event-ID header cannot recover missed business events unless the server implements a replay contract.']),
('Keep blocking work out of the sequence',['The fixture does not query JPA in its emission callback. Putting a blocking repository call inside map would still block the executing thread; changing a return type does not convert that database driver into nonblocking I/O. [[spring/reactive-demand|Demand foundations]] and [[spring/spring-data-repositories|JPA repositories]] address separate execution models.','WebTestClient binds directly to the controller, exercising request mapping and codecs without a listening socket. It does not test server adapter queues, reverse-proxy buffering, disconnect behavior across a real network or deployment capacity. Test those paths before making delivery or memory claims.'])],kit('ReactiveReceiptController'),
'The fixture emits at most five events and retains no durable history. A deployed stream holds a subscription and connection for each client; proxy buffers, timeouts and upstream operator queues can add retained state. The mock HTTP test makes no throughput or end-to-end memory guarantee.',
['Validate the count before returning a successful streaming response.','Do not put blocking repository work on an event-loop path.','Do not claim replay or durable delivery from a delayed range publisher.'],['spring/reactive-demand','spring/webflux-cancellation','spring/rest-validation','java/flow-demand'],'spring-web','ReactiveHttpContractTest.emitsOrderedSseEventsAndCompletes and rejectsCountBeforeSuccessfulStreamHeaders')

spring('webflux-cancellation','Spring WebFlux cancellation: observe downstream cleanup without undoing work',
'Cancellation ends a subscriber’s interest in future signals and can trigger cleanup in the publisher chain.',[
('Observe a separate termination path',['The HTTP fixture requests an event stream of five values, receives one value and cancels. ReactiveReceiptController records its doOnCancel callback in an AtomicBoolean, and the test checks that callback ran. Normal completion is covered by a different test because completion and cancellation are different signals.','The callback records a fact; it does not close a database transaction or erase an event already sent. An import service must define who owns its upstream resources and which cleanup method belongs to that resource. A cancellation hook is not a generic compensation mechanism.']),
('Test the actual deployment boundary later',['WebTestClient uses a mock controller binding here. Cancelling its response-body subscriber verifies propagation within that chain, not the timing of TCP disconnect detection through a proxy. Real server and network behavior needs separate tests, including clients that stop reading without disconnecting.','Operators may buffer or prefetch. Work already accepted upstream can remain in flight when a downstream subscriber cancels, and a committed side effect remains committed. Keep cancellation-safe operations separate from irreversible writes. [[java/cancellation|Java task cancellation]] has comparable ownership questions but a different API.'])],'''var controller = new ReactiveReceiptController();
var response = WebTestClient.bindToController(controller).build()
    .get().uri("/contract/events?count=5").exchange()
    .expectStatus().isOk()
    .returnResult(new ParameterizedTypeReference<ServerSentEvent<String>>() {});
StepVerifier.create(response.getResponseBody()).expectNextCount(1)
    .thenCancel().verify(Duration.ofSeconds(3));
assertTrue(controller.cancelled.get());''',
'The checked chain has at most five scheduled values and no external resource ownership. Retained operator state and the delay scheduler are specific to this fixture. Network detection delay, pooled connections, cancellation races during writes and deployment load are not measured.',
['Separate cancellation cleanup from successful completion.','Do not interpret cancellation as rollback of completed side effects.','Test the real server and proxy path before promising disconnect timing.'],['spring/webflux-sse','spring/reactive-demand','spring/transaction-events','java/cancellation'],'spring-web','ReactiveHttpContractTest.downstreamCancellationReachesTheControllerSequence')

spring('jwt-resource-server','Spring Security JWT resource server: validate trust before checking scope',
'A JWT resource server authenticates a bearer token by verifying its signature and configured claims before applying endpoint authorization.',[
('Define what this API trusts',['ReceiptTokenDecoder trusts one RSA public key, one issuer and an audience containing receipt-api. The test creates temporary RSA keys in memory, signs local tokens, and exercises the actual security filter chain through MockMvc. A trusted token with receipt.read reaches the endpoint. Wrong signatures, issuers and audiences are rejected with 401, as is a token expired well beyond the validator clock-skew allowance.','The fixed public key is a fixture trust input. It is not a private signing key embedded in the application, a JWKS rotation implementation or a remote issuer lookup. The test signs its own tokens solely to make accepted and rejected inputs reproducible. Never accept an unverified issuer claim as a reason to fetch keys from an arbitrary caller-selected URL.']),
('Authentication does not grant every operation',['The security chain requires SCOPE_receipt.read for the GET route. A valid token with receipt.write is authenticated but receives 403 because it lacks the required authority. A request with no token receives 401. The test keeps these outcomes separate.','The route returns a fixed teaching receipt. A general read scope does not establish ownership of a particular tenant or receipt. [[spring/method-authorization|Service authorization]] can enforce another boundary, but resource-level permission still needs trusted identity and domain state. This page implements no login screen, authorization server, OIDC session or token refresh flow.'])],kit('ReceiptTokenDecoder'),
'The tests check seven local request outcomes with the pinned Spring Security libraries and in-memory keys. Signature verification has CPU cost per checked token; key retrieval, rotation, revocation, identity-store access and distributed clock behavior are outside this fixture. Stateless session configuration does not remove application authorization obligations.',
['Do not decode claims and call that signature verification.','Validate the API audience as well as the issuer.','Distinguish an invalid token from a valid token lacking an authority.'],['spring/security-filter-chain','spring/method-authorization','spring/password-encoding','java/secure-random-tokens'],'spring-security','JwtResourceServerContractTest')

spring('cache-eviction','Spring cache eviction: invalidate the same tenant key used by the read',
'Cache eviction removes an entry selected by the cache name and key so a later intercepted read can recompute its value.',[
('Use one key definition',['ReceiptCacheEdits uses a Key record containing tenant and id for both Cacheable and CacheEvict. The test reads tenant-a receipt seven and tenant-b receipt seven, changes only tenant-a, then checks that the next tenant-a read sees the new value while tenant-b retains its own value. Using id alone would collapse unrelated records into the same cache entry.','The service comes from an annotation-enabled Spring context. A direct object or self-invocation can bypass cache interception, just as other proxy-based concerns can be bypassed. [[spring/cache-keys|Cache key rules]] and [[spring/proxy-self-invocation|Proxy boundaries]] explain those separate failure paths.']),
('Eviction timing is not transaction durability',['The fixture stores values in a ConcurrentHashMap and uses a local ConcurrentMapCacheManager. By default the method completes before its matching entry is evicted. A failed method and an explicit beforeInvocation policy have different consequences; choose that policy deliberately rather than treating all invalidation annotations as identical.','This teaching store has no database transaction, expiry, capacity or cross-process replication. A database write that rolls back after cache changes can require transaction-aware cache design; another application instance has its own local state. The test cannot establish consistency across servers from one process-local map.'])],kit('ReceiptCacheEdits'),
'Local map access has expected constant-time lookup, with retained storage proportional to distinct keys. Neither the backing store nor the cache has a size limit or expiry in this fixture. Production use needs retention and invalidation policies plus an explicit consistency contract for concurrent reads and writes.',
['Match read and eviction keys, including tenant identity.','Call through the configured cache proxy.','Do not claim distributed consistency or bounded memory from a local map test.'],['spring/cache-keys','spring/transaction-events','spring/proxy-self-invocation','java/lru-cache'],'spring-production','CacheEvictionContractTest.proxiedEditEvictsOnlyTheMatchingTenantKey')

names={'java-advanced':'Foreign calls, binary formats and coordination','java-collections':'Bounded caches and ordered range views','java-dsa':'Pattern windows, graph cuts and interval planning','spring-data':'Repository queries and cursor-shaped reads','spring-boot':'Packaged configuration defaults','spring-web':'Event-stream encoding and cancellation','spring-security':'Bearer trust and scope checks','spring-production':'Key-matched cache invalidation'}
for subject in sorted({lookup[path]['subject'] for path in added}):
 hub=next(e for e in es if e['type']=='subject' and e['subject']==subject)
 name=names[subject]
 hub['data']['modules']=[m for m in hub['data']['modules'] if m['title']!=name]
 hub['data']['modules'].append({'title':name,'summary':'Follow the input contract, inspect failures and run the checked source.','lessons':[p for p in added if lookup[p]['subject']==subject]})
 hub['updated_at']=stamp
reverse={
 'java/foreign-memory':['java/native-linker'], 'java/shared-arena':['java/native-linker'],
 'java/blocking-queues':['java/flow-demand'], 'java/linkedhashmap':['java/lru-cache'],
 'java/treemap':['java/navigable-map-ranges'], 'java/file-channels':['java/bytebuffer-order','java/crc32-boundary'],
 'java/resource-bundles':['java/messageformat-quotes'], 'java/phaser-registration':['java/countdown-latch'],
 'java/records':['java/record-defensive-copy','spring/spring-data-projections'], 'java/kmp-search':['java/z-pattern-search'],
 'java/graph-dfs':['java/graph-bridges'], 'java/tabulation':['java/matrix-chain'],
 'spring/jpa-entity-lifecycle':['spring/spring-data-repositories'], 'spring/jpa-fetch-plans':['spring/spring-data-projections'],
 'spring/pagination-bounds':['spring/keyset-pagination'], 'spring/auto-configuration':['spring/auto-configuration-registration'],
 'spring/reactive-demand':['java/flow-demand','spring/webflux-sse','spring/webflux-cancellation'],
 'spring/security-filter-chain':['spring/jwt-resource-server'], 'spring/method-authorization':['spring/jwt-resource-server'],
 'spring/cache-keys':['spring/cache-eviction','java/lru-cache'], 'java/secure-random-tokens':['spring/jwt-resource-server'],
 'java/interfaces':['spring/spring-data-repositories'], 'java/cancellation':['spring/webflux-cancellation']}
for path,targets in reverse.items():
 e=lookup[path];marker='<h2>Extend the tested workflow</h2>'
 e['body']=e['body'].split(marker)[0]+marker+para('Continue with '+', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.')
 e['updated_at']=stamp
for hub in es:
 if hub['type']=='subject' and hub['path'].startswith(('java/','spring/')):
  paths={p for m in hub['data'].get('modules',[]) for p in m['lessons']}
  hub['body']=re.sub(r'This section contains \d+ (?:published |checked )?(?:lessons|pages)', 'This section contains '+str(len(paths))+' published lessons',hub['body'])
  if hub['path'].startswith('spring/'):
   lesson_links='<ul>'+''.join('<li><a href="/'+path+'">'+html.escape(lookup[path]['title'])+'</a></li>' for m in hub['data']['modules'] for path in m['lessons'])+'</ul>'
   hub['body']=re.sub(r'(<h2>Section lessons</h2>)[\s\S]*?(<h2>Continue learning</h2>)',lambda match:match[1]+lesson_links+match[2],hub['body'])
FILE.write_text(json.dumps(es,ensure_ascii=False,indent=2)+'\n')
(ROOT.parent.parent/'outputs/java-spring-third-additions.json').write_text(json.dumps({'added':added,'java':[p for p in added if p.startswith('java/')],'spring':[p for p in added if p.startswith('spring/')],'reciprocalPagesUpdated':len(reverse)},indent=2))
print('Added',len(added),'pages; reciprocal links updated on',len(reverse),'existing pages')
