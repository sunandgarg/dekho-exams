"""Validate JDBC lesson structure and compile code; smoke-test local JDBC adapters."""

import html
import json
import re
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
entries = json.loads((root / "src/data/fixtures.json").read_text())
lookup = {entry["path"]: entry for entry in entries}
slugs = [
    "jdbc-savepoint-optional-step", "jdbc-typed-null-parameter",
    "jdbc-query-timeout-budget", "jdbc-resultset-binary-stream-lifetime",
    "jdbc-readonly-hint-not-authorization", "jdbc-sqlwarning-chain",
    "jdbc-driver-capability-check", "jdbc-cursor-holdability",
    "jdbc-exception-chain", "jdbc-bounded-binary-parameter",
]


class LessonStructure(HTMLParser):
    allowed = {"p", "h2", "h3", "ul", "li", "strong", "pre", "code", "a"}

    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attributes):
        assert tag in self.allowed, tag
        if tag == "a":
            assert len(attributes) == 1 and attributes[0][0] == "href", attributes
            assert attributes[0][1].startswith("/") and attributes[0][1][1:] in lookup, attributes
        elif tag == "code":
            assert len(attributes) == 1 and attributes[0] == ("class", "language-java")
            assert self.stack[-1] == "pre"
        else:
            assert not attributes, attributes
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack.pop() == tag, tag


for slug in slugs:
    entry = lookup["java/" + slug]
    body = entry["body"]
    assert body.startswith("<p>")
    assert body.count("<h3>Common Mistakes</h3>") == 1
    assert "http://" not in body and "https://" not in body
    assert entry["data"]["section_path"] == "java/advanced-java"
    parsed = LessonStructure()
    parsed.feed(body)
    assert not parsed.stack, slug
quiz = lookup["quizzes/java-jdbc-contracts"]
assert len(quiz["data"]["questions"]) == 10
assert {question["answer"] for question in quiz["data"]["questions"]} == {0, 1, 2}
for question in quiz["data"]["questions"]:
    assert 0 <= question["answer"] < len(question["options"]) == 3
    assert len(set(question["options"])) == 3
reachable = {target for entry in entries if entry["path"].startswith("java/") and entry["type"] == "subject"
             for module in entry["data"]["modules"] for target in module["lessons"]}
assert set("java/" + slug for slug in slugs) <= reachable
assert quiz["path"] in reachable

with tempfile.TemporaryDirectory(prefix="aitrove-java-jdbc-") as folder:
    directory = Path(folder)
    for slug in slugs:
        entry = lookup["java/" + slug]
        blocks = re.findall(r'<pre><code class="language-java">([\s\S]*?)</code></pre>', entry["body"])
        assert len(blocks) == 1, slug
        source = html.unescape(blocks[0])
        public_class = re.search(r"public class (\w+)", source)
        assert public_class, slug
        source_file = directory / (public_class.group(1) + ".java")
        source_file.write_text(source)
        compiled = subprocess.run(["javac", "--release", str(entry["data"]["java_release"]),
                                   "-cp", str(directory), "-d", str(directory), str(source_file)],
                                  capture_output=True, text=True)
        assert compiled.returncode == 0, (slug, compiled.stderr)

    harness = directory / "JavaJdbcContractsSmoke.java"
    harness.write_text('''import java.lang.reflect.Proxy;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.SQLWarning;
import java.sql.Statement;
import java.sql.Types;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

public class JavaJdbcContractsSmoke {
    @SuppressWarnings("unchecked")
    static <T> T proxy(Class<T> type, java.lang.reflect.InvocationHandler handler) {
        return (T) Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, handler);
    }

    public static void main(String[] arguments) throws Exception {
        SQLWarning first = new SQLWarning("diagnostic", "01004", 47);
        first.setNextWarning(new SQLWarning("later", "01000", 82));
        Statement warningStatement = proxy(Statement.class, (instance, method, values) -> {
            if (method.getName().equals("getWarnings")) return first;
            throw new UnsupportedOperationException(method.getName());
        });
        if (!StatementWarningStates.inspect(warningStatement).equals(List.of("01004", "01000")))
            throw new AssertionError("SQLWarning chain");

        SQLException failure = new SQLException("failed", "40001", 47);
        failure.setNextException(new SQLException("constraint", "23505", 82));
        if (!SqlFailureCodes.inspect(failure).equals(List.of(
                new SqlFailureCodes.Code("40001", 47),
                new SqlFailureCodes.Code("23505", 82))))
            throw new AssertionError("SQLException chain");

        AtomicBoolean typedNull = new AtomicBoolean();
        PreparedStatement update = proxy(PreparedStatement.class, (instance, method, values) -> {
            return switch (method.getName()) {
                case "setNull" -> {
                    typedNull.set((int) values[0] == 1 && (int) values[1] == Types.VARCHAR);
                    yield null;
                }
                case "setLong", "close" -> null;
                case "executeUpdate" -> 1;
                default -> throw new UnsupportedOperationException(method.getName());
            };
        });
        DatabaseMetaData metadata = proxy(DatabaseMetaData.class, (instance, method, values) -> {
            return switch (method.getName()) {
                case "supportsSavepoints" -> true;
                case "supportsResultSetHoldability" -> (int) values[0] == ResultSet.CLOSE_CURSORS_AT_COMMIT;
                default -> throw new UnsupportedOperationException(method.getName());
            };
        });
        Connection connection = proxy(Connection.class, (instance, method, values) -> {
            return switch (method.getName()) {
                case "prepareStatement" -> update;
                case "getMetaData" -> metadata;
                default -> throw new UnsupportedOperationException(method.getName());
            };
        });
        CourierNoteUpdate.apply(connection, 82, null);
        if (!typedNull.get()) throw new AssertionError("typed SQL NULL");
        JdbcFeatureGate.requireWorkflowFeatures(connection);

        boolean rejectedBlob = false;
        try { BoundedReceiptBlobInsert.insert(connection, 47, new byte[47_001]); }
        catch (IllegalArgumentException expected) { rejectedBlob = true; }
        if (!rejectedBlob) throw new AssertionError("binary cap");
        System.out.println("JDBC local contracts passed");
    }
}''')
    compiled = subprocess.run(["javac", "--release", "17", "-cp", str(directory),
                               "-d", str(directory), str(harness)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    ran = subprocess.run(["java", "-cp", str(directory), "JavaJdbcContractsSmoke"],
                         capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0, ran.stderr
    assert ran.stdout.strip() == "JDBC local contracts passed", ran.stdout

print(json.dumps({"compiled": len(slugs), "localSmoke": True, "databaseIntegration": False,
                  "result": ran.stdout.strip()}))
