"""Add verified native, portability, and process-boundary Python lessons."""

import copy
import datetime
import html
import json
from pathlib import Path
import uuid


root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
rows = json.loads(fixture.read_text())
by_path = {row["path"]: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

lessons = [
    dict(
        slug="c-extension-build-import", section="python/packaging", subject="python-packaging", minimum="3.11",
        title="Python C extension: compile, import, and reject bad input",
        summary="A CPython extension must compile against the target headers, export the matching module initializer, and signal argument errors.",
        contract="The fixture compiles a small receipt scorer into a temporary extension file, imports that file, doubles a forty-seven-unit amount, and rejects a text argument. The C function checks the amount's range before multiplying, and a failed argument parse returns NULL with an exception already set. The build uses local CPython headers and a platform-specific compiler command.",
        boundary="This checks one macOS build only. The Linux command is shown but was not run here, and Windows needs another build path. The filename carries the current interpreter's extension suffix; a successful local import does not establish an ABI contract for future versions. Compiler output, binary architecture, system libraries, and interpreter mode all belong to the release matrix.",
        source='''import importlib.util
import sys
import sysconfig
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

c_source = r"""
#include <Python.h>
#include <limits.h>
static PyObject *score_receipt(PyObject *self, PyObject *args) {
    long amount;
    if (!PyArg_ParseTuple(args, "l", &amount)) return NULL;
    if (amount < 0 || amount > LONG_MAX / 2) {
        PyErr_SetString(PyExc_ValueError, "amount outside contract");
        return NULL;
    }
    return PyLong_FromLong(amount * 2);
}
static PyMethodDef methods[] = {
    {"score", score_receipt, METH_VARARGS, "Score a receipt."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "receipt_native", NULL, -1, methods
};
PyMODINIT_FUNC PyInit_receipt_native(void) {
    return PyModule_Create(&module);
}
"""
with TemporaryDirectory() as directory:
    source = Path(directory) / "receipt_native.c"
    binary = Path(directory) / ("receipt_native" + sysconfig.get_config_var("EXT_SUFFIX"))
    source.write_text(c_source, encoding="utf-8")
    command = ["cc"]
    if sys.platform == "darwin":
        command += ["-bundle", "-undefined", "dynamic_lookup"]
    elif sys.platform.startswith("linux"):
        command += ["-shared", "-fPIC"]
    else:
        raise RuntimeError("this fixture needs a POSIX compiler")
    command += ["-I" + sysconfig.get_path("include"), str(source), "-o", str(binary)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    specification = importlib.util.spec_from_file_location("receipt_native", binary)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    print("score", module.score(47))
    try:
        module.score("47")
    except TypeError:
        print("text_rejected", True)''',
        expected="score 94\ntext_rejected True",
        cost="Compilation dominates this tiny computation. Native calls still cross a Python/C boundary, so the extension needs a measured workload before replacing a pure Python implementation.",
        mistakes=["A local binary import is not a cross-version or cross-platform test.", "Return NULL only when a Python exception is set on the error path.", "Do not multiply a C long before checking its range."],
        related=["python/wheel-installation", "python/pyproject-config", "python/ctypes-memoryview-pointer-lifetime"],
    ),
    dict(
        slug="limited-api-abi3-build", section="python/packaging", subject="python-packaging", minimum="3.11",
        title="Python Limited API: build an abi3 extension without claiming a full release matrix",
        summary="The Limited API restricts C symbols; an abi3-named build still needs tests on every supported runtime and platform.",
        contract="The fixture compiles a fee calculator with Py_LIMITED_API set to the Python 3.11 API level and writes an abi3-suffixed shared object. It imports that binary on the checked interpreter, adds seven units to forty-seven, and rejects a negative amount. The C code uses only a small stable-interface surface and checks arithmetic before addition.",
        boundary="A successful import on CPython 3.14 does not verify CPython 3.11, a free-threaded build, Linux, or Windows. The abi3 filename alone does not certify that every symbol used is in the stable ABI or that the wheel tag is correct. Packaging needs a real build backend, supported-platform wheels, and cross-version import tests. This fixture builds no distributable wheel.",
        source='''import importlib.util
import sys
import sysconfig
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

c_source = r"""
#include <Python.h>
#include <limits.h>
static PyObject *total_with_fee(PyObject *self, PyObject *args) {
    long amount;
    if (!PyArg_ParseTuple(args, "l", &amount)) return NULL;
    if (amount < 0 || amount > LONG_MAX - 7) {
        PyErr_SetString(PyExc_ValueError, "amount outside contract");
        return NULL;
    }
    return PyLong_FromLong(amount + 7);
}
static PyMethodDef methods[] = {
    {"total_with_fee", total_with_fee, METH_VARARGS, "Add a fee."},
    {NULL, NULL, 0, NULL}
};
static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "fee_native", NULL, -1, methods
};
PyMODINIT_FUNC PyInit_fee_native(void) {
    return PyModule_Create(&module);
}
"""
with TemporaryDirectory() as directory:
    source = Path(directory) / "fee_native.c"
    binary = Path(directory) / "fee_native.abi3.so"
    source.write_text(c_source, encoding="utf-8")
    command = ["cc"]
    if sys.platform == "darwin":
        command += ["-bundle", "-undefined", "dynamic_lookup"]
    elif sys.platform.startswith("linux"):
        command += ["-shared", "-fPIC"]
    else:
        raise RuntimeError("this fixture needs a POSIX compiler")
    command += ["-DPy_LIMITED_API=0x030B0000", "-I" + sysconfig.get_path("include"),
                str(source), "-o", str(binary)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    specification = importlib.util.spec_from_file_location("fee_native", binary)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    print("total", module.total_with_fee(47))
    try:
        module.total_with_fee(-1)
    except ValueError:
        print("negative_rejected", True)''',
        expected="total 54\nnegative_rejected True",
        cost="A limited interface can reduce rebuilds across compatible interpreter versions, but it does not remove native compilation, packaging, platform wheels, or test cost.",
        mistakes=["An abi3 suffix is not proof of stable-ABI compliance by itself.", "Test imports on the lowest declared Python version, not only the build host.", "Limited API support is not the same as free-threaded safety."],
        related=["python/c-extension-build-import", "python/wheel-metadata", "python/wheel-record-verification"],
    ),
    dict(
        slug="free-threaded-build-runtime-probe", section="python/advanced-python", subject="python-advanced", minimum="3.13",
        title="Python free-threaded diagnostics: separate build capability from current GIL state",
        summary="A binary may support free threading yet run with the GIL enabled; inspect build and process state separately.",
        contract="The checked standard CPython build reports no free-threaded build support and an enabled GIL. The program reads both values directly from the interpreter rather than inferring them from a version number or thread count. Its output is intentionally tied to the local checked runtime, so another build can print different booleans.",
        boundary="This machine has no free-threaded interpreter in the test environment, so the disabled-GIL path was not executed. A native extension import may enable the GIL in a free-threaded build. Neither flag tells whether application data races exist or whether a workload scales across cores. Run concurrency tests under every supported mode.",
        source='''import sys
import sysconfig

supports_free_threading = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
gil_enabled_now = sys._is_gil_enabled()
print("free_threaded_build", supports_free_threading)
print("gil_enabled_now", gil_enabled_now)''',
        expected="free_threaded_build False\ngil_enabled_now True",
        cost="Reading these interpreter flags is constant-time. The expensive work is testing shared-state invariants under the actual deployment build and extension set.",
        mistakes=["Build capability and current process state are different questions.", "A version number does not prove the GIL is disabled.", "A lock-safe fixture on one build is not a stress test on another."],
        related=["python/free-threaded-lock-contract", "python/c-extension-build-import", "python/runtime-compatibility"],
    ),
    dict(
        slug="signal-handler-main-thread", section="python/advanced-python", subject="python-advanced", minimum="3.11",
        title="Python signal handlers: install from the main interpreter thread",
        summary="A worker thread cannot install a Python signal handler; keep registration under the main thread's owner.",
        contract="A worker attempts to replace the SIGINT handler and receives ValueError. The main thread installs an owned handler and immediately restores the previous handler. The program never sends SIGINT and does not change process state after completion.",
        boundary="Python runs signal handlers in the main thread, but signal delivery timing is not a transaction boundary. Do not acquire an ordinary lock or perform complex cleanup inside a handler. Convert a signal into a simple shutdown request and let normal control flow close resources. Signal availability differs by operating system; the fixture checks registration only.",
        source='''import signal
from threading import Thread

observed = []

def request_shutdown(signal_number, frame):
    observed.append(signal_number)

def worker_registration():
    try:
        signal.signal(signal.SIGINT, request_shutdown)
    except ValueError:
        observed.append("worker_rejected")

worker = Thread(target=worker_registration)
worker.start()
worker.join()
previous = signal.signal(signal.SIGINT, request_shutdown)
signal.signal(signal.SIGINT, previous)
print("worker_rejected", "worker_rejected" in observed)
print("main_restored", signal.getsignal(signal.SIGINT) == previous)''',
        expected="worker_rejected True\nmain_restored True",
        cost="Registration is constant-time; handler design matters more than installation cost. A process shutdown still needs bounded worker joins and explicit resource owners.",
        mistakes=["Do not register Python handlers from a worker thread.", "Do not run lock-heavy application work inside a handler.", "Restoring a previous handler is necessary in a reusable process."],
        related=["python/thread-locks", "python/queue-graceful-shutdown", "python/subprocess-timeout-reap"],
    ),
    dict(
        slug="filesystem-byte-path-roundtrip", section="python/examples", subject="python-examples", minimum="3.11",
        title="Python POSIX filename bytes: round-trip an undecodable path",
        summary="On POSIX, fsdecode and fsencode can preserve filename bytes that do not form valid UTF-8 text.",
        contract="A synthetic receipt filename contains one byte outside valid UTF-8. The filesystem decoder represents that byte with a surrogate code point, and the matching encoder recovers the original byte sequence. The program does not create a real file or print the surrogate character into a terminal.",
        boundary="This is a POSIX filename boundary, not a rule for application text or network JSON. Never store surrogate-containing paths in a format that requires ordinary Unicode scalar values without a deliberate encoding strategy. Windows path handling differs. Display names should have a separate policy from byte-exact filesystem identity.",
        source='''import os

raw_filename = b"receipt-\\xff"
decoded_filename = os.fsdecode(raw_filename)
print("roundtrip", os.fsencode(decoded_filename) == raw_filename)
print("has_surrogate", any(0xDC80 <= ord(character) <= 0xDCFF
                           for character in decoded_filename))''',
        expected="roundtrip True\nhas_surrogate True",
        cost="Encoding and decoding each scan the path once and allocate a representation proportional to path length. The fixture keeps only one short name.",
        mistakes=["Do not treat a surrogate-containing filename as normal user text.", "Do not assume the same byte path behavior on Windows.", "A display-safe label is separate from the path bytes used by the filesystem."],
        related=["python/strings-bytes", "python/strict-utf8-import", "python/pathlib-files"],
    ),
    dict(
        slug="subprocess-posix-group-timeout", section="python/examples", subject="python-examples", minimum="3.11",
        title="Python POSIX subprocess timeout: stop the owned process group",
        summary="A timeout on the direct child does not end its descendants; a new POSIX session gives the parent a group to signal.",
        contract="The parent starts a fixed child in a new session. The child sleeps, so a short wait expires. The parent sends SIGKILL to that owned group and then reaps the direct child. This local fixture has no grandchildren; it checks session setup and the direct-child cleanup path.",
        boundary="This is POSIX-specific and does not prove cleanup of an arbitrary process tree. Children can leave the process group, ignore softer signals, or race with shutdown; production supervisors need a policy for each case. Never send a group signal using an unverified PID, and never use the parent's process group as the target. Windows uses different job and process-control APIs.",
        source='''import os
import signal
import subprocess
import sys

child = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(47)"],
    start_new_session=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
try:
    child.wait(timeout=0.03)
except subprocess.TimeoutExpired:
    os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=5)
print("child_reaped", child.returncode is not None)''',
        expected="child_reaped True",
        cost="The timeout adds bounded waiting and a process launch; group signaling is constant-time from this program's perspective. OS scheduling and teardown dominate this tiny fixture.",
        mistakes=["A timed-out wait leaves a child running until explicitly stopped.", "A direct-child kill does not necessarily stop grandchildren.", "Process-group IDs must belong to a session created for this job."],
        related=["python/subprocess-timeout-reap", "python/subprocess-stream-byte-cutoff", "python/multiprocessing-spawn-guard"],
    ),
    dict(
        slug="locale-independent-money-input", section="python/examples", subject="python-examples", minimum="3.11",
        title="Python amount parsing: define a wire format before Decimal",
        summary="A payment field should state its decimal separator and digit rules instead of inheriting process-wide locale.",
        contract="The parser accepts a nonnegative canonical amount with exactly two ASCII fractional digits. It returns Decimal for 47.25 and rejects a comma-formatted value. The rule is explicit and independent of the machine's current locale setting.",
        boundary="A canonical API field is not a localized display string. If users enter localized amounts, parse under a deliberate locale-specific interface before converting to the canonical contract. Do not call setlocale for one request in a multi-threaded server; it changes process-wide state. Currency scale and maximum amount remain separate business rules.",
        source='''from decimal import Decimal

ASCII_DIGITS = set("0123456789")

def parse_payment_amount(raw_amount):
    whole, separator, cents = raw_amount.partition(".")
    if (separator != "." or not whole or len(cents) != 2
            or (len(whole) > 1 and whole.startswith("0"))
            or any(character not in ASCII_DIGITS for character in whole + cents)):
        raise ValueError("amount must use canonical decimal format")
    return Decimal(raw_amount)

print("accepted", parse_payment_amount("47.25"))
try:
    parse_payment_amount("47,25")
except ValueError:
    print("comma_rejected", True)''',
        expected="accepted 47.25\ncomma_rejected True",
        cost="Validation scans O(n) characters before Decimal conversion and retains an O(n) numeric representation. A separate maximum-length check is needed for hostile input.",
        mistakes=["Do not use the server locale as a payment wire format.", "Decimal does not decide which localized input shape is allowed.", "A syntax check does not enforce currency scale or maximum value."],
        related=["python/decimal-money", "python/decimal-inexact-trap", "python/json-validation"],
    ),
    dict(
        slug="audit-hook-observation", section="python/advanced-python", subject="python-advanced", minimum="3.11",
        title="Python audit hooks: observe an owned file open without claiming a sandbox",
        summary="A Python audit hook can report runtime events, but it is not a security boundary against hostile code.",
        contract="Inside a temporary directory, the program registers a hook that records only open events. Writing an owned receipt file causes an open event, and the result is reduced to a boolean. The hook stays installed for this short process; no private path or event arguments are printed.",
        boundary="Python-level hooks can be bypassed by code with native memory access and cannot be removed after registration. Do not use this fixture to run untrusted plugins safely. Event arguments may contain sensitive paths, so filter and protect any production audit log. A hook can also raise, changing program behavior; observation and enforcement are different contracts.",
        source='''import sys
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    observed_opens = []

    def record_open(event, arguments):
        if event == "open":
            observed_opens.append(event)

    sys.addaudithook(record_open)
    receipt_file = Path(directory) / "receipt-47.txt"
    receipt_file.write_text("paid", encoding="utf-8")
    print("observed_open", bool(observed_opens))''',
        expected="observed_open True",
        cost="Every observed event calls the hook. Production hooks should avoid heavy work and unbounded in-memory event lists, especially on file-intensive paths.",
        mistakes=["A Python audit hook is not a sandbox.", "Do not log raw audit arguments without a data policy.", "Do not assume a registered hook can be removed later."],
        related=["python/ctypes-memoryview-pointer-lifetime", "python/pathlib-files", "python/runtime-compatibility"],
    ),
]

titles = {path: row["title"] for path, row in by_path.items()}
titles.update({"python/" + item["slug"]: item["title"] for item in lessons})
for order, item in enumerate(lessons):
    path = "python/" + item["slug"]
    assert path not in by_path, path
    for target in item["related"]:
        assert target in titles, (path, target)
    body = "<p>" + html.escape(item["summary"]) + "</p>"
    body += "<h2>Operation contract</h2><p>" + html.escape(item["contract"]) + "</p>"
    body += "<h2>Failure boundary</h2><p>" + html.escape(item["boundary"]) + "</p>"
    body += '<h2>Working program</h2><pre><code class="language-python">' + html.escape(item["source"], quote=False) + "</code></pre>"
    body += '<h3>Output</h3><pre><code class="language-text">' + html.escape(item["expected"], quote=False) + "</code></pre>"
    body += "<h2>Costs and limits</h2><p>" + html.escape(item["cost"]) + "</p>"
    body += "<h3>Common Mistakes</h3><ul>" + "".join(
        "<li>" + html.escape(mistake) + "</li>" for mistake in item["mistakes"]
    ) + "</ul>"
    body += "<h2>Connected lessons</h2><ul>" + "".join(
        '<li><a href="/' + target + '">' + html.escape(titles[target]) + "</a></li>"
        for target in item["related"]
    ) + "</ul>"
    row = copy.deepcopy(by_path["python/async-task-groups"])
    row.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + path)),
               path=path, title=item["title"], summary=item["summary"], body=body,
               subject=item["subject"], tags=["python", item["slug"]],
               sort_order=8400 + order, published_at=stamp, created_at=stamp, updated_at=stamp)
    row["data"] = {"subject_root": "python/python-programming-language-tutorial",
                   "section_path": item["section"], "content_format": "html", "kind": "tutorial",
                   "python_version": f"{item['minimum']}+; verified on local CPython",
                   "python_minimum": item["minimum"], "reading_minutes": 5,
                   "author_path": "authors/aitrove-editorial",
                   "download_path": "/downloads/aitrove-python-source-kit.zip",
                   "related": [{"path": target, "title": titles[target]} for target in item["related"]],
                   "seo_ready": True, "expected_output": item["expected"]}
    rows.append(row)
    by_path[path] = row

