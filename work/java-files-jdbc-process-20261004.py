"""Add original Java filesystem, JDBC, and subprocess contract lessons."""

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
    dict(slug="file-tree-visitor-failure-policy", title="Java walkFileTree: visit failures without hiding incomplete scans", group="Filesystem observation", release=11,
         definition="Files.walkFileTree visits a directory tree through callbacks that distinguish entry visits, directory entry, failed visits, and directory completion. A complete inventory must define what happens when any visit fails.",
         details="A manifest scanner should not return a green count after permission failure halfway through a tree. SimpleFileVisitor's default failure behavior throws, which is useful when completeness matters. If the application deliberately skips a subtree, it must record the omitted path and mark the inventory partial. The visitor below collects regular files without following symbolic links and lets I/O failures reach the caller. The caller owns the resulting list and the decision to publish it.",
         case="A fictional dispatch archive has 47 manifest files under several depot folders. If one depot cannot be opened, a count of the other files is not an archive total. Keep that failure beside the scan ID; do not silently treat it as an empty folder. Following directory links would also change the traversal boundary and could create cycles, so the sample retains the default no-follow behavior.",
         code='''import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.ArrayList;
import java.util.List;

public class ManifestTreeInventory {
    public static List<Path> scan(Path archiveRoot) throws IOException {
        List<Path> manifests = new ArrayList<>();
        Files.walkFileTree(archiveRoot, new SimpleFileVisitor<Path>() {
            @Override public FileVisitResult visitFile(Path path, BasicFileAttributes attributes) {
                if (attributes.isRegularFile() && path.getFileName().toString().endsWith(".manifest")) {
                    manifests.add(path);
                }
                return FileVisitResult.CONTINUE;
            }
            @Override public FileVisitResult visitFileFailed(Path path, IOException failure) throws IOException {
                throw new IOException("Inventory incomplete at " + path, failure);
            }
        });
        return manifests;
    }
}''',
         cost="The walk visits N reachable entries in O(N) time. The visitor retains M matching paths in O(M) application memory; traversal bookkeeping grows with depth. A failure is a correctness result, not a performance detail. For huge trees, write bounded inventory records to a controlled sink rather than retaining every path.",
         mistakes=["Do not convert visitFileFailed into CONTINUE without recording a partial result.", "Do not call a symlink target part of the scan unless link traversal is an explicit policy.", "Do not publish a total before traversal completes."],
         related=["java/files", "java/files-walk-close", "java/path-lexical-boundary"]),
    dict(slug="watch-service-key-lifecycle", title="Java WatchService: register, consume, and reset each key", group="Filesystem observation", release=17,
         definition="WatchService reports changes to registered watchable objects through signaled keys. The consumer retrieves a key, reads its events, and resets it so later changes can be signaled.",
         details="A watched directory is a hint source, not a durable message queue. Register the directory for the event kinds needed by the application, process a key's current batch, then inspect reset's boolean result. A false result means the registration is no longer valid and requires a new ownership decision. The event context for a Path registration is relative to the watched directory. The code keeps resolution local to that directory and returns whether observation remains active; the owner closes the service on shutdown.",
         case="A depot process watches a staging folder where 47 manifests may arrive over a shift. One create notification prompts an intake check, but a modify notification can arrive while the producer is still writing. The consumer records candidate paths and waits for the publication contract described in the next lesson. It does not parse each event as a complete manifest or promise that every short-lived file will be observed.",
         code='''import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.nio.file.StandardWatchEventKinds;
import java.nio.file.WatchEvent;
import java.nio.file.WatchKey;
import java.nio.file.WatchService;
import java.util.Set;

public class StagingWatchConsumer {
    public record Outcome(boolean rescan, boolean active) {}

    public static WatchService register(Path staging) throws IOException {
        WatchService service = FileSystems.getDefault().newWatchService();
        try {
            staging.register(service, StandardWatchEventKinds.ENTRY_CREATE,
                StandardWatchEventKinds.ENTRY_MODIFY, StandardWatchEventKinds.ENTRY_DELETE);
            return service;
        } catch (IOException | RuntimeException failure) {
            try { service.close(); }
            catch (IOException closeFailure) { failure.addSuppressed(closeFailure); }
            throw failure;
        }
    }

    public static Outcome takeOne(WatchService service, Path staging, Set<Path> candidates)
            throws InterruptedException {
        WatchKey key = service.take();
        boolean rescan = false;
        for (WatchEvent<?> event : key.pollEvents()) {
            if (event.kind() == StandardWatchEventKinds.OVERFLOW) {
                rescan = true;
                continue;
            }
            Object context = event.context();
            if (context instanceof Path) {
                Path relative = (Path) context;
                if (!relative.isAbsolute()) candidates.add(staging.resolve(relative).normalize());
            }
        }
        return new Outcome(rescan, key.reset());
    }
}''',
         cost="Processing E delivered events is O(E) plus set insertion. The set retains O(U) distinct candidate paths, where U is the number of unique names. If the producer outruns the consumer, event loss can occur; reset and overflow handling must be paired with a directory reconciliation path.",
         mistakes=["Do not forget to reset the key after processing its batch.", "Do not resolve event context against an unrelated working directory.", "Do not equate a create event with a finished file."],
         related=["java/atomic-file-publication", "java/files", "java/cancellation"]),
    dict(slug="watch-service-overflow-reconciliation", title="Java WatchService OVERFLOW: reconcile against directory state", group="Filesystem observation", release=11,
         definition="WatchService OVERFLOW means changes may have been discarded. A consumer must compare current directory state with its last accepted snapshot rather than trying to reconstruct missing events.",
         details="The event stream does not identify which changes were lost. Treat it as a signal to rescan the registered directory and rebuild the candidate set under the same eligibility rule. A directory listing can itself race with writers or fail; its result is a point-in-time observation, not an atomic filesystem transaction. Keep a scan generation and record failures. The code below demonstrates a bounded reconciliation, refusing a directory with more than 47 visible entries instead of silently truncating it.",
         case="A depot initially knows 42 names. A burst of writes produces OVERFLOW. The service cannot say whether the remaining five expected manifests were created, renamed, or removed. A fresh listing obtains the current names and replaces the remembered set only if it completes inside the cap. The caller then validates candidate contents using a separate publication rule before counting them as accepted manifests.",
         code='''import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

public class DirectoryReconciliation {
    public static Set<Path> snapshot(Path staging) throws IOException {
        Set<Path> visible = new HashSet<>();
        try (DirectoryStream<Path> entries = Files.newDirectoryStream(staging)) {
            for (Path candidate : entries) {
                if (visible.size() >= 47) throw new IOException("Listing cap exceeded");
                visible.add(candidate.getFileName());
            }
        }
        return visible;
    }
}''',
         cost="Rebuilding a set from N directory entries is O(N) expected time and O(N) memory. Comparing it with the old set is also O(N+K) expected for old-set size K. A cap protects memory but deliberately fails completeness when exceeded; increase capacity or page the intake design, never report the capped set as complete.",
         mistakes=["Do not treat OVERFLOW as one ordinary file event.", "Do not retain a partial listing as a complete snapshot.", "Do not assume a rescan is atomic with ongoing writers."],
         related=["java/files-walk-close", "java/atomic-file-publication", "java/collection-views"]),
    dict(slug="directory-stream-close-and-cap", title="Java DirectoryStream: close iteration and reject silent truncation", group="Filesystem observation", release=11,
         definition="DirectoryStream iterates directory entries while holding an I/O resource. A bounded listing needs a close scope, an explicit maximum, and a policy for iteration failures.",
         details="Unlike a materialized list, iteration can fail after some entries have already been seen. The caller must not confuse the partial result with a complete batch. The program selects manifest names, rejects a forty-eighth match, sorts the accepted names for stable reporting, and unwraps a DirectoryIteratorException as an I/O failure. Directory iteration order is not a business order. If a larger scan is required, design a chunked consumer or use a database-backed inventory instead of quietly dropping entries.",
         case="A review job expects at most 47 staging manifests. Forty-seven matches fit; a forty-eighth is a capacity error, not the first file of an invisible next page. Sorting makes a report reproducible for the snapshot that was observed, but a producer can still change the directory during iteration. The job records the scan time and verifies each opened file again before processing.",
         code='''import java.io.IOException;
import java.nio.file.*;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class BoundedManifestListing {
    public static List<Path> list(Path staging) throws IOException {
        List<Path> matches = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(staging, "*.manifest")) {
            for (Path candidate : stream) {
                if (matches.size() == 47) throw new IOException("More than 47 manifests");
                matches.add(candidate);
            }
        } catch (DirectoryIteratorException failure) {
            throw new IOException("Manifest listing failed", failure.getCause());
        }
        matches.sort(Comparator.comparing(path -> path.getFileName().toString()));
        return matches;
    }
}''',
         cost="The listing visits N entries and sorting M matches takes O(M log M) time with O(M) retained paths. The cap bounds M at 47 for this job. It does not bound the provider's traversal work or prove the directory stayed unchanged between listing and open.",
         mistakes=["Do not leave DirectoryStream open after iteration.", "Do not assume iteration order is sorted.", "Do not return a partial list after an iteration failure or cap breach."],
         related=["java/files-walk-close", "java/file-tree-visitor-failure-policy", "java/bounded-line-reader"]),
    dict(slug="symbolic-link-attribute-boundary", title="Java symbolic links: inspect attributes without claiming race safety", group="Filesystem observation", release=11,
         definition="NOFOLLOW_LINKS makes a metadata read describe a symbolic link itself rather than the target it names. That observation is useful for an intake policy but does not lock the path against replacement.",
         details="A manifest intake may reject symbolic links because they can point outside the owned staging tree. readAttributes with NOFOLLOW_LINKS distinguishes a regular file from a link at the moment of inspection. A later open can still follow a path that has been replaced in between. For an adversarial writable directory, move ownership to a trusted staging area or use a supported handle-relative API such as SecureDirectoryStream, with a fallback policy when it is unavailable. The sample is an inspection gate, not a race-free opener.",
         case="A contractor uploads a candidate named shipment-47.manifest. The metadata gate accepts a regular file and rejects a symbolic link. If another writer can rename entries after the check, the application must not claim that the next path-based read is protected. The job keeps the folder write permissions narrow and validates the opened content before it makes any state change.",
         code='''import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.attribute.BasicFileAttributes;

public class ManifestAttributeGate {
    public static void requireRegularEntry(Path candidate) throws IOException {
        BasicFileAttributes observed = Files.readAttributes(
            candidate, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (!observed.isRegularFile()) {
            throw new IOException("Manifest entry is not a regular file");
        }
    }
}''',
         cost="One metadata read is O(1) API work but may involve remote or slow filesystem I/O. Secure open-and-verify designs cost more coordination than a lexical check, yet they are needed when untrusted users can mutate the directory. The observed attributes should never be sold as a permanent property of a path name.",
         mistakes=["Do not equate Path.normalize with filesystem containment.", "Do not assume NOFOLLOW_LINKS prevents a later replacement race.", "Do not accept a symbolic link because its current target appears regular."],
         related=["java/path-lexical-boundary", "java/atomic-file-publication", "java/files"]),
    dict(slug="jdbc-batch-update-counts", title="Java JDBC batches: inspect update counts and own rollback", group="JDBC result contracts", release=11,
         definition="PreparedStatement batching queues parameter sets for one executeBatch call. The returned counts and a possible BatchUpdateException describe execution, not automatic transaction success.",
         details="Some drivers stop after a failed command, while others continue and mark failed positions. SUCCESS_NO_INFO means success without a row count. A caller must decide whether every position met the business invariant, then commit or roll back the owned transaction. The method stages one receipt ID per parameter set and returns raw counts; it requires auto-commit to be disabled. It does not promise that batch execution alone is atomic, and it leaves commit, rollback, and connection lifetime to its caller.",
         case="A depot sends 47 receipt IDs. If entry 31 violates a uniqueness rule, the caller records the failing batch result, rolls back the transaction, and resolves whether a retry is safe. It does not report 30 or 46 accepted receipts from a count array while leaving the connection open for another request. The IDs need an idempotency rule before a retry after a network failure.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.List;

public class ReceiptBatchWriter {
    public static int[] stage(Connection connection, List<String> receiptIds) throws SQLException {
        if (connection.getAutoCommit()) throw new SQLException("Caller must own a transaction");
        try (PreparedStatement statement = connection.prepareStatement(
                "INSERT INTO receipt_intake (receipt_id) VALUES (?)")) {
            for (String receiptId : receiptIds) {
                statement.setString(1, receiptId);
                statement.addBatch();
            }
            return statement.executeBatch();
        }
    }
}''',
         cost="Binding N rows is O(N) client work and O(N) pending parameter state until execution. Batching can reduce round trips, but the actual transport and server plan depend on the driver. Bound batch size and inspect all returned positions; a database transaction remains the durability boundary.",
         mistakes=["Do not interpret SUCCESS_NO_INFO as zero affected rows.", "Do not assume every driver stops at the first failed command.", "Do not leave rollback ownership ambiguous after any failure."],
         related=["java/jdbc-transactions", "java/jdbc-prepared", "java/database-project"]),
    dict(slug="jdbc-resultset-null-cursor", title="Java ResultSet: cursor position and SQL NULL are separate states", group="JDBC result contracts", release=11,
         definition="A JDBC ResultSet begins before its first row and advances with next. Primitive getters return a Java primitive even for SQL NULL, so wasNull must be checked immediately after that getter.",
         details="A zero from getInt can mean a stored zero or SQL NULL. Calling another getter before wasNull changes which read the flag describes. The method below maps an optional reserved quantity to Integer, preserving zero and absence as distinct values. It uses a forward-only read and closes the result and statement together. The SQL orders rows explicitly; ResultSet traversal order without ORDER BY is not a report contract. A missing row remains different from a row with a null quantity.",
         case="A dispatch report contains one receipt with zero reserved units and another with no quantity reported. Turning both into zero would hide missing source data. The mapping keeps the second value null for an upstream validation decision. The caller can then reject incomplete quantities without distorting the first receipt's legitimate zero.",
         code='''import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class ReservationRows {
    public static List<Integer> quantities(Connection connection) throws SQLException {
        List<Integer> quantities = new ArrayList<>();
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT reserved_qty FROM receipt_intake ORDER BY receipt_id");
             ResultSet rows = statement.executeQuery()) {
            while (rows.next()) {
                int quantity = rows.getInt(1);
                quantities.add(rows.wasNull() ? null : quantity);
            }
        }
        return quantities;
    }
}''',
         cost="Reading N rows is O(N) time and the returned list uses O(N) memory. A streaming consumer can reduce retained memory, but driver fetch behavior and connection lifetime still matter. Never infer a complete business population merely because next eventually returns false; filters and snapshot isolation determine which rows were queried.",
         mistakes=["Do not call a primitive zero proof that the SQL column was non-null.", "Do not invoke wasNull after reading another column.", "Do not read a getter before next positions the cursor on a row."],
         related=["java/jdbc-prepared", "java/jdbc-transactions", "java/optional"]),
    dict(slug="jdbc-generated-key-ownership", title="Java JDBC generated keys: validate one insert and one returned identity", group="JDBC result contracts", release=11,
         definition="A JDBC insert can request generated keys from its PreparedStatement. The caller must check update count, key presence, key type, and transaction outcome before treating the identity as durable.",
         details="Generated-key support and which columns are returned vary by driver and SQL operation. This example asks for a key for a single inserted manifest, rejects zero or multiple returned key rows, and preserves the connection's transaction boundary for the caller. It does not commit. A key seen before commit can still disappear on rollback. For multi-row inserts, define an explicit mapping between input rows and generated identities rather than assuming a convenient order.",
         case="A review process inserts manifest-47 and needs the new row ID for a child audit record. It requests the key while using the same transaction, then inserts the child row and commits both together. If the insert reports no row or the driver returns no key, the operation fails and the owner rolls back. The application never invents an ID from the last value seen in another request.",
         code='''import java.sql.*;

