"""Add original Java file-channel and JVM management lessons."""

import copy
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {row["path"]: row for row in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="filechannel-write-completion", title="Java FileChannel.write: finish the buffer before reporting success", group="File channel boundaries", release=11,
         definition="A FileChannel.write call advances a ByteBuffer by the number of bytes it actually wrote. A caller that needs the entire payload must loop until the buffer has no remaining bytes.",
         details="The channel is opened with CREATE_NEW so an existing manifest cannot be overwritten by this helper. The buffer wraps bytes already owned by the caller; the caller must not mutate that array during the write. A zero-byte write is treated as lack of progress rather than an excuse to spin forever. Closing the channel releases its handle but is not the same as an explicit durability request. If the write fails halfway, a partial new file may remain; the caller owns cleanup or should stage to a temporary name before publication.",
         case="A receipt batch is encoded into 47,000 bytes. One write returns after 16,384 bytes. Treating that return as completion publishes a truncated batch. The loop continues from the buffer's new position and only returns after all bytes have been accepted by the channel. It still does not claim that the data survived a power failure.",
         code='''import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ManifestChannelWriter {
    public static void create(Path destination, byte[] payload) throws IOException {
        try (FileChannel channel = FileChannel.open(destination,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer pending = ByteBuffer.wrap(payload);
            while (pending.hasRemaining()) {
                if (channel.write(pending) == 0) throw new IOException("Channel made no write progress");
            }
        }
    }
}''',
         cost="The loop writes B bytes in O(B) I/O work and uses O(1) extra application storage because ByteBuffer wraps the caller's array. Device and filesystem costs dominate. A staged publish adds another file operation but prevents readers from opening a half-written final name.",
         mistakes=["Do not assume one write drains a ByteBuffer.", "Do not mutate the wrapped byte array during the write.", "Do not call close alone a full durability or publication guarantee."],
         related=["java/bytebuffer-flip-compact-state", "java/atomic-file-publication", "java/files"]),
    dict(slug="filechannel-positioned-exact-read", title="Java positioned FileChannel.read: detect a short record without moving the cursor", group="File channel boundaries", release=11,
         definition="FileChannel.read(dst, position) reads from an explicit file offset without changing the channel's current position. A fixed-width record reader must still handle partial reads and end of file.",
         details="This method validates the requested range and allocates only the bounded record size. Each call uses the initial offset plus the buffer's current position, so a partial read resumes at the correct byte. It throws EOFException if the record ends early and rejects a zero-progress read rather than spinning forever. Concurrent changes to the underlying file are outside this method's snapshot contract; a writer could replace bytes between calls. Use an immutable published file or an application version check when a coherent multi-record view matters.",
         case="An index says that receipt 47 begins at byte 8,192 and occupies 64 bytes. A first read returns only 23. The second read must start at byte 8,215, not at the channel's unrelated shared cursor. If the file ends after 49 bytes, the reader reports an incomplete record rather than returning a padded array.",
         code='''import java.io.EOFException;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class IndexedReceiptReader {
    public static byte[] read(Path archive, long offset, int width) throws IOException {
        if (offset < 0 || width < 0 || width > 47_000 || offset > Long.MAX_VALUE - width) {
            throw new IllegalArgumentException("Invalid record range");
        }
        ByteBuffer record = ByteBuffer.allocate(width);
        try (FileChannel channel = FileChannel.open(archive, StandardOpenOption.READ)) {
            while (record.hasRemaining()) {
                int count = channel.read(record, offset + record.position());
                if (count < 0) throw new EOFException("Receipt record is incomplete");
                if (count == 0) throw new IOException("Channel made no read progress");
            }
        }
        return record.array();
    }
}''',
         cost="Reading W bytes takes O(W) I/O work and O(W) memory for the result, capped here at 47,000. Positioned reads avoid a shared cursor but do not remove disk contention or make concurrent file mutations atomic.",
         mistakes=["Do not advance a shared channel position by accident when using positioned reads.", "Do not return a zero-padded buffer after early EOF.", "Do not treat multiple positioned reads as an atomic file snapshot."],
         related=["java/bytebuffer-order", "java/filechannel-write-completion", "java/atomic-file-publication"]),
    dict(slug="filechannel-transfer-progress", title="Java FileChannel.transferTo: verify the byte count on every pass", group="File channel boundaries", release=11,
         definition="FileChannel.transferTo requests a byte range be copied to another channel. A return smaller than the requested count is permitted, so a complete copy needs explicit progress accounting.",
         details="The method creates a new destination, captures the source size, and advances by the actual transferred count. It fails on zero progress to avoid an infinite loop. The size is only an observation: if another process changes the source during transfer, the result may not represent one stable version. For reliable publication, copy from an immutable source into a staged destination and then apply an accepted move contract. A failed transfer can leave a partial destination, so the owner must remove or quarantine it.",
         case="A 47-megabyte archive is copied to a new review location. A transfer call moves only part of the requested range. Without the loop, the review location has a plausible filename but missing tail bytes. The loop checks every returned count; it does not claim that this operation verifies content identity or durability.",
         code='''import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ArchiveChannelTransfer {
    public static long copy(Path source, Path destination) throws IOException {
        try (FileChannel input = FileChannel.open(source, StandardOpenOption.READ);
             FileChannel output = FileChannel.open(destination,
                 StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            long expected = input.size();
            long copied = 0;
            while (copied < expected) {
                long count = input.transferTo(copied, expected - copied, output);
                if (count <= 0) throw new IOException("Transfer stopped before expected size");
                copied += count;
            }
            return copied;
        }
    }
}''',
         cost="The method performs O(B) data movement for B bytes and uses O(1) application buffer space. An operating system may optimize some transfers, but that is platform-dependent. File creation and failure cleanup remain separate costs.",
         mistakes=["Do not assume one transferTo call copies its full count.", "Do not trust a size sampled before concurrent mutation as a snapshot.", "Do not leave a partial destination available as a valid archive."],
         related=["java/filechannel-write-completion", "java/atomic-file-publication", "java/files"]),
    dict(slug="filechannel-force-durability", title="Java FileChannel.force: distinguish written bytes from forced storage", group="File channel boundaries", release=11,
         definition="FileChannel.force requests that changes made through the channel reach the storage device. Passing true includes relevant file metadata; it does not make a multi-step file publication atomic.",
         details="The method writes a complete byte buffer through one channel and calls force(true) before closing it. A successful write call only says the channel accepted bytes; the force call is a separate durability boundary whose guarantees depend on the storage device and filesystem. An atomic rename is a different visibility boundary. Some filesystems need additional directory handling for crash-safe name persistence, which this example does not provide. Document the platform contract before claiming crash recovery.",
         case="A depot stages a 47,000-byte manifest before making it visible. A write loop completes, then force(true) requests persistence of its content and metadata. The caller may next use a same-filesystem atomic move. If the process fails before the move, the staged file remains unpublished; if storage ignores or cannot guarantee a flush, the application must not promise stronger durability than the platform provides.",
         code='''import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class DurableManifestStage {
    public static void write(Path stagingFile, byte[] bytes) throws IOException {
        try (FileChannel channel = FileChannel.open(stagingFile,
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer pending = ByteBuffer.wrap(bytes);
            while (pending.hasRemaining()) {
                if (channel.write(pending) == 0) throw new IOException("Staging write stalled");
            }
            channel.force(true);
        }
    }
}''',
         cost="Writing B bytes remains O(B). A force can add a high-latency storage synchronization and reduce throughput if called for every tiny record. Batching changes can improve throughput but widens the amount of data at risk between flushes.",
         mistakes=["Do not equate write completion with forced persistence.", "Do not equate force(true) with an atomic rename.", "Do not promise crash-safe directory naming without a platform-specific contract."],
         related=["java/filechannel-write-completion", "java/atomic-file-publication", "java/files"]),
    dict(slug="filechannel-lock-region", title="Java FileLock: coordinate one byte range with a shared protocol", group="File channel boundaries", release=11,
         definition="A FileLock represents a lock on a region of a file held through a channel. It coordinates only participants that honor the same locking protocol, and platform behavior for other writers can differ.",
         details="This writer takes an exclusive lock on one byte, writes a single-byte status at position zero, and releases the lock in a try-with-resources scope. It deliberately keeps the critical section short. Another lock on an overlapping range in the same JVM may fail with OverlappingFileLockException rather than wait, while another process may wait or observe platform-specific behavior. A lock is not a substitute for validating file ownership or making a multi-file transaction. The path still needs an access-control policy.",
         case="Two depot processes update a one-byte handoff marker. Both agree to lock range [0,1) before writing. If one process skips that protocol, the lock cannot make its write safe. If the marker needs a richer state transition, a database transaction or atomic file publication may be a better fit than extending the locked section around unrelated work.",
         code='''import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class HandoffMarkerLock {
    public static void mark(Path marker, byte status) throws IOException {
        try (FileChannel channel = FileChannel.open(marker,
                StandardOpenOption.CREATE, StandardOpenOption.WRITE);
             FileLock held = channel.lock(0, 1, false)) {
            ByteBuffer update = ByteBuffer.wrap(new byte[] {status});
            if (channel.write(update, 0) != 1) throw new IOException("Marker update incomplete");
        }
    }
}''',
         cost="The update is O(1) data work, but lock acquisition can wait indefinitely under contention. A short locked region reduces wait time. The lock and channel consume operating-system resources until closed.",
         mistakes=["Do not assume nonparticipating writers are stopped on every platform.", "Do not expect an overlapping lock in the same JVM to queue politely.", "Do not hold the lock across slow remote calls."],
         related=["java/atomic-file-publication", "java/filechannel-write-completion", "java/jdbc-transactions"]),
    dict(slug="filechannel-truncate-recovery", title="Java FileChannel.truncate: cut only after validating the recovery offset", group="File channel boundaries", release=11,
         definition="FileChannel.truncate reduces a file to a requested size when it is larger. A recovery routine must validate that offset against a known complete-record boundary before deleting the tail.",
         details="The method refuses negative offsets and offsets beyond the current file size, then truncates and forces the channel. It cannot discover the last valid record by itself. That boundary must come from a separately validated record format or checksum scan. Truncation is destructive, and a concurrent writer can make a size observation stale. Stop writers and capture a backup or quarantine copy before recovery. A channel's current position may be adjusted by truncation, so code that continues writing should set its intended position explicitly.",
         case="An append-only receipt log ends with a torn record. A scanner verifies all complete records through byte 8,192 and reports that exact offset. Recovery stops writers, keeps a copy of the damaged tail for inspection, and cuts the active log at 8,192. Guessing the offset from the last newline would be unsafe for a binary format.",
         code='''import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

public class ReceiptLogTailRecovery {
    public static void cutToValidatedBoundary(Path log, long completeBytes) throws IOException {
        if (completeBytes < 0) throw new IllegalArgumentException("Negative boundary");
        try (FileChannel channel = FileChannel.open(log, StandardOpenOption.WRITE)) {
            if (completeBytes > channel.size()) {
                throw new IllegalArgumentException("Boundary is beyond current file");
            }
            channel.truncate(completeBytes);
            channel.force(true);
        }
    }
}''',
         cost="The API request is O(1) in application work, but filesystem work and a forced flush can be expensive. Validating the last complete record may require O(N) scanning. Never trade that validation away to make recovery appear faster.",
         mistakes=["Do not infer a valid record boundary from size alone.", "Do not truncate while an uncontrolled writer is appending.", "Do not assume the channel position remains useful for the next write."],
         related=["java/filechannel-force-durability", "java/atomic-file-publication", "java/bounded-line-reader"]),
    dict(slug="asynchronousfilechannel-buffer-lifetime", title="Java AsynchronousFileChannel: own the buffer through completion", group="File channel boundaries", release=11,
         definition="AsynchronousFileChannel.read starts an operation and returns a Future for its byte count. The destination ByteBuffer belongs to that operation until completion is observed.",
         details="The method opens a channel, starts one positioned read, waits for completion, and then extracts exactly the returned bytes. Waiting on Future.get blocks this caller, so the example demonstrates the buffer and channel lifetime rather than claiming a throughput gain. A truly concurrent workflow can submit multiple independent reads with separate buffers and a bounded admission policy. A completed read may contain fewer bytes than requested; a negative count means end of file. On interruption, the method restores the thread's interrupt flag and closes the channel; do not reuse the buffer while an unfinished operation might still reference it.",
         case="A review service requests up to 47,000 bytes from an archive. It must not hand the same buffer to another read just because the Future was returned. The code waits, then copies the actual byte count. If the service needs an exact record, it uses a loop or the positioned exact-reader lesson rather than padding the short result.",
         code='''import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.AsynchronousFileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;

public class ArchiveAsyncRead {
    public static byte[] readOnce(Path archive, long offset, int capacity)
            throws IOException, ExecutionException, InterruptedException {
        if (offset < 0 || capacity < 0 || capacity > 47_000) {
            throw new IllegalArgumentException("Invalid read range");
        }
        ByteBuffer destination = ByteBuffer.allocate(capacity);
        try (AsynchronousFileChannel channel = AsynchronousFileChannel.open(
                archive, StandardOpenOption.READ)) {
            Future<Integer> pending = channel.read(destination, offset);
            int count;
            try {
                count = pending.get();
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                throw interrupted;
            }
            if (count < 0) return new byte[0];
            destination.flip();
            byte[] received = new byte[count];
            destination.get(received);
            return received;
        }
    }
}''',
         cost="One read requests at most C bytes and retains O(C) buffer memory plus O(R) returned bytes for R bytes received. Future.get waits for completion; the asynchronous API alone does not make this call nonblocking. A pipeline of concurrent operations needs a bound on outstanding buffers and file handles.",
         mistakes=["Do not reuse a destination buffer before completion.", "Do not treat one completed read as an exact-length record.", "Do not claim nonblocking behavior when the caller immediately waits on Future.get."],
         related=["java/filechannel-positioned-exact-read", "java/completable-future", "java/cancellation"]),
    dict(slug="threadmxbean-deadlock-snapshot", title="Java ThreadMXBean deadlocks: diagnose platform-thread cycles", group="JVM management observations", release=11,
         definition="ThreadMXBean.findDeadlockedThreads returns IDs of platform threads in a detected lock cycle, or null when none are found. It is a diagnostic snapshot, not a recovery mechanism.",
         details="This method retrieves the bean, asks for deadlocked IDs, and resolves each ID to a short ThreadInfo. A thread can disappear between those calls, so null ThreadInfo entries are ignored. Some JVMs may not support the requested synchronizer inspection; an UnsupportedOperationException must be reported instead of being translated into 'no deadlock'. The API does not detect cycles involving virtual threads, and a non-null result does not identify which business operation should be rolled back. Capture the broader thread state under an incident policy before terminating anything.",
         case="A shipment service stops making progress while CPU is low. A probe finds a cycle between two platform threads holding separate locks. The IDs and names help narrow the incident; restarting a thread blindly can leave data inconsistent. If the probe returns null, the service may still be stuck on I/O, queue admission, or a virtual-thread wait.",
         code='''import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.ArrayList;
import java.util.List;

public class PlatformDeadlockSnapshot {
    public static List<String> threadNames() {
        ThreadMXBean threads = ManagementFactory.getThreadMXBean();
        long[] ids = threads.findDeadlockedThreads();
        if (ids == null) return List.of();
        List<String> names = new ArrayList<>();
        for (long id : ids) {
            ThreadInfo observed = threads.getThreadInfo(id, 47);
            if (observed != null) names.add(observed.getThreadName());
        }
        return names;
    }
}''',
         cost="A deadlock scan can be expensive relative to an ordinary counter read because it inspects thread and lock state. The returned list uses O(D) memory for D reported threads. Run it on a deliberate diagnostic path, not on every request.",
         mistakes=["Do not translate unsupported inspection into an empty result.", "Do not assume virtual-thread cycles are covered.", "Do not treat a deadlock snapshot as permission to kill a thread or roll back work."],
         related=["java/threads", "java/concurrency-reference", "java/jfr-incident-workflow"]),
    dict(slug="threadmxbean-cpu-time-policy", title="Java ThreadMXBean CPU time: check support and the disabled state", group="JVM management observations", release=11,
         definition="ThreadMXBean can report nanoseconds of CPU time for a platform thread when the JVM supports and enables the measurement. The value is CPU consumption, not elapsed wall time.",
         details="The method checks both support and enablement before reading the current thread. It returns absence when the capability is not available or the JVM reports a negative value; it does not switch monitoring on for the whole process. Enabling CPU-time measurement can have overhead and belongs to runtime configuration policy. For the same operation, wall time includes waiting on locks, network, and storage; a low CPU reading beside a high wall time suggests waiting but does not prove its cause. This API's platform-thread scope matters when virtual threads are used.",
         case="A parser completes in 82 milliseconds of wall time but uses only 17 milliseconds of CPU. The difference invites inspection of I/O and contention. It should not be labelled exactly 65 milliseconds of blocking: scheduling and measurement precision also matter. A missing CPU reading must stay missing rather than being reported as zero.",
         code='''import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.OptionalLong;

public class CurrentThreadCpuSample {
    public static OptionalLong nanoseconds() {
        ThreadMXBean threads = ManagementFactory.getThreadMXBean();
        if (!threads.isCurrentThreadCpuTimeSupported() || !threads.isThreadCpuTimeEnabled()) {
            return OptionalLong.empty();
        }
        long measured = threads.getCurrentThreadCpuTime();
        return measured < 0 ? OptionalLong.empty() : OptionalLong.of(measured);
    }
}''',
         cost="The API call is small compared with a file scan, but repeated high-frequency sampling still adds overhead. Store a pair of readings and subtract them for one scoped operation; one cumulative value is not its per-operation cost.",
         mistakes=["Do not report unsupported measurement as zero CPU time.", "Do not equate CPU time with elapsed time.", "Do not enable process-wide measurement as a hidden side effect of a helper."],
         related=["java/threads", "java/jvm-memory", "java/flight-recorder"]),
    dict(slug="memorymxbean-heap-snapshot", title="Java MemoryMXBean: read used, committed, and an optional maximum", group="JVM management observations", release=17,
         definition="MemoryMXBean reports a current heap usage observation. Used, committed, and maximum bytes answer different questions; maximum can be undefined.",
         details="This sampler retains one value object with those three fields. Used includes live objects and objects not yet collected, so one high reading is not evidence of a leak. Committed is storage available to the JVM, while max is a configured or implementation limit and may be -1. Heap does not include every form of process memory. Compare equivalent workload phases across time and use allocation, GC, and retained-object evidence before deciding that growth is pathological. Do not call System.gc merely to make a dashboard number look smaller.",
         case="A depot processes 47 batches. Heap used rises while a batch is active, then falls after the system reaches its normal idle point. That pattern differs from an idle floor that rises after each equivalent batch. The sampler records raw values; interpretation requires timestamps and workload context supplied by its caller.",
         code='''import java.lang.management.ManagementFactory;
import java.lang.management.MemoryUsage;
import java.util.OptionalLong;

public class HeapUsageSample {
    public record Snapshot(long usedBytes, long committedBytes, OptionalLong maxBytes) {}

    public static Snapshot capture() {
        MemoryUsage heap = ManagementFactory.getMemoryMXBean().getHeapMemoryUsage();
        long maximum = heap.getMax();
        return new Snapshot(heap.getUsed(), heap.getCommitted(),
            maximum < 0 ? OptionalLong.empty() : OptionalLong.of(maximum));
    }
}''',
         cost="Capturing three scalar fields uses O(1) application memory and time relative to heap size. Sampling too frequently can add monitoring overhead, and storing every sample indefinitely creates its own retention problem.",
         mistakes=["Do not interpret one used-heap value as a leak.", "Do not use -1 maximum as a real byte limit.", "Do not confuse heap usage with total process memory."],
         related=["java/jvm-memory", "java/gc-diagnostics", "java/heap-dump-workflow"]),
    dict(slug="classloading-mxbean-counts", title="Java ClassLoadingMXBean: separate live classes from lifetime totals", group="JVM management observations", release=17,
         definition="ClassLoadingMXBean exposes the current loaded-class count and lifetime loaded and unloaded totals. Those counters describe class activity, not why a class loader remains reachable.",
         details="The sampler reads all three counters without changing verbose loading settings. Because the bean is queried three times, the tuple is a nearby set of observations rather than an atomic snapshot. A rising current count can be expected during startup or plugin loading. A lifetime total only increases and must not be graphed as if it represented current retention. If current count continues rising after equivalent load cycles, inspect loader references and heap evidence; the counters alone cannot identify the retaining object.",
         case="A service installs 47 rule bundles. Its total loaded count rises even after some bundles unload, because it is a lifetime counter. The current count is the more relevant trend for possible accumulation, but a change in runtime libraries could also alter that trend. The caller tags samples with deployment version and bundle activity before diagnosing a leak.",
         code='''import java.lang.management.ClassLoadingMXBean;
import java.lang.management.ManagementFactory;

public class LoadedClassSample {
    public record Counts(int current, long loadedSinceStart, long unloadedSinceStart) {}

    public static Counts capture() {
        ClassLoadingMXBean classes = ManagementFactory.getClassLoadingMXBean();
        return new Counts(classes.getLoadedClassCount(),
            classes.getTotalLoadedClassCount(), classes.getUnloadedClassCount());
    }
}''',
         cost="Reading three counters is O(1) API work and memory. Keeping a bounded history of samples costs O(S) space for S samples. The investigation triggered by a suspicious trend may need a heap dump, which is far more expensive and sensitive.",
         mistakes=["Do not call a lifetime loaded total the number of live classes.", "Do not infer a class-loader leak from one rising sample.", "Do not enable verbose class loading inside a passive sampler."],
         related=["java/java-modules", "java/jvm-memory", "java/heap-dump-workflow"]),
]

