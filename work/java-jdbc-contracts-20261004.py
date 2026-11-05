"""Add original JDBC boundary lessons and a review quiz."""

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
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(slug="jdbc-savepoint-optional-step", title="Java JDBC savepoints: roll back one optional step inside a transaction", group="Transaction and capability boundaries", release=11,
         definition="A JDBC savepoint marks a position inside a caller-owned transaction. Rolling back to it undoes later database changes while retaining earlier uncommitted changes.",
         details="This method requires auto-commit to be off and assumes the caller owns the transaction. It creates a savepoint immediately before an optional audit insert. If the insert fails, it rolls back to the savepoint and rethrows the original SQLException. The caller then decides whether the earlier shipment work may be committed or whether the entire transaction must be rolled back. Some drivers or transaction managers do not support savepoints; detect support before making this policy mandatory. This helper never commits, changes isolation, or closes the connection.",
         case="A shipment update succeeds, then an optional audit row conflicts with an existing key. The helper rolls back only its attempted audit insert. The outer service can decide whether a missing audit record is acceptable; it must not blindly commit after every SQL failure, especially if the connection itself is unusable.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Savepoint;

public class OptionalShipmentAudit {
    public static void insert(Connection connection, long shipmentId) throws SQLException {
        if (connection.getAutoCommit()) throw new IllegalStateException("Transaction required");
        Savepoint beforeAudit = connection.setSavepoint();
        try (PreparedStatement statement = connection.prepareStatement(
                "INSERT INTO shipment_audit (shipment_id, event_code) VALUES (?, ?)")) {
            statement.setLong(1, shipmentId);
            statement.setString(2, "REVIEW-47");
            if (statement.executeUpdate() != 1) throw new SQLException("Audit row not inserted");
        } catch (SQLException failure) {
            try { connection.rollback(beforeAudit); }
            catch (SQLException rollbackFailure) { failure.addSuppressed(rollbackFailure); }
            throw failure;
        }
    }
}''',
         cost="Creating and rolling back a savepoint involve driver and database round trips or local transaction bookkeeping. The Java method retains O(1) application state. Database undo work depends on changes after the savepoint; it is not free merely because the Java code is short.",
         mistakes=["Do not create a savepoint while auto-commit is enabled.", "Do not treat a rollback-to-savepoint failure as permission to commit.", "Do not assume every driver or managed transaction supports savepoints."],
         related=["java/jdbc-transactions", "java/database-isolation", "java/jdbc-driver-capability-check"]),
    dict(slug="jdbc-typed-null-parameter", title="Java JDBC setNull: bind a nullable column with its SQL type", group="Parameter and row boundaries", release=11,
         definition="PreparedStatement.setNull binds SQL NULL with a specified SQL type. A nullable parameter should follow the column's type contract instead of relying on a driver to infer one from a Java null.",
         details="The method updates a nullable VARCHAR courier note by shipment ID. It uses setNull with Types.VARCHAR when the note is absent and setString otherwise. It rejects a note longer than 47 characters before contacting the database, then requires exactly one updated row. The database schema may impose a different length or character rule, so this application cap must be aligned with migration policy. SQL NULL is not the same as an empty string. The connection and transaction remain owned by the caller.",
         case="A carrier clears the note for shipment 82. Passing null to setString may be handled by a driver, but this code states the SQL type explicitly. A zero-row update signals an unknown shipment rather than reporting success, and a two-row update signals a broken uniqueness assumption.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Types;

public class CourierNoteUpdate {
    public static void apply(Connection connection, long shipmentId, String note)
            throws SQLException {
        if (note != null && note.length() > 47)
            throw new IllegalArgumentException("Courier note exceeds 47 characters");
        try (PreparedStatement statement = connection.prepareStatement(
                "UPDATE shipments SET courier_note = ? WHERE shipment_id = ?")) {
            if (note == null) statement.setNull(1, Types.VARCHAR);
            else statement.setString(1, note);
            statement.setLong(2, shipmentId);
            if (statement.executeUpdate() != 1)
                throw new SQLException("Expected one shipment update");
        }
    }
}''',
         cost="Parameter binding is O(L) or driver-dependent for a note of length L; this code holds at most 47 Java UTF-16 code units. Database update cost depends on indexing, locks, and transaction work. The method allocates no result collection.",
         mistakes=["Do not equate SQL NULL with an empty string.", "Do not ignore a zero-row or multi-row update when one row is required.", "Do not assume a Java string-length cap exactly matches database byte or character semantics."],
         related=["java/jdbc-prepared", "java/jdbc-resultset-null-cursor", "java/jdbc-generated-key-ownership"]),
    dict(slug="jdbc-query-timeout-budget", title="Java JDBC query timeout: bound a statement without claiming a whole-request deadline", group="Transaction and capability boundaries", release=11,
         definition="Statement.setQueryTimeout asks the driver to limit execution time for that statement in seconds. It is not a complete deadline for connection acquisition, network stalls, or all work in a request.",
         details="This method sets a three-second query timeout before executing a parameterized lookup. It closes the ResultSet and PreparedStatement in one scope, returns at most one status value, and rejects a second matching row. A driver may attempt to cancel a timed-out statement and report SQLTimeoutException; cancellation and server behavior are driver-dependent. A connection-pool acquisition timeout and Connection.setNetworkTimeout govern different waiting phases. Never assume this setter interrupts every JDBC call at exactly three seconds.",
         case="A shipment-status query waits on a database lock. The statement timeout may terminate the query and surface an exception; the outer request must still decide whether to retry. A request that spent five seconds waiting for a pool connection before creating the statement was never protected by this three-second setting.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class TimedShipmentLookup {
    public static String status(Connection connection, long shipmentId) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT status FROM shipments WHERE shipment_id = ?")) {
            statement.setQueryTimeout(3);
            statement.setLong(1, shipmentId);
            try (ResultSet rows = statement.executeQuery()) {
                if (!rows.next()) return null;
                String status = rows.getString(1);
                if (rows.next()) throw new SQLException("Duplicate shipment ID");
                return status;
            }
        }
    }
}''',
         cost="The Java cursor retains O(1) application data, while indexed lookup and lock wait determine database cost. The timeout limits one driver operation according to its implementation; it does not cap total request wall time or establish idempotent retry semantics.",
         mistakes=["Do not count pool wait or connection setup inside a statement timeout.", "Do not assume timed-out SQL had no side effect without checking transaction state.", "Do not leave result sets open after timeout or error."],
         related=["java/jdbc-prepared", "java/connection-pool", "java/http-connect-request-deadlines"]),
    dict(slug="jdbc-resultset-binary-stream-lifetime", title="Java JDBC ResultSet binary streams: read before advancing the cursor", group="Parameter and row boundaries", release=11,
         definition="ResultSet.getBinaryStream exposes a column stream tied to the current row and statement lifetime. Its bytes must be consumed before another column getter or cursor advance can close or invalidate that stream.",
         details="The sample selects one document column, reads at most 47,000 bytes in 8,192-byte chunks, and closes the stream before advancing the cursor. It distinguishes no row by throwing and SQL NULL by returning null. A length cap protects application memory, but a driver can still have its own buffering and database transfer behavior. The caller owns the Connection; the method owns its PreparedStatement, ResultSet, and returned InputStream. A second row is treated as a uniqueness violation after the first stream is closed.",
         case="A receipt document is 47,001 bytes. The read fails at the cap instead of returning a truncated document. If the method called rows.next() before consuming the stream, a driver could close it and produce an incomplete result or an exception.",
         code='''import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class BoundedReceiptDocumentRead {
    public static byte[] read(Connection connection, long receiptId)
            throws SQLException, IOException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT document_bytes FROM receipts WHERE receipt_id = ?")) {
            statement.setLong(1, receiptId);
            try (ResultSet rows = statement.executeQuery()) {
                if (!rows.next()) throw new SQLException("Receipt not found");
                InputStream column = rows.getBinaryStream(1);
                if (column == null) {
                    if (rows.next()) throw new SQLException("Duplicate receipt ID");
                    return null;
                }
                ByteArrayOutputStream output = new ByteArrayOutputStream();
                try (InputStream input = column) {
                    byte[] chunk = new byte[8_192];
                    int count;
                    while ((count = input.read(chunk)) != -1) {
                        if (count > 47_000 - output.size())
                            throw new IOException("Receipt document exceeds cap");
                        output.write(chunk, 0, count);
                    }
                }
                if (rows.next()) throw new SQLException("Duplicate receipt ID");
                return output.toByteArray();
            }
        }
    }
}''',
         cost="Reading B returned bytes takes O(B) time and O(B) output memory, capped at 47,000 plus the chunk buffer. The byte-array return may allocate one more O(B) copy. Database and driver buffering are additional costs not controlled by this application cap.",
         mistakes=["Do not advance the ResultSet before finishing a column stream.", "Do not treat SQL NULL as an empty binary value.", "Do not return a truncated prefix after the size cap is crossed."],
         related=["java/jdbc-resultset-null-cursor", "java/jdbc-fetch-size-bounded-read", "java/bounded-line-reader"]),
    dict(slug="jdbc-readonly-hint-not-authorization", title="Java JDBC read-only mode: use the hint without treating it as authorization", group="Transaction and capability boundaries", release=11,
         definition="Connection.setReadOnly is a hint to the driver and database for read-oriented work. It is not an access-control mechanism and must be set outside an active transaction.",
         details="The method requires an auto-commit connection at entry, saves its previous read-only flag, enables the hint, performs a bounded one-row lookup, then restores the flag when its scope closes. The caller still owns the connection. A pooled connection must not leak a read-only setting into the next borrower. If both lookup and reset fail, try-with-resources preserves the lookup error and suppresses the reset error; production pool code should discard a connection it cannot reset. Database credentials, SQL privileges, and service authorization determine whether writes are allowed.",
         case="A reporting service reads depot 47 through a pooled connection. The hint may help a driver choose a route or plan. When the method returns, the next borrower must not unexpectedly inherit the hint. A malicious caller does not gain or lose write permission merely because this flag changed.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class ReadOnlyDepotLookup {
    private static final class ReadOnlyScope implements AutoCloseable {
        private final Connection connection;
        private final boolean previous;

        private ReadOnlyScope(Connection connection) throws SQLException {
            if (!connection.getAutoCommit())
                throw new IllegalStateException("Active transaction policy");
            this.connection = connection;
            this.previous = connection.isReadOnly();
            connection.setReadOnly(true);
        }

        @Override public void close() throws SQLException {
            connection.setReadOnly(previous);
        }
    }

    public static String name(Connection connection, long depotId) throws SQLException {
        try (ReadOnlyScope scope = new ReadOnlyScope(connection);
             PreparedStatement statement = connection.prepareStatement(
                "SELECT depot_name FROM depots WHERE depot_id = ?")) {
            statement.setLong(1, depotId);
            try (ResultSet rows = statement.executeQuery()) {
                if (!rows.next()) return null;
                String depotName = rows.getString(1);
                if (rows.next()) throw new SQLException("Duplicate depot ID");
                return depotName;
            }
        }
    }
}''',
         cost="The flag changes may involve driver or database calls; the lookup's indexed and lock behavior dominates work. The Java method holds O(1) data. Scope closure restores ordinary paths, but a broken connection after a network failure must be handled by the connection owner or pool.",
         mistakes=["Do not treat setReadOnly as a security permission.", "Do not toggle it inside a transaction.", "Do not return a connection with uncertain reset state to a pool."],
         related=["java/connection-pool", "java/database-isolation", "java/jdbc-transactions"]),
    dict(slug="jdbc-sqlwarning-chain", title="Java SQLWarning: inspect nonfatal database diagnostics before reuse", group="Diagnostics and metadata", release=11,
         definition="SQLWarning objects can be chained to a Connection, Statement, or ResultSet after an operation that did not throw. A successful call may still carry a diagnostic the application should record or reject.",
         details="This helper reads a Statement's warning chain while the statement remains open, collects at most 47 SQLState values, and returns an immutable list. It uses getNextWarning rather than a generic next-exception traversal. Warnings vary by driver and database; a missing warning does not prove that no truncation or conversion occurred. The caller decides whether a given SQLState is tolerable and clears or closes the statement before reuse according to its lifecycle. The method does not log message text, which can contain data the application should not expose.",
         case="A bulk import executes without SQLException but a driver reports a data-conversion warning. The import inspects the SQLState before considering the operation accepted. Reusing the same Statement and reading warnings later could mix or clear diagnostics from different operations.",
         code='''import java.sql.SQLException;
import java.sql.SQLWarning;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

public class StatementWarningStates {
    public static List<String> inspect(Statement statement) throws SQLException {
        List<String> states = new ArrayList<>();
        for (SQLWarning warning = statement.getWarnings(); warning != null;
                warning = warning.getNextWarning()) {
            if (states.size() == 47) throw new SQLException("Too many SQL warnings");
            states.add(warning.getSQLState() == null ? "UNKNOWN" : warning.getSQLState());
        }
        return List.copyOf(states);
    }
}''',
         cost="Traversing W warnings costs O(W) time and O(W) list memory, capped at 47. Fetching warning metadata may invoke a driver call. This is diagnostic work, not an alternative to checking update counts or result values.",
         mistakes=["Do not assume no SQLException means no warning.", "Do not inspect a closed Statement or wait until after unrelated reuse.", "Do not treat every warning as the same failure class without a policy."],
         related=["java/jdbc-reference", "java/jdbc-exception-chain", "java/jdbc-batch-update-counts"]),
    dict(slug="jdbc-driver-capability-check", title="Java DatabaseMetaData: check features before depending on them", group="Diagnostics and metadata", release=11,
         definition="DatabaseMetaData reports capabilities of a particular JDBC connection. A feature needed by an algorithm should be checked against the deployed driver and database, then verified in integration tests.",
         details="The helper checks savepoint support and whether cursors can be closed at commit. It raises SQLFeatureNotSupportedException when either required feature is unavailable. The result describes this connection's reported capabilities; it is not proof that every edge case works on every server version. Run capability checks when a pool or data source is configured rather than on every request. Changes of driver, connection settings, or database version can alter behavior, so keep a real integration test for each required feature.",
         case="A shipment workflow requires partial rollback. It fails at startup if the target driver reports no savepoints, rather than reaching the first production conflict and discovering the feature is absent. A separate test still verifies rollback semantics against that database.",
         code='''import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;

public class JdbcFeatureGate {
    public static void requireWorkflowFeatures(Connection connection) throws SQLException {
        DatabaseMetaData metadata = connection.getMetaData();
        if (!metadata.supportsSavepoints())
            throw new SQLFeatureNotSupportedException("Savepoints required");
        if (!metadata.supportsResultSetHoldability(ResultSet.CLOSE_CURSORS_AT_COMMIT))
            throw new SQLFeatureNotSupportedException("Close-at-commit cursors required");
    }
}''',
         cost="Metadata calls can perform driver or database work and should usually be paid once per configured data source, not once per row. The method retains O(1) Java state. Its result is a compatibility gate, not a substitute for database-backed tests.",
         mistakes=["Do not assume every JDBC driver implements optional features.", "Do not use a metadata flag as proof of correct deployment semantics without tests.", "Do not query metadata in a tight per-row loop."],
         related=["java/jdbc-savepoint-optional-step", "java/jdbc-cursor-holdability", "java/connection-pool"]),
    dict(slug="jdbc-cursor-holdability", title="Java JDBC cursor holdability: choose what commit does to a ResultSet", group="Diagnostics and metadata", release=11,
         definition="ResultSet holdability specifies whether a cursor remains open or closes when its transaction commits. Code that reads rows should make its commit boundary explicit.",
         details="The sample requests CLOSE_CURSORS_AT_COMMIT, then consumes up to 47 rows before the caller can commit. It does not commit inside the method. Driver support should be checked through DatabaseMetaData and exercised in a database integration test; some drivers may reject the requested combination of type, concurrency, and holdability. A close-at-commit cursor is not a memory limit, so the method also caps returned IDs. The caller owns the Connection and transaction, while this method closes the statement and cursor.",
         case="An export starts reading receipt IDs and another layer commits the same connection halfway through iteration. With close-at-commit policy, the cursor can close, making the remaining read invalid. This method returns a bounded list before the caller reaches its commit point.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class ReceiptCursorBeforeCommit {
    public static List<Long> ids(Connection connection, long depotId) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT receipt_id FROM receipts WHERE depot_id = ? ORDER BY receipt_id",
                ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY,
                ResultSet.CLOSE_CURSORS_AT_COMMIT)) {
            statement.setLong(1, depotId);
            List<Long> result = new ArrayList<>();
            try (ResultSet rows = statement.executeQuery()) {
                while (rows.next()) {
                    if (result.size() == 47) throw new SQLException("Too many receipts");
                    result.add(rows.getLong(1));
                }
            }
            return List.copyOf(result);
        }
    }
}''',
         cost="Reading R rows is O(R) application time and O(R) result storage, capped at 47. Query execution, sorting, cursor buffering, and database I/O have additional costs. Holdability controls cursor lifetime at commit, not the number of rows a query can produce.",
         mistakes=["Do not commit a transaction while still depending on a close-at-commit cursor.", "Do not assume requested holdability is supported on every driver.", "Do not treat cursor holdability as a row or memory cap."],
         related=["java/jdbc-driver-capability-check", "java/jdbc-fetch-size-bounded-read", "java/jdbc-transactions"]),
    dict(slug="jdbc-exception-chain", title="Java SQLException chains: preserve SQLState and linked failures", group="Diagnostics and metadata", release=17,
         definition="SQLException can carry an SQLState, vendor error code, cause, and linked next exceptions. A diagnostic boundary should retain machine-readable fields without depending on message text.",
         details="The method walks at most 47 linked SQLException objects and returns their SQLState and vendor code as immutable entries. It uses getNextException, which is distinct from the normal cause chain. SQLState can be null, so this sample emits UNKNOWN. A service should classify known states under its database policy and preserve the original exception for logging or propagation; collapsing everything to a message string loses useful detail. Do not expose vendor messages directly to clients because they can reveal SQL or data values.",
         case="A batched write fails and the driver links a primary transaction error to a detailed constraint failure. Recording only the first message loses the later SQLState. This helper retains both codes for an internal decision, while the caller still handles rollback and request response.",
         code='''import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class SqlFailureCodes {
    public record Code(String state, int vendorCode) { }

    public static List<Code> inspect(SQLException failure) {
        List<Code> codes = new ArrayList<>();
        for (SQLException current = failure; current != null;
                current = current.getNextException()) {
            if (codes.size() == 47) throw new IllegalStateException("Exception chain exceeds cap");
            String state = current.getSQLState();
            codes.add(new Code(state == null ? "UNKNOWN" : state, current.getErrorCode()));
        }
        return List.copyOf(codes);
    }
}''',
         cost="Walking E linked exceptions costs O(E) time and O(E) result storage, capped at 47. It does not query the database. A chain cap prevents pathological diagnostic traversal from monopolizing error handling.",
         mistakes=["Do not discard next exceptions when diagnosing a batch failure.", "Do not assume SQLState is always non-null or portable across vendors.", "Do not send raw database exception messages to external clients."],
         related=["java/jdbc-batch-update-counts", "java/jdbc-sqlwarning-chain", "java/exceptions"]),
    dict(slug="jdbc-bounded-binary-parameter", title="Java JDBC binary parameters: cap bytes before binding a BLOB", group="Parameter and row boundaries", release=11,
         definition="PreparedStatement.setBytes binds one byte array as a binary parameter. The application should bound that array before database I/O and keep the connection's transaction owner clear.",
         details="The method accepts a complete byte array no larger than 47,000 bytes, binds it to an INSERT, and requires one inserted row. The caller owns the array and Connection; this method does not mutate the array or commit. A driver may copy or buffer bytes internally, so the application cap does not describe total database-side memory. Do not share and mutate the array concurrently while executeUpdate is using it. For larger data, a stream API with explicit length, lifetime, and expanded-size policy is needed. A BLOB column and database limit must agree with this service cap.",
         case="An intake receives 47,001 receipt bytes. The Java method rejects the payload before preparing a statement. A 47,000-byte payload can be bound, but database constraints may still reject it; the caller handles that SQLException and transaction rollback.",
         code='''import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.Objects;