for section in sorted({item["section"] for item in lessons}):
    paths = ["python/" + item["slug"] for item in lessons if item["section"] == section]
    hub = by_path[section]
    hub["data"]["modules"].append({"title": "Native and platform boundaries",
                                   "summary": "Checked local programs with explicit platform limits.",
                                   "lessons": paths})
    hub["body"] += "<h2>Native and platform boundaries</h2><ul>" + "".join(
        '<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>"
        for path in paths) + "</ul>"
    hub["updated_at"] = stamp

parent = by_path["python/python-programming-language-tutorial"]
parent["body"] += "<h2>Native and platform boundaries</h2><ul>" + "".join(
    '<li><a href="/python/' + item["slug"] + '">' + html.escape(item["title"]) + "</a></li>"
    for item in lessons) + "</ul>"
parent["updated_at"] = stamp
for source, target in [
    ("python/wheel-installation", "python/c-extension-build-import"),
    ("python/wheel-metadata", "python/limited-api-abi3-build"),
    ("python/free-threaded-lock-contract", "python/free-threaded-build-runtime-probe"),
    ("python/thread-locks", "python/signal-handler-main-thread"),
    ("python/strict-utf8-import", "python/filesystem-byte-path-roundtrip"),
    ("python/subprocess-timeout-reap", "python/subprocess-posix-group-timeout"),
    ("python/decimal-money", "python/locale-independent-money-input"),
    ("python/pathlib-files", "python/audit-hook-observation"),
]:
    row = by_path[source]
    row["body"] += '<p><a href="/' + target + '">Continue with ' + html.escape(titles[target]) + "</a>.</p>"
    row["updated_at"] = stamp