quiz_path = "quizzes/java-channels-mxbeans"
quiz_title = "Java file channels and JVM observations quiz"
new_paths = ["java/" + lesson["slug"] for lesson in lessons] + [quiz_path]
assert len(new_paths) == len(set(new_paths)) and not set(new_paths) & lookup.keys()
titles = {row["path"]: row["title"] for row in entries}
titles.update({"java/" + lesson["slug"]: lesson["title"] for lesson in lessons})
titles[quiz_path] = quiz_title


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths):
    return "<ul>" + "".join("<li>" + link(path) + "</li>" for path in dict.fromkeys(paths)) + "</ul>"


def related(paths):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths)]


new_rows = []
for index, lesson in enumerate(lessons):
    path = "java/" + lesson["slug"]
    cohort = ["java/" + item["slug"] for item in lessons if item["group"] == lesson["group"] and item["slug"] != lesson["slug"]]
    connections = lesson["related"] + cohort + [quiz_path, "java/advanced-java"]
    body = ("<p>" + html.escape(lesson["definition"]) + "</p>"
            + "<h2>Operational contract</h2><p>" + html.escape(lesson["details"]) + "</p>"
            + "<h2>Failure case</h2><p>" + html.escape(lesson["case"]) + "</p>"
            + '<h2>Java code</h2><pre><code class="language-java">' + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + "<h2>Performance and ownership cost</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    row = copy.deepcopy(lookup["java/casts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=lesson["title"], summary=lesson["definition"], body=body,
               subject="java-advanced", category="Programming", tags=["java", lesson["group"].lower(), lesson["slug"]],
               difficulty="Advanced", sort_order=34400 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("What proves a FileChannel write has consumed the whole payload?", "The ByteBuffer has no remaining bytes", "One write returned a positive count", "The channel was opened", "A positive write may be partial."),
    ("What happens to the channel cursor after a positioned read?", "It stays at its prior position", "It always moves to the end", "It resets to zero", "The explicit position controls that read without changing the channel's cursor."),
    ("Why loop over transferTo?", "It can transfer fewer bytes than requested", "It always returns zero", "It verifies a checksum automatically", "Count actual progress until the expected range is copied."),
    ("What does force(true) request?", "Persistence of content and relevant metadata", "An atomic rename", "A database commit", "Forced storage and namespace publication are different boundaries."),
    ("Does a FileLock control a writer that ignores the lock protocol everywhere?", "No", "Yes on every filesystem", "Only after a JFR recording", "Lock behavior and enforcement vary across platforms and participants."),
    ("What must be known before truncating a damaged binary log?", "A validated complete-record boundary", "Only its current size", "The number of Java threads", "Truncation cannot determine the last valid record."),
    ("When may an asynchronous read buffer be reused?", "After the operation has completed", "As soon as read returns a Future", "While the operation is still writing", "The pending operation owns its destination until completion."),
    ("What does a null result from findDeadlockedThreads mean?", "No platform-thread lock cycle was detected", "Every thread is healthy", "A virtual-thread cycle was found", "The API's diagnostic scope is narrower than all forms of waiting."),
    ("How should unsupported thread CPU time be represented?", "As absent", "As zero CPU time", "As elapsed time", "A missing measurement is not a measured zero."),
    ("Can a heap maximum of -1 be used as a real limit?", "No, it is undefined", "Yes, it means one byte", "Yes, it is committed memory", "MemoryUsage permits an undefined maximum."),
    ("Does used heap alone prove a memory leak?", "No, it can include objects not yet collected", "Yes after one batch", "Only when max is defined", "Compare equivalent workload phases and retained-object evidence."),
    ("Which class count is current rather than lifetime cumulative?", "getLoadedClassCount", "getTotalLoadedClassCount", "getUnloadedClassCount", "The other two are totals since process start."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check file-channel progress, recovery, and JVM observation contracts.",
            body="<p>Choose the decision supported by each API contract. These are local self-check questions.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not mistake a partial I/O result or one runtime sample for a complete system guarantee.</p>",
            sort_order=34550, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=18, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": group, "summary": "Track partial results, resource ownership, and what each observation proves.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Separate an API observation from the business conclusion.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Channels and JVM observations", "summary": "Test byte progress and runtime measurement boundaries.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Channels and JVM observations</h2><p>Test the new channel and management boundaries.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java channel and runtime topics</h2><p>Inspect byte progress, file ownership, and JVM measurements.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/files": ["java/filechannel-write-completion", "java/filechannel-positioned-exact-read", "java/asynchronousfilechannel-buffer-lifetime"],
    "java/atomic-file-publication": ["java/filechannel-force-durability", "java/filechannel-transfer-progress", "java/filechannel-truncate-recovery"],
    "java/bytebuffer-flip-compact-state": ["java/filechannel-write-completion", "java/asynchronousfilechannel-buffer-lifetime"],
    "java/jvm-memory": ["java/memorymxbean-heap-snapshot", "java/classloading-mxbean-counts"],
    "java/gc-diagnostics": ["java/memorymxbean-heap-snapshot"],
    "java/threads": ["java/threadmxbean-deadlock-snapshot", "java/threadmxbean-cpu-time-policy"],
    "java/flight-recorder": ["java/threadmxbean-cpu-time-policy", "java/memorymxbean-heap-snapshot"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