public class ManifestIdentityWriter {
    public static long insert(Connection connection, String manifestName) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "INSERT INTO manifests (name) VALUES (?)", Statement.RETURN_GENERATED_KEYS)) {
            statement.setString(1, manifestName);
            if (statement.executeUpdate() != 1) throw new SQLException("Expected one inserted row");
            try (ResultSet keys = statement.getGeneratedKeys()) {
                if (!keys.next()) throw new SQLException("Generated key absent");
                long identity = keys.getLong(1);
                if (keys.wasNull() || keys.next()) throw new SQLException("Invalid generated key result");
                return identity;
            }
        }
    }
}''',
         cost="The client performs one insert and one key-result read. Database indexing and transaction work dominate the actual cost. Keeping the child write in the same transaction prevents a published ID from describing a parent row that was later rolled back.",
         mistakes=["Do not assume generated keys are available for every driver and statement.", "Do not treat a pre-commit key as a committed record.", "Do not assume multi-row key order without a database-specific contract."],
         related=["java/jdbc-transactions", "java/jdbc-prepared", "java/database-project"]),
    dict(slug="jdbc-fetch-size-bounded-read", title="Java JDBC fetch size: a hint, not a memory guarantee", group="JDBC result contracts", release=11,
         definition="Statement.setFetchSize suggests how many rows a JDBC driver should fetch when more rows are needed. Its behavior is driver-dependent and does not by itself cap a query result.",
         details="Use a query predicate and explicit order to define the population. Add a separate maximum-row or pagination contract when a result may be large. The method below reads at most 470 ordered receipt IDs into memory and marks that it is only a page, not a complete report. Some drivers buffer more than the hint or require transaction settings for cursor-based fetching. Measure memory and fetch behavior with the deployed driver before claiming streaming.",
         case="A depot has 47,000 receipts. The reviewer requests a page of 470 IDs, ordered by stable receipt ID, and carries the last ID into a later keyset query. Asking only for fetch size 47 would still permit a 47,000-row result. The code keeps one page in memory; it does not claim a snapshot across later pages without an isolation policy.",
         code='''import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class ReceiptPageReader {
    public static List<String> pageAfter(Connection connection, String lastId) throws SQLException {
        List<String> receiptIds = new ArrayList<>();
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT receipt_id FROM receipt_intake WHERE receipt_id > ? ORDER BY receipt_id")) {
            statement.setString(1, lastId);
            statement.setFetchSize(47);
            statement.setMaxRows(470);
            try (ResultSet rows = statement.executeQuery()) {
                while (rows.next()) receiptIds.add(rows.getString(1));
            }
        }
        return receiptIds;
    }
}''',
         cost="Each page retains at most 470 IDs in O(P) application memory for page size P, while the database may scan or index-search according to its plan. Fetch size affects transport hints rather than the logical limit. Repeated pages require stable ordering, an index strategy, and a policy for rows inserted between calls.",
         mistakes=["Do not call fetch size a row limit.", "Do not promise constant process memory without testing the driver.", "Do not paginate without a stable order and change policy."],
         related=["java/jdbc-prepared", "java/jdbc-transactions", "java/streams"]),
    dict(slug="processbuilder-command-token-boundary", title="Java ProcessBuilder: pass command tokens without a shell", group="Subprocess ownership", release=11,
         definition="ProcessBuilder receives an executable and individual arguments. It does not need a shell to pass a file path to a known command, and its Process result needs an owner.",
         details="Never construct a shell command string from a user-supplied manifest name when the job only needs to run a fixed executable. Select the executable from trusted configuration, keep each argument separate, and constrain which inputs the child may read. The sample starts the JDK's own version command and discards output so a full pipe cannot block it. Returning a Process transfers wait, timeout, and cleanup responsibility to the caller; the companion lesson owns that lifecycle.",
         case="A depot startup check runs the installed Java executable with a fixed '-version' argument solely to confirm that the process starts and exits. This sample discards version text; a caller that needs the numeric version must capture a bounded stream and parse it separately. The command is not a facility for arbitrary user input. If the child fails to launch, the application records the I/O exception and never reports a successful check.",
         code='''import java.io.IOException;
