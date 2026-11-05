"""Original Java additions; upsert only this batch and preserve all existing content."""
import copy, datetime, html, json, pathlib, uuid, re
ROOT=pathlib.Path(__file__).resolve().parents[1]
FILE=ROOT/'src/data/fixtures.json'
entries=json.loads(FILE.read_text()); lookup={e['path']:e for e in entries}; stamp=datetime.datetime.now(datetime.UTC).isoformat()
def p(s): return '<p>'+html.escape(s)+'</p>'
def code(s,lang='java'): return '<pre><code class="language-'+lang+'">'+html.escape(s.strip(),quote=False)+'</code></pre>'
def put(slug,title,definition,sections,source,output,cost,mistakes,related,subject='java-advanced',release=8):
 path='java/'+slug; body=p(definition)+p('The complete program targets Java '+str(release)+'. Compile it as one source file; its output is checked against the lesson.')
 for heading,paragraphs in sections: body+='<h2>'+heading+'</h2>'+''.join(p(s) for s in paragraphs)
 body+='<h2>Working program</h2>'+code(source)+'<h3>Output</h3>'+code(output,'text')+'<h2>Costs and boundaries</h2>'+p(cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in mistakes)+'</ul><h2>Read next</h2><p>'+', '.join('<a href="/'+s+'">'+html.escape(lookup.get(s,{}).get('title',s.split('/')[-1].replace('-',' ').capitalize()))+'</a>' for s in related)+'.</p>'
 e=copy.deepcopy(lookup['java/casts']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary=definition,body=body,subject=subject,tags=['java',slug],difficulty='Intermediate',sort_order=400,status='published',featured=False,published_at=stamp,updated_at=stamp)
 hub=next(x for x in entries if x['type']=='subject' and x['subject']==subject and x['path'].startswith('java/'))
 e['data']={'subject_root':'java/java','section_path':hub['path'],'content_format':'html','kind':'tutorial','java_release':release,'java_version':str(release)+'+','reading_minutes':max(4,round(len(re.sub('<[^>]*>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-java-source-kit.zip','related':[{'path':s,'title':lookup.get(s,{}).get('title',s.split('/')[-1])} for s in related],'seo_ready':True}
 if path in lookup: entries[entries.index(lookup[path])]=e
 else: entries.append(e)
 lookup[path]=e
 return path
added=[]
added.append(put('clock-injection','Java Clock: test expiry without sleeping',
'A Clock supplies instants and a time zone so application code can read time through an explicit dependency instead of a hidden system call.',
[('Define the expiry boundary',[
'A payment reservation expires at a stored Instant. The predicate uses now greater than or equal to expiry. Equality matters: switching to a strict greater-than comparison grants an extra instant at the boundary. That is a business decision, not a formatting preference.',
'Use an instant for an absolute deadline. A LocalDateTime has no offset and cannot identify a unique point on the timeline during an overlap. Inject the clock into the service constructor; tests can then use a fixed instant without waiting or changing machine time.'
]),('Separate civil time from elapsed time',[
'Clock.fixed returns the supplied instant whenever read. Clock.offset moves that view by a duration, which lets this fixture check both sides of an expiry boundary using the same reservation. Neither object simulates an operating system clock that ticks by itself.',
'For measuring elapsed latency inside one JVM, a monotonic time source such as System.nanoTime addresses a different problem. Wall time can change after synchronization. Do not use a fixed clock to conclude that concurrent timing or scheduler behavior has been tested.'
])],'''import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
public class ReservationExpiry {
    private final Clock clock;
    ReservationExpiry(Clock clock) { this.clock = clock; }
    boolean expired(Instant deadline) { return !clock.instant().isBefore(deadline); }
    public static void main(String[] args) {
        Instant deadline = Instant.parse("2026-01-12T12:00:00Z");
        Clock boundary = Clock.fixed(deadline, ZoneOffset.UTC);
        System.out.println(new ReservationExpiry(Clock.offset(boundary, Duration.ofSeconds(-1))).expired(deadline));
        System.out.println(new ReservationExpiry(boundary).expired(deadline));
    }
}''','false\ntrue','Each comparison is bounded work with constant application state. Storage precision can truncate timestamps, so test after converting to the database precision used in production. This fixture has no database and cannot establish that conversion contract.',
['Do not scatter Instant.now() through a service that needs reproducible tests.','Choose whether equality means expired.','A wall clock is not a monotonic latency counter.'],['java/date-time','java/test-boundaries','spring/constructor-injection'],subject='java'))
added.append(put('zone-transitions','Java daylight-saving transitions: reject gaps and choose overlaps',
'A ZoneRules instance maps local date-time values to valid offsets; a gap has no valid offset and an overlap can have two.',
[('A local appointment is not yet an instant',[
'A scheduler accepting a local appointment needs a region zone and a rule for daylight-saving changes. Automatically adjusting a nonexistent time can move a booking away from what the customer entered. Reject it when the application contract requires an exact local time.',
'This fixture uses known 2024 transitions in Europe/Paris. The March appointment has no matching offset. The October appointment has two, and each creates a different Instant from the same local fields. The region rules come from the runtime time-zone database; governments can change future rules.'
]),('Make the overlap policy visible',[
'An offset is a numeric displacement, not a region rule. Persist the selected instant and the region when both execution and later display matter. If a future appointment must stay at a civil time even after a rule change, store that civil intent separately and define when it is recalculated.',
'The program displays both overlap instants rather than silently selecting one. A production input flow should ask for or clearly specify the earlier or later offset. A blanket UTC conversion before examining the local-time ambiguity loses evidence the service needs to make that choice.'
])],'''import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.List;
public class AppointmentOffsets {
    public static void main(String[] args) {
        ZoneId zone = ZoneId.of("Europe/Paris");
        LocalDateTime gap = LocalDateTime.parse("2024-03-31T02:30:00");
        LocalDateTime overlap = LocalDateTime.parse("2024-10-27T02:30:00");
        System.out.println("gap offsets=" + zone.getRules().getValidOffsets(gap).size());
        List<ZoneOffset> offsets = zone.getRules().getValidOffsets(overlap);
        System.out.println("overlap offsets=" + offsets.size());
        for (ZoneOffset offset : offsets) System.out.println(overlap.toInstant(offset));
    }
}''','gap offsets=0\noverlap offsets=2\n2024-10-27T00:30:00Z\n2024-10-27T01:30:00Z','The fixture stores at most two offsets per query. Region rules and their cached data are runtime resources; do not model them as a fixed application-owned lookup table for every future date.',
['Do not treat LocalDateTime as a unique instant.','A fixed ZoneOffset does not include regional daylight-saving rules.','Test gaps and overlaps separately.'],['java/date-time','java/clock-injection','spring/configuration-properties'],subject='java'))
added.append(put('optional-evaluation','Java Optional: eager defaults and lazy suppliers',
'Optional.orElse evaluates its argument before the call, while orElseGet invokes its supplier only when the Optional is empty.',
[('An unused default can still do work',[
'A receipt lookup already found a cached value. Passing a fallback method to orElse does not postpone that method; Java evaluates the method argument even though Optional later returns the cached value. The fallback could allocate a document, query a database or fail.',
'The counter in this program records actual fallback calls. It is intentionally local and deterministic. orElseGet avoids the call on a present value, but writing a supplier that closes over an already-computed fallback will not undo the earlier computation.'
]),('Absence is a domain choice',[
'A supplier can return null, so the return value of orElseGet is not automatically non-null. If absence is an error, orElseThrow can express that boundary directly. Avoid using Optional merely to hide a missing value that the caller must handle explicitly.',
'The fixture uses a single thread. Adding suppliers with mutable shared counters needs synchronization, and deferring a remote lookup still needs a timeout and failure policy. Lazy evaluation controls when work starts; it does not make the work safe or inexpensive.'
])],'''import java.util.Optional;
public class ReceiptFallbackCalls {
    static int calls;
    static String loadArchive() { calls++; return "archive"; }
    public static void main(String[] args) {
        Optional<String> receipt = Optional.of("cached");
        System.out.println(receipt.orElse(loadArchive()));
        System.out.println(calls);
        System.out.println(receipt.orElseGet(ReceiptFallbackCalls::loadArchive));
        System.out.println(calls);
        System.out.println(Optional.<String>empty().orElseGet(ReceiptFallbackCalls::loadArchive));
        System.out.println(calls);
    }
}''','cached\n1\ncached\n1\narchive\n2','Optional selection itself is bounded work. The fallback cost depends on the operation supplied. Captured state can keep objects reachable longer than expected; a supplier is not a free replacement for designing the lookup lifecycle.',
['Do not assume an orElse argument is lazy.','Do not compute the fallback before creating its supplier.','Handle exceptions from the supplier at the intended boundary.'],['java/optional','java/lambdas','spring/object-provider'],subject='java'))
added.append(put('spliterator-contracts','Java Spliterator: split traversal without inventing characteristics',
'A Spliterator traverses elements and may partition the remaining traversal; its characteristic flags describe promises about that source.',
[('Split the remaining work',[
'A receipt batch is an ordered list. trySplit hands out a portion of the unvisited elements while leaving the rest on the original spliterator. Consume both parts to cover the batch. Consuming only the original after a successful split loses the elements transferred to the returned object.',
'This program checks the sum after consuming both parts; it does not assume a particular split size. A spliterator may return null, so callers must still consume the original when partitioning is unavailable. Splitting alone does not create threads or schedule tasks.'
]),('Flags are contracts',[
'ORDERED does not mean sorted. SIZED means the estimate is exact under its contract; SUBSIZED extends the size promise to splits. A custom spliterator that declares an unsupported property can cause downstream operations to rely on evidence it did not supply.',
'The fixture avoids source mutation during traversal. Fail-fast detection is not a concurrency protocol. A parallel stream also needs independent operations and a suitable source; adding parallel() to a shared mutable accumulator creates a separate correctness problem.'
])],'''import java.util.Arrays;
import java.util.Spliterator;
import java.util.concurrent.atomic.AtomicInteger;
public class PartitionedReceiptAmounts {
    public static void main(String[] args) {
        Spliterator<Integer> remaining = Arrays.asList(12, 18, 25, 45).spliterator();
        Spliterator<Integer> prefix = remaining.trySplit();
        AtomicInteger total = new AtomicInteger();
        if (prefix != null) prefix.forEachRemaining(total::addAndGet);
        remaining.forEachRemaining(total::addAndGet);
        System.out.println(total.get());
        System.out.println(remaining.hasCharacteristics(Spliterator.ORDERED));
    }
}''','100\ntrue','Traversal visits n elements in O(n) time. The sequential example keeps bounded accumulator state; the source list stores n elements. Actual split costs depend on the source, and a linked structure can partition differently from an array-backed one.',
['Consume both returned and remaining partitions.','Do not label unsorted data SORTED.','Splitting is not thread execution.'],['java/streams','java/arraylist','java/linkedlist']))
added.append(put('collector-key-collisions','Java toMap: reject or merge duplicate keys deliberately',
'Collectors.toMap accumulates stream elements into a map, and a duplicate key needs either an explicit merge rule or a visible failure.',
[('Choose what duplicate means',[
'Two receipt rows share a currency code. If the target represents total exposure per currency, summing amounts is appropriate. If the target represents one authoritative payment per identifier, keeping the first row would conceal inconsistent input. The merge function belongs to the domain contract.',
'The program first verifies that the two-argument collector rejects a duplicate, then supplies a sum rule and a TreeMap factory for reproducible key order. It uses checked integer addition so overflow is rejected rather than wrapping silently.'
]),('Parallel reduction adds another constraint',[
'A merge function used in parallel reduction must produce the intended result under grouping changes. Subtracting values in the merge function is not a valid substitute for adding them. Side effects on another map or counter also introduce ordering and concurrency dependencies.',
'The fixture contains positive bounded amounts. Real currency calculations need a documented unit and rounding rule, often BigDecimal or a checked integral minor-unit value. A collection operation does not validate currency scale or convert between currencies.'
])],'''import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.Collectors;
public class CurrencyExposure {
    static class Row {
        final String currency; final int minorUnits;
        Row(String currency, int minorUnits) { this.currency = currency; this.minorUnits = minorUnits; }
    }
    public static void main(String[] args) {
        List<Row> rows = Arrays.asList(new Row("INR", 120), new Row("INR", 80), new Row("USD", 50));
        try { rows.stream().collect(Collectors.toMap(row -> row.currency, row -> row.minorUnits)); }
        catch (IllegalStateException rejected) { System.out.println("duplicate rejected"); }
        Map<String,Integer> totals = rows.stream().collect(Collectors.toMap(
            row -> row.currency, row -> row.minorUnits, Math::addExact, TreeMap::new));
        System.out.println(totals);
    }
}''','duplicate rejected\n{INR=200, USD=50}','TreeMap insertion costs O(log k) for k distinct keys, so this collector uses O(n log k) time and O(k) map storage. The ordinary hash-map form has a different cost profile. Sorting is chosen for deterministic output, not claimed as a faster collector.',
['Do not silently overwrite an identifier that should be unique.','Make the merge function suitable for the reduction grouping.','Define money units before summing.'],['java/streams','java/hashmap','java/bigdecimal']))
added.append(put('stream-resource-lifetime','Java Stream.close: terminal traversal does not close every source',
'A Stream can have a close handler, but a terminal operation does not by itself invoke that handler.',
[('Traversal and resource release are different events',[
'A file-backed stream can hold a reader while elements are processed. Reaching count() or collecting the values is not a general resource-release protocol. Close the stream with try-with-resources when its source owns an external resource.',
'This fixture uses Stream.of and an onClose counter rather than opening a file, making the lifecycle distinction visible without depending on filesystem state. The count completes while the close counter remains zero; leaving the try block changes it to one.'
]),('Do not return ownership ambiguously',[
'A helper that returns a file-backed stream transfers a resource obligation to its caller. Document that obligation or collect the required bounded data inside the helper and close it there. Collecting an unbounded input is not a safe way to avoid documenting ownership.',
'A stream is single-use. Closing one also prevents later traversal, and exceptions in processing still require release. If traversal and closing both fail, try-with-resources records the closing failure as suppressed rather than replacing the original failure.'
])],'''import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Stream;
public class ReceiptStreamLifetime {
    public static void main(String[] args) {
        AtomicInteger closed = new AtomicInteger();
        try (Stream<String> receiptIds = Stream.of("R-21", "R-22").onClose(closed::incrementAndGet)) {
            System.out.println(receiptIds.count());
            System.out.println("before close=" + closed.get());
        }
        System.out.println("after close=" + closed.get());
    }
}''','2\nbefore close=0\nafter close=1','The example uses constant application state and a two-element source. A real lazy source can bound memory while still keeping descriptors open; memory usage and descriptor lifetime require separate checks.',
['Do not assume collect() closes a Files.lines stream.','Do not return a resource-backed stream without explaining who closes it.','Do not reuse a consumed stream.'],['java/files','java/try-with-resources','java/streams']))
added.append(put('thread-local-cleanup','Java ThreadLocal: clear request state on reused worker threads',
'A ThreadLocal stores a value associated with a thread, so a pool worker can retain that value after the request that set it finishes.',
[('A pool changes the lifetime',[
'A request identifier is useful for local logging, but a pooled thread normally lives longer than one request. If cleanup is skipped, the next task can observe the previous identifier. The error is an ownership mismatch: request state was stored in worker-owned storage.',
'This program uses a single-thread executor to make worker reuse deterministic. The first task installs an identifier and removes it in finally; the second task reads null. Clearing only on a successful path leaves stale state when processing throws.'
]),('Context does not travel automatically',[
'ThreadLocal values are not a transaction or an authorization mechanism. Moving work to another executor does not automatically transfer the intended value, and blindly copying context can transfer credentials beyond their lifetime. Pass ordinary arguments when that ownership is easier to inspect.',
'The fixture waits for each Future and shuts down its executor. It tests cleanup, not every interleaving in a multi-worker pool. A production wrapper should restore an earlier value when nested operations share a thread, rather than always destroying another caller’s context.'
])],'''import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
public class RequestContextCleanup {
    static final ThreadLocal<String> REQUEST = new ThreadLocal<>();
    public static void main(String[] args) throws Exception {
        ExecutorService worker = Executors.newSingleThreadExecutor();
        try {
            System.out.println(worker.submit(() -> {
                REQUEST.set("receipt-71");
                try { return REQUEST.get(); }
                finally { REQUEST.remove(); }
            }).get());
            System.out.println(worker.submit(() -> REQUEST.get()).get());
        } finally { worker.shutdownNow(); }
    }
}''','receipt-71\nnull','One value is stored per participating thread while the context exists. A large object stored there can remain reachable through a long-lived worker. remove() releases this thread’s association, but it does not erase copies of the data held elsewhere.',
['Place cleanup in finally.','Do not treat thread-local values as authenticated identity.','Account for nested context and restore an existing value when needed.'],['java/executors','java/scoped-values','spring/async-boundaries']))
added.append(put('executor-rejection','Java bounded executors: test saturation and rejected work',
'A ThreadPoolExecutor with a bounded queue can reject a submitted task when its workers and queue cannot accept more work.',
[('Backlog needs a limit',[
'An importer with one worker and one queue slot can hold one running task and one waiting task. A third submission must meet an explicit rejection rule. An unbounded queue changes the failure mode to growing memory and delay; it does not create extra processing capacity.',
'The fixture blocks the worker on a latch, fills the queue, and checks AbortPolicy rejection. It then releases the worker in finally. That arrangement controls saturation without relying on sleeps or guessing how quickly a worker starts.'
]),('Choose what the caller observes',[
'CallerRunsPolicy moves execution onto the submitting thread, which can slow admission but may also block an HTTP request or event-loop thread. Silently discarding a task can lose work while the caller believes it was accepted. Neither policy is universally correct.',
'A queue limit does not supply durable storage. If the JVM exits, queued work disappears. A service that promises eventual processing needs persistence and replay semantics outside this local executor demonstration.'
])],'''import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
public class ImportAdmission {
    public static void main(String[] args) throws Exception {
        CountDownLatch release = new CountDownLatch(1);
        ThreadPoolExecutor worker = new ThreadPoolExecutor(1, 1, 0, TimeUnit.SECONDS,
            new ArrayBlockingQueue<Runnable>(1), new ThreadPoolExecutor.AbortPolicy());
        try {
            worker.execute(() -> { try { release.await(); } catch (InterruptedException stop) { Thread.currentThread().interrupt(); } });
            worker.execute(() -> {});
            try { worker.execute(() -> {}); }
            catch (RejectedExecutionException rejected) { System.out.println("capacity rejected"); }
            System.out.println("queued=" + worker.getQueue().size());
        } finally { release.countDown(); worker.shutdown(); }
        if (!worker.awaitTermination(5, TimeUnit.SECONDS)) throw new AssertionError("worker did not stop");
    }
}''','capacity rejected\nqueued=1','This queue holds at most one task and the pool has one worker. Retained task closures can still reference large payloads, so a bounded task count is not an exact byte budget. This test checks admission and termination, not production throughput.',
['Do not hide rejected work behind a success response.','Bound payload size as well as queue length.','Release test latches even when an assertion fails.'],['java/executors','java/blocking-queues','spring/async-boundaries']))
added.append(put('secure-random-tokens','Java SecureRandom: token entropy, encoding and comparison boundaries',
'SecureRandom produces bytes from a cryptographic random generator; a token format must preserve those bytes and define its own validation rules.',
[('Count bytes before formatting',[
'This fixture generates 24 bytes and encodes them with unpadded URL-safe Base64. Twenty-four bytes represent 192 bits of raw random input. That number does not prove an entire authentication scheme is secure: token storage, expiry, transmission and lookup behavior remain separate requirements.',
'The output check uses the decoded byte count rather than a fixed token string. Tests should never expect a particular random value or seed a production token generator merely to make a screenshot reproducible.'
]),('Do not compare the wrong representation',[
'Encoding is reversible; it does not hash or encrypt a token. Validate the transport format before decoding and handle malformed input as rejected input. When comparing secret byte strings of an expected length, MessageDigest.isEqual is preferable to writing an early-exit byte loop.',
'The fixture compares a token to its own decoded bytes, which verifies a round trip only. It does not implement login, token rotation or rate limiting. A database should avoid storing bearer credentials in readable form where a lookup digest can meet the design requirements.'
])],'''import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
public class OpaqueReceiptToken {
    public static void main(String[] args) {
        byte[] entropy = new byte[24];
        new SecureRandom().nextBytes(entropy);
        String encoded = Base64.getUrlEncoder().withoutPadding().encodeToString(entropy);
        byte[] decoded = Base64.getUrlDecoder().decode(encoded);
        System.out.println("characters=" + encoded.length());
        System.out.println("bytes=" + decoded.length);
        System.out.println(MessageDigest.isEqual(entropy, decoded));
    }
}''','characters=32\nbytes=24\ntrue','Generation and encoding scale with token length; this fixed fixture uses bounded buffers. Provider initialization can have different costs from later calls. Benchmark the actual generator and deployment rather than treating a tiny example as a latency guarantee.',
['Do not use Random for bearer token generation.','Base64 is not encryption.','Never log the generated credential as routine diagnostic data.'],['java/byte-streams','java/test-boundaries','spring/password-encoding']))
added.append(put('segment-tree','Java segment tree: range sums with checked updates',
'A segment tree stores aggregate values over nested intervals so a point update and a range-sum query can each visit logarithmically many nodes.',
[('Use one interval convention',[
'A stock ledger needs the total quantity for a contiguous range of warehouse slots after individual corrections. This implementation uses half-open intervals: start is included and end is excluded. An empty range returns zero; a reversed or out-of-bounds range is rejected.',
'The tree uses an iterative layout with leaves starting at index n. It does not require n to be a power of two for this sum query. Parent values are rebuilt from child sums. Long storage prevents ordinary int-sum overflow for this bounded fixture, but arbitrary long inputs still need an overflow policy.'
]),('Update ownership is local',[
'An update replaces one leaf rather than adding a delta, then recomputes its ancestors. A caller that mistakes replacement for increment will get plausible but incorrect totals. The test changes one warehouse from five to nine and checks the new sum.',
'This class is not thread-safe. A concurrent query can observe part of an update. Protect the complete tree operation with a lock or choose a versioned structure when readers need a consistent snapshot; marking the array reference volatile does not make its element mutations atomic as a group.'
])],'''public class WarehouseRangeTotals {
    private final int size; private final long[] tree;
    WarehouseRangeTotals(int[] quantities) {
        size = quantities.length;
        if (size == 0 || size > 1000000) throw new IllegalArgumentException("size");
        tree = new long[2 * size];
        for (int index = 0; index < size; index++) tree[size + index] = quantities[index];
        for (int node = size - 1; node > 0; node--) tree[node] = tree[2 * node] + tree[2 * node + 1];
    }
    void replace(int index, int value) {
        if (index < 0 || index >= size) throw new IndexOutOfBoundsException();
        int node = index + size; tree[node] = value;
        while ((node /= 2) > 0) tree[node] = tree[2 * node] + tree[2 * node + 1];
    }
    long sum(int start, int end) {
        if (start < 0 || end < start || end > size) throw new IndexOutOfBoundsException();
        long total = 0;
        for (int left = start + size, right = end + size; left < right; left /= 2, right /= 2) {
            if ((left & 1) != 0) total += tree[left++];
            if ((right & 1) != 0) total += tree[--right];
        }
        return total;
    }
    public static void main(String[] args) {
        WarehouseRangeTotals stock = new WarehouseRangeTotals(new int[]{3, 5, 2, 7, 4});
        System.out.println(stock.sum(1, 4));
        stock.replace(1, 9); System.out.println(stock.sum(1, 4));
        System.out.println(stock.sum(2, 2));
        try { stock.sum(4, 2); } catch (IndexOutOfBoundsException rejected) { System.out.println("range rejected"); }
    }
}''','14\n18\n0\nrange rejected','Construction is O(n), queries and point replacements are O(log n), and the array stores 2n long values. This version supports sums and point replacement only; lazy range updates need different state and are not implemented here.',
['Do not mix inclusive and half-open endpoints.','Point replacement is not a delta update.','Protect a whole mutation when concurrent snapshots matter.'],['java/fenwick-tree','java/arrays','java/multi-index-invariants'],subject='java-dsa'))
added.append(put('coin-change','Java minimum coin change: reachable states and impossible totals',
'Minimum coin change uses earlier reachable amounts to compute the smallest number of reusable denominations that can form a target total.',
[('An unreachable state is not zero',[
'A voucher issuer supports denominations three and five. It must find the minimum voucher count for an exact total, or report that no combination exists. Initializing every state to zero would make nonexistent predecessor states look like free money.',
'The recurrence starts at zero vouchers for total zero and marks other totals unreachable. For each total it considers every denomination that fits. The resulting state represents exact totals with unlimited reuse of the supplied positive denominations.'
]),('Input bounds are part of the algorithm',[
'A denomination of zero creates a self-dependency and a negative one violates the recurrence. Reject both. The target is capped at one million to bound allocation and prevent target-plus-one overflow in this implementation.',
'This is not a greedy algorithm. Choosing the largest denomination first can miss a better combination or fail when a smaller-first combination exists. A bounded supply of each denomination is another problem and needs a count-sensitive state transition.'
])],'''import java.util.Arrays;
public class VoucherMinimum {
    static int minimum(int[] denominations, int target) {
        if (target < 0 || target > 1000000 || denominations.length == 0) throw new IllegalArgumentException("target or coins");
        for (int coin : denominations) if (coin <= 0) throw new IllegalArgumentException("coin");
        int missing = target + 1;
        int[] best = new int[target + 1]; Arrays.fill(best, missing); best[0] = 0;
        for (int amount = 1; amount <= target; amount++) {
            for (int coin : denominations) if (coin <= amount && best[amount - coin] != missing)
                best[amount] = Math.min(best[amount], best[amount - coin] + 1);
        }
        return best[target] == missing ? -1 : best[target];
    }
    public static void main(String[] args) {
        System.out.println(minimum(new int[]{3, 5}, 11));
        System.out.println(minimum(new int[]{3, 5}, 4));
        System.out.println(minimum(new int[]{3, 5}, 0));
        try { minimum(new int[]{0, 5}, 9); } catch (IllegalArgumentException rejected) { System.out.println("coin rejected"); }
    }
}''','3\n-1\n0\ncoin rejected','For target t and k denominations the running time is O(tk) and state storage is O(t). Duplicate denominations repeat work without changing the optimum. The code returns the count only; reconstructing an actual voucher list needs predecessor information.',
['Do not initialize unreachable amounts as zero.','Reject non-positive denominations.','Unlimited reuse and bounded inventory need different transitions.'],['java/tabulation','java/zero-one-knapsack','java/greedy-intervals'],subject='java-dsa'))
# Include new canonical pages in only their own Java section; existing module groups are preserved.
for subject in sorted({lookup[path]['subject'] for path in added}):
 hub=next(e for e in entries if e['type']=='subject' and e['subject']==subject and e['path'].startswith('java/'))
 lessons=[s for s in added if lookup[s]['subject']==subject]
 name={'java':'Time and evaluation boundaries','java-advanced':'Traversal, resources and worker ownership','java-dsa':'Range sums and exact change'}[subject]
 hub['data']['modules']=[m for m in hub['data']['modules'] if m['title'] not in ('Time, traversal and ownership boundaries',name)]
 hub['data']['modules'].append({'title':name,'summary':'Test exact boundaries, resource ownership and bounded work.','lessons':lessons})
 hub['updated_at']=stamp
FILE.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
(ROOT.parent.parent/'outputs/java-spring-java-additions.json').write_text(json.dumps({'added':added,'count':len(added)},indent=2))
print('Java additions:',len(added))