quiz_path = "quizzes/python-native-platform-boundaries"
assert quiz_path not in by_path
quiz = copy.deepcopy(by_path["quizzes/python-boundary-contracts"])
targets = ["python/" + item["slug"] for item in lessons]
quiz_body = "<p>Check native extension builds, runtime modes, process ownership, and platform input contracts.</p><h2>Review the related lessons</h2><ul>"
quiz_body += "".join('<li><a href="/' + path + '">' + html.escape(titles[path]) + "</a></li>" for path in targets)
quiz_body += "</ul><h3>Common Mistakes</h3><p>A correct answer does not prove cross-platform binary compatibility or free-threaded safety.</p>"
quiz.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "https://aitrove.in/" + quiz_path)),
            path=quiz_path, title="Python native and platform boundaries quiz",
            summary="Twelve explained questions on C builds, the Limited API, signals, paths, subprocesses and audit hooks.",
            body=quiz_body, sort_order=8500, published_at=stamp, created_at=stamp, updated_at=stamp)
raw_questions = [
    ("What does importing a locally compiled extension establish?", "It loads on the checked interpreter and platform", "It works on every Python release", "It is safe without the GIL", "A local import is one cell of a version and platform matrix."),
    ("What must a failing C extension function return after setting an exception?", "NULL", "A borrowed reference to None", "A positive success integer", "CPython uses the error return and exception state together."),
    ("What does an abi3 suffix alone fail to certify?", "Actual stable-ABI use and cross-version tests", "That the file has a name", "That a compiler ran", "Filename and compile flags are not a replacement for symbol and runtime checks."),
    ("Can a free-threaded-capable binary run with the GIL enabled?", "Yes", "No", "Only if it has no threads", "Build capability and current runtime state are separate."),
    ("Which thread can install a Python signal handler?", "The main thread of the main interpreter", "Any worker with a Lock", "Only a daemon thread", "Worker registration raises ValueError."),
    ("Why is fsencode paired with fsdecode for a POSIX byte path?", "To preserve undecodable filename bytes", "To make network JSON valid", "To normalize currency", "A filesystem surrogate may round-trip bytes without becoming normal text."),
    ("What happens after a direct child wait times out?", "The parent still owns a running child until stopping and reaping it", "All descendants are reaped automatically", "The child's stdout is authenticated", "TimeoutExpired does not terminate the process."),
    ("Why create a new POSIX session for a job?", "To target its owned process group during teardown", "To make code run on Windows", "To skip reaping the child", "A group signal must target a verified group belonging to that job."),
    ("Should an API payment field inherit the server's locale?", "No, define a canonical wire shape", "Yes, for every request", "Only when using Decimal", "Process locale is shared state and is not an input contract."),
    ("Does Decimal decide whether a comma-formatted amount is valid input?", "No, the parser must define accepted syntax", "Yes, based on thread locale", "Only when using JSON", "Numeric representation and input grammar are separate decisions."),
    ("Can a Python-level audit hook safely sandbox hostile native code?", "No", "Yes", "Only if it observes open", "Native memory access and malicious code can bypass Python-level hooks."),
    ("What should a production audit hook avoid storing without a data policy?", "Raw sensitive event arguments", "The event name alone", "A boolean test result", "File paths and other arguments may reveal private data."),
]
quiz["data"]["questions"] = []
for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(raw_questions):
    options = [correct, wrong_a, wrong_b]
    options = options[index % 3:] + options[:index % 3]
    quiz["data"]["questions"].append({"prompt": prompt, "options": options,
                                      "answer": options.index(correct), "explanation": explanation})
rows.append(quiz)
by_path[quiz_path] = quiz
quiz_hub = by_path["python/quizzes"]
quiz_hub["data"]["modules"][-1]["lessons"].append(quiz_path)
needle = "</ul><h2>Continue learning</h2>"
assert needle in quiz_hub["body"], "quiz hub insertion point moved"
quiz_hub["body"] = quiz_hub["body"].replace(needle,
    '<li><a href="/' + quiz_path + '">' + html.escape(quiz["title"]) + "</a></li>" + needle)
parent["body"] += '<p><a href="/' + quiz_path + '">Check the native and platform quiz</a>.</p>'
for path in targets:
    by_path[path]["body"] += '<p><a href="/' + quiz_path + '">Test this contract</a>.</p>'

fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
print("Added", len(lessons), "lessons and one quiz")