import java.nio.file.Path;

public class JavaRuntimeProbe {
    public static Process start() throws IOException {
        Path executable = Path.of(System.getProperty("java.home"), "bin", "java");
        return new ProcessBuilder(executable.toString(), "-version")
            .redirectOutput(ProcessBuilder.Redirect.DISCARD)
            .redirectError(ProcessBuilder.Redirect.DISCARD)
            .start();
    }
}''',
         cost="Launching a native process is far more expensive than a Java method call and consumes operating-system resources until reaped. The snippet allocates no output buffer because both streams are discarded. If output is required, drain it under a size limit rather than reading it only after waiting for exit.",
         mistakes=["Do not concatenate untrusted arguments into a shell string.", "Do not ignore the returned Process after starting it.", "Do not wait for exit while leaving bounded output pipes undrained."],
         related=["java/socket-boundaries", "java/executors", "java/cancellation"]),
    dict(slug="process-timeout-and-cleanup", title="Java Process.waitFor timeout: terminate and reap the owned child", group="Subprocess ownership", release=11,
         definition="Process.waitFor with a timeout reports whether a child has exited; a false return does not stop the child. The owner must terminate it and account for its streams and descendants.",
         details="The method first asks for a normal termination, waits briefly, then requests forceful termination and waits for the child to exit. It restores the interrupt signal if the waiting thread is interrupted. This is a bounded attempt for the direct child only; programs that spawn descendants require a separate process-tree policy, and native termination behavior varies. In the companion command example, output is discarded so a filled pipe cannot keep the child blocked while the parent waits.",
         case="The depot allows a diagnostic 47 seconds. If it is still alive, timeout is a failure, not a successful zero exit code. The owner terminates the child and records the timeout. If the waiting thread is interrupted, it requests forceful termination before passing the interrupt upward. A production supervisor also checks whether the command launched child processes that outlive this direct handle.",
         code='''import java.util.concurrent.TimeUnit;