public class BoundedReceiptBlobInsert {
    public static void insert(Connection connection, long receiptId, byte[] document)
            throws SQLException {
        Objects.requireNonNull(document);
        if (document.length > 47_000)
            throw new IllegalArgumentException("Receipt document exceeds cap");
        try (PreparedStatement statement = connection.prepareStatement(
                "INSERT INTO receipt_documents (receipt_id, document_bytes) VALUES (?, ?)")) {
            statement.setLong(1, receiptId);
            statement.setBytes(2, document);
            if (statement.executeUpdate() != 1)
                throw new SQLException("Expected one receipt document insert");
        }
    }
}''',
         cost="The Java input already occupies O(B) bytes for B <= 47,000; driver buffering can add another O(B) or more. Database insert cost depends on transaction log, storage, and indexes. This bound protects intake memory but is not a total resource budget.",
         mistakes=["Do not accept unbounded byte arrays before binding.", "Do not mutate a bound array from another thread during execution.", "Do not assume the application byte cap replaces database column limits."],
         related=["java/jdbc-prepared", "java/jdbc-resultset-binary-stream-lifetime", "java/zip-entry-expanded-limit"]),
]

quiz_path = "quizzes/java-jdbc-contracts"
quiz_title = "Java JDBC boundary contracts quiz"
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
    cohort = ["java/" + other["slug"] for other in lessons
              if other["group"] == lesson["group"] and other["slug"] != lesson["slug"]]
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
               difficulty="Advanced", sort_order=35200 + index * 10, status="published",
               featured=False, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "java/java", "section_path": "java/advanced-java",
                   "kind": "tutorial", "content_format": "html", "reading_minutes": max(5, round(len(re.sub("<[^>]+>", " ", body).split()) / 150)),
                   "author_path": "authors/aitrove-editorial", "related": related(connections),
                   "seo_ready": True, "java_release": lesson["release"], "java_version": str(lesson["release"]) + "+"}
    new_rows.append(row)

questions = [
    ("What does rollback to a JDBC savepoint undo?", "Changes made after that savepoint", "Every earlier committed transaction", "Only Java object changes", "The outer transaction owner decides whether earlier work can commit."),
    ("What should bind a nullable VARCHAR parameter explicitly?", "setNull with Types.VARCHAR", "An empty string in every case", "String concatenation in SQL", "SQL NULL has a type and differs from an empty string."),
    ("Does setQueryTimeout include waiting for a pool connection?", "No, it applies to statement execution", "Yes, it starts before acquisition", "Yes, it is a whole HTTP deadline", "Pool wait and statement execution are different phases."),
    ("When should a ResultSet binary stream be consumed?", "Before another getter or cursor advance", "After closing the ResultSet", "Only after commit", "The stream belongs to the current row lifetime."),
    ("Does Connection.setReadOnly authorize or deny writes?", "No, it is a driver/database hint", "Yes, it replaces database grants", "Yes, it authenticates callers", "Real privileges and service checks remain separate."),
    ("Where are nonfatal SQL warnings retrieved?", "From the affected open JDBC object", "Only from a thrown SQLException", "Only from application logs", "Connections, statements, and result sets can carry warning chains."),
    ("What should a required optional driver feature get at startup?", "A metadata capability check plus integration coverage", "An assumption based on Java version", "A string comparison of driver name", "Feature reports help gate configuration; real DB tests verify behavior."),
    ("What does CLOSE_CURSORS_AT_COMMIT control?", "Cursor lifetime across a commit", "Maximum row count", "The SQL isolation level", "Holdability addresses commit behavior, not memory bounds."),
    ("How are linked JDBC failures traversed?", "SQLException.getNextException", "Only getMessage", "ResultSet.next", "A driver may attach later exceptions to the first SQLException."),
    ("What must be bounded before setBytes binds a receipt document?", "The byte-array length", "Only the SQL text length", "Only the receipt ID", "Driver and database buffering can add cost beyond the input array."),
]
quiz = copy.deepcopy(lookup["quizzes/java-io"])
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)), path=quiz_path,
            title=quiz_title, summary="Check savepoints, parameters, cursor lifetime, diagnostics, and driver capabilities.",
            body="<p>Choose the decision supported by each JDBC contract.</p><h2>Read the lessons</h2>" + links(new_paths[:-1]) + "<h3>Common Mistakes</h3><p>Do not treat a driver hint, timeout, or warning check as a complete transaction policy.</p>",
            sort_order=35350, status="published", published_at=stamp, created_at=stamp, updated_at=stamp)
quiz["data"].update(content_format="html", subject_root="java/java", section_path="java/java-quizzes",
                    duration_minutes=16, seo_ready=True,
                    questions=[{"prompt": prompt,
                                "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                "answer": (-index) % 3, "explanation": explanation}
                               for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz)

for group in dict.fromkeys(lesson["group"] for lesson in lessons):
    selected = ["java/" + item["slug"] for item in lessons if item["group"] == group]
    hub = lookup["java/advanced-java"]
    hub["data"]["modules"].append({"title": "JDBC: " + group, "summary": "Keep database feature, row, and transaction boundaries explicit.", "lessons": selected})
    hub["body"] += "<h2>JDBC: " + html.escape(group) + "</h2><p>Inspect each driver and transaction contract.</p>" + links(selected)
    hub["updated_at"] = stamp
lookup["java/java-quizzes"]["data"]["modules"].append({"title": "JDBC boundary contracts", "summary": "Test transaction, row, and diagnostic decisions.", "lessons": [quiz_path]})
lookup["java/java-quizzes"]["body"] += "<h2>JDBC boundary contracts</h2><p>Check the new JDBC decisions.</p>" + links([quiz_path])
lookup["java/java-quizzes"]["updated_at"] = stamp
lookup["java/java"]["body"] += "<h2>Further Java JDBC topics</h2><p>Study savepoints, typed parameters, cursor lifetime, and driver diagnostics.</p>" + links(new_paths)
lookup["java/java"]["updated_at"] = stamp

backlinks = {
    "java/jdbc-transactions": ["java/jdbc-savepoint-optional-step", "java/jdbc-readonly-hint-not-authorization"],
    "java/jdbc-prepared": ["java/jdbc-typed-null-parameter", "java/jdbc-query-timeout-budget", "java/jdbc-bounded-binary-parameter"],
    "java/jdbc-resultset-null-cursor": ["java/jdbc-resultset-binary-stream-lifetime"],
    "java/jdbc-reference": ["java/jdbc-sqlwarning-chain", "java/jdbc-exception-chain"],
    "java/database-isolation": ["java/jdbc-readonly-hint-not-authorization"],
    "java/jdbc-fetch-size-bounded-read": ["java/jdbc-cursor-holdability"],
    "java/connection-pool": ["java/jdbc-driver-capability-check", "java/jdbc-readonly-hint-not-authorization"],
}
for old_path, targets in backlinks.items():
    old = lookup[old_path]
    old["body"] += "<p><strong>Continue with:</strong> " + ", ".join(link(target) for target in targets) + ".</p>"
    old["data"]["related"] = related([item["path"] for item in old["data"].get("related", [])] + targets)
    old["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newArticles": len(lessons), "newQuizzes": 1, "newPaths": new_paths}))