public class ChildProcessDeadline {
    public static int await(Process child) throws InterruptedException {
        try {
            if (child.waitFor(47, TimeUnit.SECONDS)) return child.exitValue();
            child.destroy();
            if (!child.waitFor(3, TimeUnit.SECONDS)) {
                child.destroyForcibly();
                child.waitFor();
            }
            throw new IllegalStateException("Child exceeded its deadline");
        } catch (InterruptedException interrupted) {
            child.destroyForcibly();
            Thread.currentThread().interrupt();
            throw interrupted;
        }
    }
}''',
         cost="Waiting consumes elapsed time rather than CPU in the usual case. One process consumes handles and native memory until exit. A timeout plus cleanup bounds the direct child's lifetime in normal operation, but a forceful kill can still require a reaping wait and cannot guarantee every descendant is gone.",
         mistakes=["Do not call a false timed wait a terminated child.", "Do not report timeout as exit code zero.", "Do not assume killing one Process handle kills its descendants."],
         related=["java/processbuilder-command-token-boundary", "java/cancellation", "java/executor-rejection"]),
]

quiz_path = "quizzes/java-files-jdbc-process"
quiz_title = "Java file, JDBC, and subprocess boundaries quiz"
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
            + "<h2>Java code</h2><pre><code class=\"language-java\">" + html.escape(lesson["code"], quote=False) + "</code></pre>"
            + "<h2>Performance and ownership cost</h2><p>" + html.escape(lesson["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in lesson["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    row = copy.deepcopy(lookup["java/casts"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)), path=path,
               title=lesson["title"], summary=lesson["definition"], body=body,
               subject="java-advanced", category="Programming", tags=["java", lesson["group"].lower(), lesson["slug"]],
               difficulty="Advanced", sort_order=34000 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("What should walkFileTree do when a required folder cannot be read?", "Fail or record a partial scan", "Count it as empty", "Invent the missing files", "A complete inventory cannot hide visit failure."),
    ("When should a WatchKey be reset?", "After its current events are processed", "Before registration", "Only when the service closes", "Reset permits another signal and reports key validity."),
    ("What does a create event prove about file content?", "Only that an event was observed", "The producer closed the file", "The manifest is validated", "A writer may still be modifying the file."),
    ("What follows WatchService OVERFLOW?", "Reconcile current directory state", "Guess the missing event names", "Ignore the key forever", "Discarded events cannot be reconstructed from the notification."),
    ("What happens after a DirectoryStream cap breach?", "Fail the listing as incomplete", "Return the first 47 as the full directory", "Assume entries are sorted", "A cap must not turn into silent truncation."),
    ("Does NOFOLLOW_LINKS make a later open race-free?", "No, the path may be replaced after inspection", "Yes, always", "Only when the filename is short", "Metadata inspection and later open are separate operations."),
    ("What does SUCCESS_NO_INFO mean in a JDBC batch?", "Success with no row count available", "Zero rows always", "A failed command", "The driver cannot report an affected-row count for that position."),
    ("When is ResultSet.wasNull checked for getInt?", "Immediately after that getter", "Before next", "After reading another column", "The flag describes the most recent column read."),
    ("Is a generated key durable before commit?", "No, rollback can remove the inserted row", "Yes, even after rollback", "Only if it is a long", "The transaction owner still decides commit."),
    ("Does setFetchSize cap the result rows?", "No, it is a driver-dependent fetch hint", "Yes, at exactly 47", "Yes, for every database", "A logical page needs its own limit and order."),
    ("Why pass ProcessBuilder arguments separately?", "To avoid constructing a shell command from data", "To bypass all authorization", "To make the child synchronous", "A fixed executable can receive explicit argument tokens."),
    ("What does timed waitFor returning false mean?", "The child has not exited within the wait", "Exit code zero", "All descendants are gone", "The owner must terminate and reap under its policy."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check Java filesystem observations, JDBC result contracts, and subprocess ownership.",
            body="<p>Choose the decision supported by each API contract. These are local self-check questions.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not mistake an observed event, returned key, or hint for a committed and complete result.</p>",
            sort_order=34150, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
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
    hub["data"]["modules"].append({"title": group, "summary": "Track the actual API result, failure policy, and resource owner.", "lessons": selected})
    hub["body"] += "<h2>" + html.escape(group) + "</h2><p>Work from observed state to an explicit decision.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "Filesystem, JDBC and process decisions", "summary": "Test observation, transaction, and child lifetime contracts.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>Filesystem, JDBC and process decisions</h2><p>Test the new API boundaries.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java API boundaries</h2><p>Inspect filesystem changes, database results, and owned subprocesses.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/files": ["java/file-tree-visitor-failure-policy", "java/directory-stream-close-and-cap"],
    "java/files-walk-close": ["java/file-tree-visitor-failure-policy", "java/directory-stream-close-and-cap"],
    "java/atomic-file-publication": ["java/watch-service-key-lifecycle", "java/watch-service-overflow-reconciliation"],
    "java/path-lexical-boundary": ["java/symbolic-link-attribute-boundary"],
    "java/jdbc-prepared": ["java/jdbc-batch-update-counts", "java/jdbc-resultset-null-cursor", "java/jdbc-generated-key-ownership"],
    "java/jdbc-transactions": ["java/jdbc-batch-update-counts", "java/jdbc-generated-key-ownership"],
    "java/jdbc-reference": ["java/jdbc-resultset-null-cursor", "java/jdbc-fetch-size-bounded-read"],
    "java/cancellation": ["java/process-timeout-and-cleanup"],
    "java/executors": ["java/processbuilder-command-token-boundary"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
