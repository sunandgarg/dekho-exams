"""Write original Python curriculum, preserving other subjects and canonical starter routes."""
import copy,datetime,html,json,pathlib,re,uuid
ROOT=pathlib.Path(__file__).resolve().parents[1];FILE=ROOT/'src/data/fixtures.json';entries=json.loads(FILE.read_text());lookup={e['path']:e for e in entries};original_lookup=copy.deepcopy(lookup);stamp=datetime.datetime.now(datetime.UTC).isoformat();added=[]
root='python/python-programming-language-tutorial'
HUBS=[(root,'Python Tutorial','python'),('python/data-types','Data Types & Collections','python-types'),('python/advanced-python','Advanced Python','python-advanced'),(root+'/interview','Interview Questions','python-interview'),('python/exercises','Exercises','python-exercises'),('python/examples','Examples','python-examples'),('python/quizzes','Quizzes','python-quizzes'),('python/projects','Projects','python-projects'),('python/cheatsheet','Cheatsheet','python-reference'),('python/dsa-in-python','DSA in Python','python-dsa')]
HUBS.extend([('python/packaging','Packaging & Tools','python-packaging'),('python/data-analysis','Data Analysis','python-data'),('python/web-applications','Web Applications','python-web'),('python/testing','Testing & Quality','python-testing')])
paths={subject:path for path,title,subject in HUBS}
def para(text):return '<p>'+re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',lambda m:'<a href="/'+m[1]+'">'+m[2]+'</a>',html.escape(text))+'</p>'
def code(text,language='python'):return '<pre><code class="language-'+language+'">'+html.escape(text.strip(),quote=False)+'</code></pre>'
def upsert(e):
 if e['path'] in lookup:entries[entries.index(lookup[e['path']])]=e
 else:entries.append(e)
 lookup[e['path']]=e

def put(slug,title,definition,explanation,boundary,source,expected,cost,mistakes,related,subject='python'):
 path='python/'+slug
 body=para(definition)+'<h2>Operation contract</h2>'+para(explanation)+'<h2>Failure and ownership boundary</h2>'+para(boundary)+'<h2>Working program</h2>'+code(source)+'<h3>Output</h3>'+code(expected,'text')+'<h2>Costs and limits</h2>'+para(cost)+'<h3>Common Mistakes</h3><ul>'+''.join('<li>'+html.escape(m)+'</li>' for m in mistakes)+'</ul><h2>Connected lessons</h2>'+para(', '.join('[['+p+'|'+p.split('/')[-1].replace('python-','').replace('-',' ').capitalize()+']]' for p in related)+'.')
 e=copy.deepcopy(lookup.get(path,lookup['java/casts']));e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),type='article',path=path,title=title,summary=definition,body=body,category='Programming Languages',subject=subject,tags=['python',slug],difficulty='Intermediate' if subject!='python' else 'Beginner',status='published',featured=False,sort_order=100+len(added),published_at=stamp,updated_at=stamp)
 e['data']={'subject_root':root,'section_path':paths[subject],'content_format':'html','kind':'tutorial','python_version':'3.11+ syntax; verified on CPython 3.14.6','python_minimum':'3.11','reading_minutes':max(4,round(len(re.sub('<[^>]+>',' ',body).split())/150)),'author_path':'authors/aitrove-editorial','download_path':'/downloads/aitrove-python-source-kit.zip','related':[{'path':p,'title':p.split('/')[-1].replace('-',' ')} for p in related],'seo_ready':True,'expected_output':expected}
 upsert(e);added.append(path)

put('setup-interpreter','Python interpreter and virtual environments: run the intended executable',
'A Python interpreter executes a program, while a virtual environment gives that interpreter an isolated package installation location.',
'The runtime probe checks the version before doing work and identifies whether its interpreter belongs to an environment. Create an environment with python3 -m venv .venv, then install through .venv/bin/python -m pip on POSIX systems or .venv\\Scripts\\python.exe -m pip on Windows. That command names the interpreter that owns the installation. An unrelated pip executable can install into another runtime without changing the application you later run.',
'Environment isolation is package isolation, not a process sandbox. The fixture uses only the standard library and performs no installation. It deliberately prints a stable version-range result rather than claiming every machine has an identical patch version. [[python/modules|Module lookup]] and [[python/receipt-cli|Command-line entrypoints]] need the same interpreter ownership rule.',
'''import sys

def supported_runtime(version):
    return version >= (3, 11)

print("runtime supported:", supported_runtime(sys.version_info[:2]))
print("old runtime supported:", supported_runtime((3, 9)))''','runtime supported: True\nold runtime supported: False',
'The version comparison has fixed-size work. Creating an environment writes interpreter support files and installing dependencies adds network/disk cost. Those operations are not timed or performed by this program.',
['Install with the interpreter that runs the application.','A virtual environment is not a security sandbox.'],['python/modules','python/receipt-cli'])

put('python-variables','Python variables: names refer to objects, assignment does not copy',
'A Python variable is a name bound to an object; assigning that object to another name does not create an independent copy.',
'The dispatch batch is a list. A second name points to that same list, so appending through the second name changes the batch. A shallow copy gives a separate outer list; adding a new entry there does not extend the original. The fixture uses immutable strings so outer-copy independence is easy to inspect. Identity and equality answer different questions.',
'Rebinding a name differs from mutating its object. Copying a nested list still shares its inner objects, and passing a list into a function does not revoke the caller’s access to it. State who owns mutation before calling the copy an immutable snapshot. [[python/python-lists|List ownership]] and [[java/pass-by-value|Java argument references]] describe comparable aliasing problems with different language rules.',
'''dispatch_batch = ["receipt-41"]
shared_batch = dispatch_batch
shared_batch.append("receipt-42")
copied_batch = dispatch_batch.copy()
copied_batch.append("receipt-43")
print(dispatch_batch)
print(copied_batch)
print(shared_batch is dispatch_batch)''',"['receipt-41', 'receipt-42']\n['receipt-41', 'receipt-42', 'receipt-43']\nTrue",
'Binding another name has bounded reference work. Copying n list entries takes O(n) time and O(n) outer storage; it does not recursively duplicate referenced objects.',
['Assignment does not copy mutable state.','A shallow copy does not isolate nested objects.'],['python/python-lists','python/tuples','java/pass-by-value'])

put('operators','Python numeric operators: division, floor division and remainder contracts',
'Python division returns a quotient, while floor division rounds its result toward negative infinity rather than toward zero.',
'The adjustment fixture compares ordinary division with floor division and remainder for a negative amount. Negative seven divided by three floors to negative three, and the remainder is two. The identity dividend equals divisor times quotient plus remainder still holds. A billing rule that expects truncation toward zero must choose that rule explicitly instead of assuming every language shares integer division behavior.',
'Zero divisors are rejected before arithmetic in an input boundary or raise ZeroDivisionError when the operation runs. Floating-point division also introduces representation limits. Monetary values need a separate unit and rounding policy; [[python/decimal-money|Decimal amounts]] avoids treating a binary float as an exact decimal wire value.',
'''adjustment = -7
package_size = 3
print(adjustment / package_size)
print(adjustment // package_size)
print(adjustment % package_size)
try:
    adjustment // 0
except ZeroDivisionError:
    print("zero divisor rejected")''','-2.3333333333333335\n-3\n2\nzero divisor rejected',
'The fixture uses small integers. Python integers can grow, so arithmetic cost and retained digits increase with operand size; constant-time arithmetic should not be claimed for unbounded input.',
['Floor division is not truncation toward zero.','Choose currency rounding separately from division syntax.'],['python/decimal-money','python/control-flow','java/operators'])

put('control-flow','Python conditions and loops: distinguish no value from an empty value',
'Python conditions test truth values, while a for loop consumes values from an iterable rather than requiring an index counter.',
'The import accepts integer amounts greater than zero. It skips None, zero and negative adjustments using explicit checks, then accumulates the accepted values. A truth check alone could collapse an absent amount and a valid domain value of zero; the program instead names the rejection policy. It also uses for-else to report that no accepted amount exceeded the review threshold.',
'Loop else runs when the loop ends without break. It does not mean the condition inside the loop was false on every iteration. Modifying the input collection while walking it can skip or invalidate work; build a separate result or define an iterator-local edit contract. [[python/python-lists|Collection changes]] and [[python/input-exercise|Rejected input]] extend this boundary.',
'''amounts = [None, 0, 125, -10, 75]
accepted = []
for amount in amounts:
    if amount is None or amount <= 0:
        continue
    accepted.append(amount)
print(sum(accepted))
for amount in accepted:
    if amount > 500:
        print("manual review")
        break
else:
    print("no review threshold reached")''','200\nno review threshold reached',
'For n inputs the filtering takes O(n) time and retains O(k) accepted values. A running total alone could use bounded storage, but this fixture keeps values for the second inspection.',
['Do not equate None with every false-valued domain input.','Loop else describes break behavior.'],['python/python-lists','python/input-exercise','python/generators'])

put('python-functions','Python functions: define units, validate input and return a result',
'A Python function defines a callable operation with its own local names and a stated argument/result contract.',
'The package-cost function accepts a nonnegative integer quantity and an integer minor-unit price, then returns an integer total. It rejects bool even though bool is an int subclass, because a boolean is not a quantity in this input format. Keyword-only unit_minor makes the price unit visible at a call site and avoids accidentally swapping two numeric fields.',
'An annotation documents intent; it does not reject bad runtime input automatically. Validation belongs at the boundary whose input is untrusted. Printing a total is also different from returning it: the caller needs a returned value to compose calculations or test it without intercepting output. [[python/function-arguments|Argument rules]] and [[python/input-exercise|Boundary parsing]] cover the next layer.',
'''def package_cost(quantity: int, *, unit_minor: int) -> int:
    if type(quantity) is not int or type(unit_minor) is not int:
        raise TypeError("integer amounts required")
    if quantity < 0 or unit_minor < 0:
        raise ValueError("negative quantity or price")
    return quantity * unit_minor

print(package_cost(3, unit_minor=125))
try:
    package_cost(True, unit_minor=125)
except TypeError:
    print("boolean quantity rejected")''','375\nboolean quantity rejected',
'Local validation is fixed work for these bounded inputs. Integer multiplication grows with operand digits; apply domain bounds before accepting arbitrarily large textual numbers.',
['Annotations are not runtime validators.','Returning a value is different from printing it.'],['python/function-arguments','python/input-exercise','java/methods'])

put('function-arguments','Python function arguments: avoid shared mutable defaults',
'Python evaluates a default argument when the function is defined, so a mutable default can be shared across later calls.',
'The receipt-tag function defaults to None and allocates a fresh list for that call. When a list is supplied, it copies it before appending so the caller retains its own collection. Those are two ownership decisions, not one syntax fix. The output proves both independent defaults and preservation of a supplied tag list.',
'Using an empty list as the default can retain earlier callers’ tags. Using tags or [] would also treat a supplied empty list as though no object were supplied, which may be wrong when preserving identity is intentional. [[python/python-variables|Aliases]] explain why default allocation and caller-owned mutation need separate rules.',
'''def receipt_tags(receipt_id, tags=None):
    owned_tags = [] if tags is None else list(tags)
    owned_tags.append(receipt_id)
    return owned_tags

shared_tags = ["reviewed"]
print(receipt_tags("R41"))
print(receipt_tags("R42"))
print(receipt_tags("R43", shared_tags))
print(shared_tags)''',"['R41']\n['R42']\n['reviewed', 'R43']\n['reviewed']",
'Copying t supplied tags takes O(t) time and storage; the default empty allocation is bounded. A shallow copy still shares mutable tag objects.',
['Do not put a mutable list in a reusable default.','Define whether the callee mutates or copies supplied state.'],['python/python-variables','python/python-functions','python/closures'])

put('exceptions','Python exceptions: translate an input error without hiding its cause',
'An exception interrupts normal execution and carries failure information to a caller that can handle that boundary.',
'The receipt parser catches only the ValueError raised by integer conversion, then raises a domain error with explicit chaining. Negative amounts fail a separate business rule. The caller distinguishes parsing rejection from successful conversion instead of catching every Exception and manufacturing a zero amount.',
'A broad catch can conceal programming errors such as a missing attribute. Finally also runs during failure, so returning from finally can suppress an exception the caller needed to see. Keep cleanup in [[python/context-managers|an owned context]] and keep error messages bounded rather than echoing an entire sensitive import record.',
'''def parse_minor_amount(text):
    try:
        amount = int(text)
    except ValueError as cause:
        raise ValueError("integer amount required") from cause
    if amount <= 0:
        raise ValueError("positive amount required")
    return amount

print(parse_minor_amount("125"))
try:
    parse_minor_amount("12x")
except ValueError as failure:
    print(str(failure))
    print(type(failure.__cause__).__name__)''','125\ninteger amount required\nValueError',
'Conversion cost grows with input length and retained integer digits. This fixture uses tiny strings; an external request must cap length before converting.',
['Catch the failure you can handle.','Do not return from finally to hide a pending error.'],['python/context-managers','python/input-exercise','java/exceptions'])

put('modules','Python modules: separate import-time definitions from program execution',
'A Python module supplies a namespace, and importing it can execute its top-level statements before the caller uses its functions.',
'The program defines a receipt-label function and guards the printing entrypoint with __name__ == "__main__". A caller importing that source can reuse the function without printing a receipt immediately. Importing a module still executes its definitions and other unguarded top-level work; the guard does not make every import side-effect free.',
'A local file named json.py or logging.py can shadow an intended module on the search path. Put reusable code in an owned package and keep environment-dependent network or database setup out of import-time code. [[python/setup-interpreter|Interpreter selection]] and [[python/receipt-cli|The CLI project]] make that execution boundary explicit.',
'''def receipt_label(identifier):
    if identifier <= 0:
        raise ValueError("positive identifier required")
    return f"receipt:{identifier}"

if __name__ == "__main__":
    print(receipt_label(41))''','receipt:41',
'The small function allocates one label string. Import cost includes module initialization and transitive imports, which this single-file fixture does not benchmark.',
['A main guard does not erase unguarded import work.','Do not shadow library module names with local files.'],['python/setup-interpreter','python/receipt-cli','java/java-modules'])

put('string-formatting','Python string formatting: format text without building SQL syntax',
'An f-string evaluates expressions and formats their values into a new string.',
'The receipt display uses integer minor units to format a major-unit and fractional part without converting through a float. The identifier and label are display text. Format alignment and decimal width are presentation rules; they do not validate a numeric range or make a displayed receipt authoritative.',
'Putting caller text in an f-string does not escape it for HTML, SQL or a shell. Each sink needs its own binding or escaping policy. The fixture prints ordinary text only. [[python/sqlite-transactions|Bound SQL parameters]] and [[python/json-validation|Structured input]] avoid treating a formatted string as a data contract.',
'''receipt_id = 41
amount_minor = 1275
major, minor = divmod(amount_minor, 100)
print(f"R{receipt_id:04d} | INR {major}.{minor:02d}")''','R0041 | INR 12.75',
'Formatting allocates a string proportional to output length. A fixed display here is bounded; very large widths or numbers supplied by callers can add allocation cost.',
['Formatting is not HTML or SQL escaping.','Keep money units explicit.'],['python/decimal-money','python/sqlite-transactions','python/json-validation'])

put('classes','Python classes: keep instance state separate from class state',
'A Python class defines a type whose instances can retain state and expose operations over that state.',
'ImportSession allocates a rejected-id list in its constructor. Two instances therefore have different lists. Adding a rejection to one session leaves the other empty. Putting that list on the class would instead provide one shared object unless the code deliberately replaced it for each instance.',
'The class does not validate who may record a rejection or persist session state. A constructor can establish a local invariant, but a shared object used by multiple threads still needs a concurrency policy. [[python/thread-pools|Worker ownership]] and [[python/dataclasses|Data containers]] use that same distinction.',
'''class ImportSession:
    def __init__(self):
        self.rejected_ids = []

    def reject(self, receipt_id):
        self.rejected_ids.append(receipt_id)

first_session = ImportSession()
second_session = ImportSession()
first_session.reject("R41")
print(first_session.rejected_ids)
print(second_session.rejected_ids)''',"['R41']\n[]",
'Each instance retains its own list, which grows with rejected IDs. The fixture imposes no retention limit; a long-running importer needs one.',
['Do not store per-request mutable lists on the class.','Object construction does not establish thread safety.'],['python/dataclasses','python/properties','python/thread-pools'])

put('inheritance','Python inheritance: override behavior without inventing shared ownership',
'Inheritance lets a subclass reuse or replace behavior supplied by its base classes.',
'The receipt exporter base defines a format contract, and the JSON exporter implements it. The import report receives an exporter instance rather than constructing a particular subclass inside the report method. That keeps selection separate from use and permits a direct test of the chosen behavior.',
'Inheritance is a type relationship, not automatic resource ownership or input validation. Deep hierarchies can make method resolution and initialization harder to inspect. Prefer an injected collaborator when the design is about replacing one operation, and read [[python/classes|Instance state]] before assuming a base class makes subclass lists independent.',
'''class ReceiptExporter:
    def render(self, identifier):
        raise NotImplementedError("export format required")

class JsonReceiptExporter(ReceiptExporter):
    def render(self, identifier):
        import json
        return json.dumps({"receipt_id": identifier}, sort_keys=True)

def export_receipt(exporter, identifier):
    return exporter.render(identifier)

print(export_receipt(JsonReceiptExporter(), 41))''','{"receipt_id": 41}',
'The dispatch retains one collaborator reference; serialization grows with the response shape. No network, file ownership or polymorphic performance comparison is claimed.',
['A type hierarchy is not a cleanup policy.','Keep implementation selection visible at construction.'],['python/classes','python/json-validation','java/interfaces'])

put('properties','Python properties: validate mutation at the public attribute boundary',
'A property intercepts attribute access so a class can enforce a rule when a value is read or assigned.',
'StockItem accepts a nonnegative integer quantity and uses the same property setter during construction and later updates. A rejected update leaves the old quantity intact because validation runs before assignment. Direct-field mutation would otherwise bypass a public method-only rule.',
'The underscore-prefixed storage is a convention, not an authorization barrier. Code with access to the object can still reach its backing attribute. The property also supplies no lock or multi-field transaction. [[python/inventory-project|Inventory transitions]] must validate the whole operation before committing a state change.',
'''class StockItem:
    def __init__(self, quantity):
        self.quantity = quantity

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if type(value) is not int or value < 0:
            raise ValueError("nonnegative integer required")
        self._quantity = value

stock = StockItem(8)
try:
    stock.quantity = -1
except ValueError:
    print("update rejected")
print(stock.quantity)''','update rejected\n8',
'The fixture performs bounded scalar validation. A setter touching external storage or several fields needs its own failure and atomicity contract.',
['Validate before replacing stored state.','An underscore is not access control.'],['python/classes','python/inventory-project','java/encapsulation'])

put('python-lists','Python lists: slicing copies the outer sequence, not nested objects',
'A Python list stores an ordered mutable sequence of object references.',
'The receipt batch contains nested lists. A slice copies the outer sequence, so appending another receipt to the copy leaves the outer original length unchanged. Editing an inner amount still changes the original because both outer lists refer to that same inner list. The program prints both states to expose the shared reference.',
'Use a copy policy that matches the value model. A full recursive copy can duplicate more state than intended, while immutable receipt records can make a shallow outer snapshot sufficient. List append also mutates in place and returns None; assigning its return value discards the reference the caller expected. [[python/tuples|Tuple contents]] and [[python/dataclasses|Frozen records]] have related ownership limits.',
'''receipt_batch = [[41, 125], [42, 75]]
snapshot = receipt_batch[:]
snapshot[0][1] = 200
snapshot.append([43, 50])
print(receipt_batch)
print(snapshot)
print(receipt_batch[0] is snapshot[0])''','[[41, 200], [42, 75]]\n[[41, 200], [42, 75], [43, 50]]\nTrue',
'Slicing n entries takes O(n) time/storage for the outer references. Front deletion shifts remaining list references; a queue should consider deque instead of repeated pop(0).',
['A slice is a shallow copy.','Do not assign the return value of append as the new list.'],['python/python-variables','python/tuples','python/graph-bfs','java/arraylist'],subject='python-types')

put('tuples','Python tuples: immutable containers can still contain mutable state',
'A tuple fixes its sequence of references, but objects reached through those references can remain mutable.',
'The import identity groups a tenant label with a mutable rejection list. Appending to the nested list changes reachable state even though the tuple itself cannot replace either slot. A separate tuple containing only the tenant string and an integer identifier is suitable as a dictionary key because those components satisfy the hashing contract.',
'Immutability and hashability are separate requirements. A tuple containing a list is unhashable, and an immutable outer shape does not make its reachable object graph read-only. Use [[python/dictionaries|Hash keys]] deliberately and choose [[python/dataclasses|record components]] according to the ownership promise.',
'''import_state = ("tenant-a", [])
import_state[1].append("R41")
print(import_state)
receipt_key = ("tenant-a", 41)
print({receipt_key: 125}[receipt_key])
try:
    hash(import_state)
except TypeError:
    print("mutable component is unhashable")''',"('tenant-a', ['R41'])\n125\nmutable component is unhashable",
'Tuple construction stores references proportional to its length. Hashing also depends on component work; it is not free merely because the outer container cannot be edited.',
['Immutable outer slots do not freeze nested values.','Check every key component’s hashing contract.'],['python/dictionaries','python/dataclasses','java/record-defensive-copy'],subject='python-types')

put('dictionaries','Python dictionaries: insertion order and duplicate-key replacement',
'A dictionary maps hashable keys to values, and replacing an existing key replaces its value rather than retaining another entry.',
'The receipt ledger inserts two identifiers, then updates the first. Its key order remains insertion order while its stored amount changes. A missing-key lookup with get returns the chosen default without inserting a new ledger entry. Those are separate facts from whether the business permits duplicate receipt identifiers.',
'If duplicate input must be rejected, test membership before assignment rather than accepting silent last-write-wins behavior. A dictionary copy shares nested values, and mutating its size during iteration can raise RuntimeError. [[python/collection-exercise|Duplicate rejection]] and [[python/json-validation|JSON member checks]] make that input policy explicit.',
'''ledger = {41: 125, 42: 75}
ledger[41] = 200
print(list(ledger))
print(ledger[41])
print(ledger.get(99, "missing"))
print(99 in ledger)''',"[41, 42]\n200\nmissing\nFalse",
'Expected hash lookup is constant work under ordinary key behavior; collisions and key hash/equality work can change that cost. Retained storage grows with distinct keys, and insertion order is not sorted key order.',
['Do not silently replace duplicates when uniqueness is required.','Insertion order is not numeric sorting.'],['python/collection-exercise','python/json-validation','python/sets','java/hashmap'],subject='python-types')

put('sets','Python sets: membership and deduplication do not preserve input order',
'A set retains distinct hashable values and supports membership and set operations.',
'The delivery fixture finds identifiers already processed and identifiers still pending. It sorts the results solely to make the displayed output deterministic; the set itself has no promised input order. Set membership is useful when deciding whether a duplicate has already been seen, but it removes multiplicity information.',
'If two identical receipt IDs indicate two separate rejected events, a set of IDs cannot tell how often the failure happened. Use a counter or retained events when frequency is part of the question. [[python/collection-exercise|Unique import validation]] and [[python/heap-top-k|Frequency ranking]] select different evidence.',
'''received_ids = {41, 42, 43}
processed_ids = {41, 44}
print(sorted(received_ids & processed_ids))
print(sorted(received_ids - processed_ids))
print(len({41, 41, 42}))''','[41]\n[42, 43]\n2',
'Expected membership has constant hash-table work for ordinary keys; retaining n distinct values takes O(n) storage. Sorting k displayed IDs adds O(k log k) time and output storage.',
['Do not promise input order from a set.','Deduplication loses frequency.'],['python/dictionaries','python/collection-exercise','python/heap-top-k'],subject='python-types')

put('strings-bytes','Python strings and bytes: reject decoding errors before parsing records',
'A str contains Unicode text, while bytes contains integer byte values that require an encoding contract before text parsing.',
'The import decodes UTF-8 with strict error handling and prints a count of code points for the decoded amount marker. A truncated byte sequence is rejected before field parsing. Character count and encoded byte count differ, so a byte-size limit must be enforced before accepting a large transmitted payload.',
'Replacement decoding can conceal a damaged record by inserting replacement characters. Code-point indexes also do not identify every user-visible grapheme cluster; combining marks can occupy more than one index. [[python/json-validation|Record validation]] follows decoding, and [[java/grapheme-boundaries|Display boundaries]] describe a separate concern.',
'''def decode_record(payload):
    if len(payload) > 4096:
        raise ValueError("record exceeds byte limit")
    return payload.decode("utf-8", errors="strict")

record = decode_record("₹125".encode("utf-8"))
print(record)
print(len(record))
try:
    decode_record(b"\\xe2\\x82")
except UnicodeDecodeError:
    print("malformed UTF-8 rejected")''','₹125\n4\nmalformed UTF-8 rejected',
'Decoding b bounded bytes takes O(b) time and text storage in the worst case. The 4096-byte cap is this record contract, not a universal HTTP body limit.',
['Specify the encoding instead of relying on the machine default.','Byte counts and visible-character counts are different.'],['python/json-validation','python/pathlib-files','java/strict-utf8'],subject='python-types')

put('decimal-money','Python Decimal money: parse decimal text and choose rounding explicitly',
'Decimal represents base-ten values with an arithmetic context rather than inheriting binary floating-point approximation.',
'The invoice fixture constructs Decimal from text and quantizes to two places with ROUND_HALF_UP. It separately rejects non-finite values. Decimal("12.345") rounds to 12.35 under that stated policy; converting a binary float first could carry its earlier approximation into the decimal object.',
'Rounding is a domain decision. A tax calculation may require another policy or round at another stage. Decimal does not supply currency identity, input length limits, positive-value rules or unlimited arithmetic precision. The local context pins working precision for the bounded example. [[python/input-exercise|Wire input]] and [[java/bigdecimal|Java decimal boundaries]] address comparable choices.',
'''from decimal import Decimal, localcontext, ROUND_HALF_UP

def invoice_amount(text):
    if len(text) > 24:
        raise ValueError("amount too long")
    with localcontext() as context:
        context.prec = 28
        amount = Decimal(text)
        if not amount.is_finite():
            raise ValueError("finite amount required")
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

print(invoice_amount("12.345"))
try:
    invoice_amount("NaN")
except ValueError:
    print("non-finite amount rejected")''','12.35\nnon-finite amount rejected',
'Decimal work depends on retained digits and precision. This fixture caps textual length and context precision; it does not define every currency’s minor-unit or maximum amount rule.',
['Construct exact decimal input from text.','Do not leave rounding policy implicit.'],['python/python-functions','python/input-exercise','java/bigdecimal'],subject='python-types')

put('generators','Python generators: lazy iteration does not make retained output free',
'A generator suspends an operation at yield and resumes it when the consumer requests another value.',
'The importer yields squared positive amounts one at a time. Turning the generator into a list materializes its results, and consuming it again produces no values because this generator instance has finished. A new call creates a new generator; keeping the same name does not reset the old one.',
'Laziness defers work and failures until iteration. A generator reading a file can keep that file open while suspended, so its lifetime needs an owner rather than an assumption that exhaustion always happens. [[python/context-managers|Cleanup]] and [[python/async-task-groups|Asynchronous ownership]] keep termination paths visible.',
'''def accepted_squares(amounts):
    for amount in amounts:
        if amount > 0:
            yield amount * amount

stream = accepted_squares([3, -1, 4])
print(list(stream))
print(list(stream))''','[9, 16]\n[]',
'The generator retains iteration state rather than every result. Materializing k results costs O(k) output storage; this fixture still receives a pre-existing input list.',
['One generator instance is not automatically reusable.','Lazy iteration is not an end-to-end memory bound.'],['python/python-lists','python/context-managers','java/streams'],subject='python-advanced')

put('decorators','Python decorators: preserve metadata and expose wrapper behavior',
'A decorator replaces or wraps a callable when its definition is evaluated.',
'The receipt decorator rejects non-positive identifiers before the wrapped lookup runs. functools.wraps preserves the original function name so diagnostics still identify lookup_receipt. The wrapper returns the result rather than discarding it or converting every failure into a success-shaped string.',
'The wrapper changes the call boundary. Stacking decorators changes which checks or side effects happen first, and a synchronous wrapper cannot correctly await an asynchronous function merely by returning its coroutine. [[python/closures|Captured state]] and [[python/async-task-groups|Async execution]] cover those separate contracts.',
'''from functools import wraps

def positive_identifier(operation):
    @wraps(operation)
    def checked(identifier):
        if type(identifier) is not int or identifier <= 0:
            raise ValueError("positive integer identifier required")
        return operation(identifier)
    return checked

@positive_identifier
def lookup_receipt(identifier):
    return f"receipt:{identifier}"

print(lookup_receipt(41))
print(lookup_receipt.__name__)
try:
    lookup_receipt(0)
except ValueError:
    print("identifier rejected")''','receipt:41\nlookup_receipt\nidentifier rejected',
'The wrapper adds one validation call and retains a reference to the wrapped callable. Expensive logging, retry or caching wrappers add their own costs; decoration does not reduce underlying work.',
['Return the wrapped result and preserve metadata deliberately.','Do not wrap async work with an unexamined synchronous policy.'],['python/closures','python/python-functions','python/async-task-groups'],subject='python-advanced')

put('closures','Python closures: capture loop values at the intended time',
'A closure retains access to names from an enclosing scope, so later calls can observe the value those names hold at call time.',
'The incorrect review callbacks all refer to the same loop name after the loop finishes, yielding the final identifier three times. The corrected callbacks use a default argument to bind each current identifier while constructing the callable. The two lists of results expose the difference without relying on timing or threads.',
'Capturing an object reference does not copy the object. A callback can still observe later mutations even when its default stores the intended reference. Use [[python/function-arguments|Default ownership]] and [[python/python-variables|Aliasing]] before assuming value capture provides an immutable snapshot.',
'''late_callbacks = []
fixed_callbacks = []
for receipt_id in [41, 42, 43]:
    late_callbacks.append(lambda: receipt_id)
    fixed_callbacks.append(lambda captured=receipt_id: captured)
print([callback() for callback in late_callbacks])
print([callback() for callback in fixed_callbacks])''','[43, 43, 43]\n[41, 42, 43]',
'Building n callbacks takes O(n) retained callables. Captured large objects can remain alive while callbacks retain their references, even after the outer operation finishes.',
['Loop closures can observe the final loop value.','Binding a reference is not copying its object.'],['python/function-arguments','python/decorators','java/lambdas'],subject='python-advanced')

put('context-managers','Python context managers: clean up on success and failure',
'A context manager owns entry and exit behavior around a with block, including cleanup during exceptions.',
'The staging context records entry, yields its temporary list, and clears that list in finally. The caller raises an import error, catches it outside the context, then checks that cleanup happened and retained state is empty. The original error is not swallowed to make the import appear successful.',
'The fixture owns only a process-local list. File, database and network contexts have their own close and transaction semantics; closing a resource is not the same as rolling back completed external work. [[python/sqlite-transactions|Transaction boundaries]] and [[python/pathlib-files|File lifetimes]] need those rules stated separately.',
'''from contextlib import contextmanager

@contextmanager
def staging_buffer(events):
    staged = []
    events.append("opened")
    try:
        yield staged
    finally:
        staged.clear()
        events.append("closed")

events = []
try:
    with staging_buffer(events) as retained:
        retained.append("R41")
        raise ValueError("import failed")
except ValueError:
    print("failure preserved")
print(events)
print(retained)''',"failure preserved\n['opened', 'closed']\n[]",
'The list retains k staged values until exit and cleanup releases its references. The context cannot undo external side effects that occurred before failure.',
['Do not suppress an error unless that is the public contract.','Cleanup and transactional rollback are different operations.'],['python/exceptions','python/sqlite-transactions','java/try-with-resources'],subject='python-advanced')

put('dataclasses','Python dataclasses: frozen fields require an immutable value model',
'A dataclass generates methods such as initialization and equality from declared fields; frozen fields restrict normal assignment to those fields.',
'The receipt record uses a tenant string, integer identifier and tuple of integer amounts. That component choice avoids the shallow-freeze problem of a mutable list field. The fixture shows value equality, tuple aggregation and rejection of ordinary reassignment to its identifier.',
'Frozen is not a complete security barrier, and a frozen dataclass containing a list would still expose list mutation. Annotations also do not validate that arbitrary caller values have the declared runtime types. Construct validated records at [[python/json-validation|the input boundary]] rather than treating generated initialization as a schema validator.',
'''from dataclasses import dataclass, FrozenInstanceError

@dataclass(frozen=True)
class ReceiptBatch:
    tenant: str
    identifier: int
    amounts: tuple[int, ...]

batch = ReceiptBatch("tenant-a", 41, (125, 75))
print(batch == ReceiptBatch("tenant-a", 41, (125, 75)))
print(sum(batch.amounts))
try:
    batch.identifier = 42
except FrozenInstanceError:
    print("field assignment rejected")''','True\n200\nfield assignment rejected',
'Generated equality compares components and can cost O(n) for an n-element tuple. Freezing references does not recursively copy input; this fixture uses immutable components already.',
['Frozen fields do not freeze a nested list.','Annotations do not enforce a runtime schema.'],['python/tuples','python/json-validation','java/records'],subject='python-advanced')

put('async-task-groups','Python asyncio TaskGroup: cancel sibling work and retain failure evidence',
'A TaskGroup owns asynchronous child tasks and waits for them to finish or be cancelled when its scope exits.',
'The receipt import starts one waiting worker and one worker that fails after yielding control. The failure cancels the waiting sibling, whose finally block records cleanup. The caller catches the ValueError part of the resulting exception group and prints stable evidence rather than relying on task completion order.',
'Cancellation is cooperative: code must reach an await boundary and must not swallow cancellation merely to continue work. Cancelling a coroutine does not undo a database commit or a payment already performed. This fixture has no network I/O and uses a finally marker, not a claim about closing a production client. [[python/context-managers|Resource ownership]] stays separate from scheduling.',
'''import asyncio

async def import_batch():
    events = []
    started = asyncio.Event()
    async def waiting_import():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            events.append("sibling cleaned")
    async def failed_import():
        await started.wait()
        raise ValueError("invalid receipt")
    try:
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(waiting_import())
            tasks.create_task(failed_import())
    except* ValueError:
        events.append("failure observed")
    print(events)

if __name__ == "__main__":
    asyncio.run(import_batch())''',"['sibling cleaned', 'failure observed']",
'The group retains two tasks and their exception state. Creating one task per unbounded input still grows memory with input count; TaskGroup itself is not an admission limit.',
['Do not hide cancellation to keep failed sibling work running.','Task ownership does not create a task-count limit.'],['python/context-managers','python/thread-pools','java/cancellation'],subject='python-advanced')

put('thread-pools','Python thread pools: collect results and observe worker failures',
'A ThreadPoolExecutor runs submitted callables in worker threads and returns futures that carry either results or failures.',
'The import submits two valid amount checks and one rejected amount to a two-worker pool. It calls result on every future, so the worker exception is observed rather than left in an ignored future. It sorts accepted results for deterministic display, keeping submission order separate from possible completion order.',
'Two workers bound concurrent execution, not the number of queued submissions. Submitting an entire huge import can still retain a future and input for each record. Threads are also not an automatic CPU-parallel speedup across Python builds; the fixture makes no GIL or throughput claim. [[python/async-task-groups|Async tasks]] solve a different scheduling problem.',
'''from concurrent.futures import ThreadPoolExecutor

def checked_amount(amount):
    if amount <= 0:
        raise ValueError("positive amount required")
    return amount * 2

accepted = []
rejected = 0
with ThreadPoolExecutor(max_workers=2) as workers:
    futures = [workers.submit(checked_amount, amount) for amount in [125, 75, -1]]
    for future in futures:
        try:
            accepted.append(future.result())
        except ValueError:
            rejected += 1
print(sorted(accepted))
print("rejected:", rejected)''','[150, 250]\nrejected: 1',
'This fixture retains three futures. A submit-all pattern retains O(n) futures for n inputs even with a small worker count; use bounded admission for large imports.',
['Read every future result or define an explicit error sink.','Worker count is not a queue-size bound.'],['python/async-task-groups','python/exceptions','java/executor-rejection'],subject='python-advanced')

put('json-validation','Python JSON validation: reject duplicate members and non-integer amounts',
'JSON decoding turns text into Python values; validating those values against an application schema is a separate step.',
'The receipt decoder uses an object-pairs hook to reject duplicate member names before a dictionary can overwrite them. It accepts exactly the amount_minor member and requires a positive integer, excluding bool. The program rejects both a boolean amount and two repeated amount members instead of letting each input become a plausible receipt.',
'JSON input can consume memory before application validation runs, so cap incoming bytes or text before decoding. This fixture caps text length and accepts a flat one-field shape; it is not a general nested-document resource sandbox. [[python/strings-bytes|UTF-8 decoding]] happens earlier, while [[python/dataclasses|Validated records]] can provide a later internal representation.',
'''import json

def unique_members(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise ValueError("duplicate member")
        values[key] = value
    return values

def receipt_amount(text):
    if len(text) > 1024:
        raise ValueError("document too long")
    values = json.loads(text, object_pairs_hook=unique_members)
    if not isinstance(values, dict) or set(values) != {"amount_minor"}:
        raise ValueError("receipt shape required")
    amount = values["amount_minor"]
    if type(amount) is not int or amount <= 0:
        raise ValueError("positive integer amount required")
    return amount

print(receipt_amount('{"amount_minor":125}'))
for payload in ['{"amount_minor":true}', '{"amount_minor":1,"amount_minor":2}']:
    try:
        receipt_amount(payload)
    except ValueError:
        print("document rejected")''','125\ndocument rejected\ndocument rejected',
'Decoding n bounded characters has input-proportional work and retains the decoded graph. The length cap does not define a general depth limit; deployments must choose broader limits for broader schemas.',
['Parsing is not schema validation.','Reject duplicate members before overwriting loses their evidence.'],['python/dictionaries','python/strings-bytes','python/dataclasses'],subject='python-examples')

put('csv-import','Python CSV imports: parse quoted fields before validating rows',
'A CSV reader interprets delimiters and quoting so a comma inside a quoted field remains part of that field.',
'The import reads a two-column header and one row whose note contains a comma. DictReader produces one amount and one note, then the application validates the amount as a positive integer. Splitting each line at commas would produce the wrong number of fields for this record.',
'The program uses an in-memory text stream, not an uploaded file. A deployed import needs byte, row, field and retained-result bounds; accepting CSV does not provide them automatically. It also needs a duplicate-header and unexpected-column policy. [[python/input-exercise|Field contracts]] and [[python/pathlib-files|Text file ownership]] follow parsing.',
'''import csv
import io

source = io.StringIO('amount_minor,note\\n125,"review, accepted"\\n', newline="")
reader = csv.DictReader(source)
if reader.fieldnames != ["amount_minor", "note"]:
    raise ValueError("expected receipt header")
for row in reader:
    if set(row) != {"amount_minor", "note"} or None in row.values():
        raise ValueError("complete row required")
    amount = int(row["amount_minor"])
    if amount <= 0:
        raise ValueError("positive amount required")
    print(amount)
    print(row["note"])''','125\nreview, accepted',
'This one-row fixture retains the entire short text. Streaming rows can avoid retaining all parsed rows, but a very large individual field still needs a limit.',
['Do not split CSV at commas manually.','Check header and row shape before using fields.'],['python/input-exercise','python/pathlib-files','python/json-validation'],subject='python-examples')

put('pathlib-files','Python pathlib files: specify encoding and close the resource owner',
'Path represents a filesystem path and provides file operations; it does not itself establish that a caller is authorized to access that location.',
'The fixture creates a temporary directory, writes a UTF-8 receipt marker, then reads it back under the same encoding. The temporary-directory owner removes its files after the block. The test displays the content and a fixed relative filename, avoiding an unstable machine-specific path in the expected output.',
'A path joined beneath a directory can still require validation if a caller supplies absolute paths, parent components or symlinks. This fixture accepts no caller path and claims no race-safe extraction sandbox. [[python/context-managers|Ownership]] and [[python/strings-bytes|Encoding]] supply different parts of the file contract.',
'''from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as directory:
    record_path = Path(directory) / "receipt.txt"
    record_path.write_text("amount=125", encoding="utf-8")
    with record_path.open(encoding="utf-8") as handle:
        print(handle.read())
    print(record_path.name)''','amount=125\nreceipt.txt',
'Read/write work grows with file bytes. Reading the entire file retains its text; large imports need bounded streaming and an explicit publication/crash-recovery policy.',
['Use the intended text encoding.','Joining paths is not authorization or a symlink-race defense.'],['python/context-managers','python/strings-bytes','java/zip-path-validation'],subject='python-examples')

put('sqlite-transactions','Python sqlite3 transactions: bind values and roll back failed batches',
'A SQLite transaction groups changes so a failure can roll back the group rather than leaving a partially inserted batch.',
'The fixture creates an in-memory receipt table with a positive-amount check. Two bound inserts run in one transaction: the second violates the check, so the first is rolled back too. A later valid insert commits and the final query returns that one row. SQL values use placeholders rather than string formatting.',
'The connection context controls commit/rollback, not connection closure; the fixture closes it in finally. Its in-memory database also disappears after closure. Target-database isolation, concurrent writers, durable files and migration recovery require their own tests. [[python/inventory-project|Atomic state changes]] and [[java/jdbc-transactions|JDBC transaction boundaries]] address related failure rules.',
'''import sqlite3

connection = sqlite3.connect(":memory:")
try:
    connection.execute("CREATE TABLE receipt (id INTEGER PRIMARY KEY, amount INTEGER CHECK(amount > 0))")
    try:
        with connection:
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (41, 125))
            connection.execute("INSERT INTO receipt VALUES (?, ?)", (42, -1))
    except sqlite3.IntegrityError:
        print("batch rolled back")
    print(connection.execute("SELECT count(*) FROM receipt").fetchone()[0])
    with connection:
        connection.execute("INSERT INTO receipt VALUES (?, ?)", (43, 75))
    print(connection.execute("SELECT id, amount FROM receipt ORDER BY id").fetchall())
finally:
    connection.close()''','batch rolled back\n0\n[(43, 75)]',
'The test inserts three tiny candidate rows and queries a count and one result. Database plan, disk durability, locking schedules and pooled connection behavior are outside this in-memory fixture.',
['Bind values instead of building SQL with f-strings.','The connection transaction context does not close the connection.'],['python/string-formatting','python/context-managers','java/jdbc-transactions'],subject='python-examples')

put('logging-context','Python logging: include bounded context without printing sensitive payloads',
'A logger emits a record through configured handlers, and a formatter chooses which fields appear in its output.',
'The receipt audit logger has one local handler and disables propagation to avoid duplicate delivery through a parent handler in this fixture. The format includes level and logger name, while parameter substitution records only a bounded identifier and outcome. It never prints a full receipt payload, authorization header or email address.',
'Configuring a logger repeatedly can attach repeated handlers and multiply output. Formatting arguments later also does not make evaluation of an expensive argument expression lazy. Use an enabled-level guard for expensive diagnostic work and define retention, access and redaction separately from this handler setup. [[python/exceptions|Failure translation]] provides an error contract for callers rather than relying on logs as a response.',
'''import io
import logging

captured = io.StringIO()
logger = logging.getLogger("aitrove.receipts.fixture")
logger.handlers.clear()
logger.propagate = False
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(captured)
handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
logger.addHandler(handler)
try:
    logger.info("receipt=%s outcome=%s", 41, "accepted")
    print(captured.getvalue().strip())
finally:
    logger.removeHandler(handler)
    handler.close()''','INFO aitrove.receipts.fixture receipt=41 outcome=accepted',
'This fixture retains one short log line in memory. Handler I/O, queue growth and retention cost are not bounded by the logger name or level setting.',
['Do not attach a new handler for every request.','Diagnostic context should not contain credentials or entire payloads.'],['python/exceptions','python/thread-pools','spring/metric-cardinality'],subject='python-examples')

put('python-interview-questions','Python interview traces: explain aliasing, defaults and identity',
'A Python interview trace tests the operation and ownership rules that determine the result, not memorization of a printed string.',
'The trace copies an outer list, checks the shared inner object, and mutates that object. It then uses a None-default function twice to prove that the two returned tag lists have distinct identity. A useful answer states when objects are allocated and which references still point to them before giving the output.',
'Identity is not equality. Two different lists can compare equal, while one shared list can change beneath several names. Correcting a mutable default alone also does not copy a list supplied by a caller. Read [[python/function-arguments|argument ownership]], [[python/python-lists|outer copies]] and [[python/closures|late binding]] before translating these traces to concurrent work.',
'''nested = [[125]]
outer_copy = nested.copy()
print(nested is outer_copy)
print(nested[0] is outer_copy[0])
outer_copy[0].append(75)
print(nested)

def new_tags(tags=None):
    return [] if tags is None else tags

print(new_tags() is new_tags())''','False\nTrue\n[[125, 75]]\nFalse',
'An outer copy is O(n) reference work; identity tests compare object identity without traversing all elements. Equality of containers may traverse their contents.',
['Explain ownership before naming the output.','Do not use is as general value equality.'],['python/python-lists','python/function-arguments','python/closures'],subject='python-interview')

put('collection-exercise','Python collection exercise: reject repeated receipt IDs before committing state',
'A duplicate-rejection exercise checks that one receipt identifier cannot silently replace another record during a batch conversion.',
'The converter builds a private dictionary and rejects the first repeated identifier. It returns that dictionary only after all rows pass. The caller’s row list remains available for inspection and no shared ledger is mutated during a failed conversion. An invalid final row therefore cannot publish a partial result.',
'The exercise validates positive integer identifiers and amounts, excluding bool. It checks valid rows and a repeated ID; larger programs need row-count and payload-size bounds too. [[python/dictionaries|Replacement behavior]] explains what would happen without the explicit duplicate check, and [[python/inventory-project|Staged mutation]] extends the same pattern.',
'''def validated_ledger(rows):
    if len(rows) > 1000:
        raise ValueError("batch too large")
    staged = {}
    for identifier, amount in rows:
        if type(identifier) is not int or type(amount) is not int or identifier <= 0 or amount <= 0:
            raise ValueError("positive integer fields required")
        if identifier in staged:
            raise ValueError("repeated receipt")
        staged[identifier] = amount
    return staged

print(validated_ledger([(41, 125), (42, 75)]))
try:
    validated_ledger([(41, 125), (41, 75)])
except ValueError:
    print("repeated receipt rejected")''','{41: 125, 42: 75}\nrepeated receipt rejected',
'Expected dictionary work is O(n) with O(n) staged storage for bounded ordinary integer keys. Returning a complete batch is intentional; a streaming sink needs a separate rollback/publication design.',
['Do not publish a partially validated batch.','A dictionary overwrite is not duplicate rejection.'],['python/dictionaries','python/input-exercise','python/inventory-project'],subject='python-exercises')

put('input-exercise','Python input exercise: accept an explicit integer grammar',
'An input grammar states which textual forms a field accepts before numeric conversion or domain validation runs.',
'The receipt wire field accepts one to eight ASCII decimal digits and a positive result. It rejects a leading plus sign, surrounding whitespace, zero and non-ASCII decimal glyphs. Python int accepts some forms that this wire format intentionally excludes; relying on conversion alone would implement a broader grammar than the API promises.',
'The parser has a small input cap and separates textual shape from numeric positivity. Changing that grammar is an API change, not merely a display improvement. [[python/python-functions|Runtime types]] and [[python/decimal-money|Decimal policies]] handle different input models; do not mix their accepted representations accidentally.',
'''def wire_amount(text):
    if not 1 <= len(text) <= 8 or any(character not in "0123456789" for character in text):
        raise ValueError("ASCII digit field required")
    amount = int(text)
    if amount == 0:
        raise ValueError("positive amount required")
    return amount

print(wire_amount("125"))
for text in ["+125", " 125", "0", "１２５"]:
    try:
        wire_amount(text)
    except ValueError:
        print("field rejected")''','125\nfield rejected\nfield rejected\nfield rejected\nfield rejected',
'The declared eight-character cap bounds parsing work and integer size. This grammar does not identify a currency, user or authorized receipt operation.',
['Conversion accepts more than every narrow wire grammar.','Validate textual shape and domain range separately.'],['python/python-functions','python/decimal-money','python/json-validation'],subject='python-exercises')

put('receipt-cli','Python receipt CLI project: parse options and report failed input',
'A command-line interface maps argument text to a program operation and communicates failure through errors and exit behavior.',
'The parser defines required quantity and unit-minor options with a custom positive-integer type. It parses an explicit local argument list for repeatable testing instead of depending on the test runner’s arguments. Valid input produces an integer total; invalid quantity produces ArgumentError in this teaching parser configuration.',
'The parser uses exit_on_error=False so the local test can observe the conversion error without terminating the process. A deployed CLI must define which failures exit, how stderr is used and whether any output file was already written. [[python/modules|Main guards]] and [[python/pathlib-files|File publication]] remain part of that application boundary.',
'''import argparse

def positive_integer(text):
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return value

def parser():
    options = argparse.ArgumentParser(exit_on_error=False)
    options.add_argument("--quantity", type=positive_integer, required=True)
    options.add_argument("--unit-minor", type=positive_integer, required=True)
    return options

if __name__ == "__main__":
    options = parser().parse_args(["--quantity", "3", "--unit-minor", "125"])
    print(options.quantity * options.unit_minor)
    try:
        parser().parse_args(["--quantity", "-1", "--unit-minor", "125"])
    except argparse.ArgumentError:
        print("option rejected")''','375\noption rejected',
'This fixture parses four small tokens and performs one multiplication. It is a checked CLI boundary, not an installed package or a durable billing application; input digit limits remain a deployment choice.',
['Do not parse a test runner’s arguments as application input.','Define failure output and exit status deliberately.'],['python/modules','python/python-functions','python/input-exercise'],subject='python-projects')

put('inventory-project','Python inventory project: validate a batch before replacing stored state',
'A staged inventory update computes a candidate state and commits it only after every transition satisfies the stock invariant.',
'The ledger copies its current stock, applies signed changes to that candidate and rejects any negative result. A failed batch leaves the original state intact; a later valid batch commits both item changes. The snapshot method returns another outer dictionary copy so ordinary caller changes do not edit the ledger directly.',
'This model uses scalar integer values and runs in one thread. It provides process-local all-or-nothing mutation, not durable transactions, authorization or concurrent compare-and-set. A sequence that dips below zero and later recovers is still rejected because each transition must be valid. [[python/sqlite-transactions|Database rollback]] is a separate persistence implementation.',
'''class InventoryLedger:
    def __init__(self):
        self._stock = {"paper": 8, "ink": 4}

    def apply(self, changes):
        if len(changes) > 100:
            raise ValueError("batch too large")
        candidate = self._stock.copy()
        for item, change in changes:
            if item not in candidate or type(change) is not int:
                raise ValueError("known item and integer change required")
            next_quantity = candidate[item] + change
            if next_quantity < 0:
                raise ValueError("negative stock")
            candidate[item] = next_quantity
        self._stock = candidate

    def snapshot(self):
        return self._stock.copy()

ledger = InventoryLedger()
try:
    ledger.apply([("paper", -2), ("ink", -9)])
except ValueError:
    print("batch rejected")
print(ledger.snapshot())
ledger.apply([("paper", -2), ("ink", 1)])
print(ledger.snapshot())''',"batch rejected\n{'paper': 8, 'ink': 4}\n{'paper': 6, 'ink': 5}",
'Copying s stock keys and checking n changes takes expected O(s+n) time and O(s) candidate storage. The fixture starts with two keys; unrestricted state size, concurrency and crash recovery are not addressed.',
['Commit the candidate only after every transition passes.','A local dictionary is not durable or thread-safe storage.'],['python/dictionaries','python/properties','python/sqlite-transactions','java/multi-index-invariants'],subject='python-projects')

put('syntax-reference','Python syntax reference: inspect shape, unpacking and mutation rules',
'A syntax reference supplies small operation contracts that can be checked before composing a larger program.',
'The receipt batch uses enumerate for an index and value, zip with strict=True to reject mismatched sequence lengths, and a comprehension to build a new result list. The strict zip exception prevents a missing price from silently truncating a batch. The input lists are not modified by the comprehension.',
'Concise syntax does not replace input validation. Unpacking a receipt tuple assumes its field count, and a comprehension can allocate all results even when written on one line. [[python/python-lists|Copying]], [[python/python-functions|Argument validation]] and [[python/generators|Lazy results]] determine the surrounding contract.',
'''receipt_ids = [41, 42]
amounts = [125, 75]
print([f"{position}:{identifier}" for position, identifier in enumerate(receipt_ids, start=1)])
print(sum(amount for identifier, amount in zip(receipt_ids, amounts, strict=True)))
try:
    list(zip(receipt_ids, [125], strict=True))
except ValueError:
    print("length mismatch rejected")''',"['1:41', '2:42']\n200\nlength mismatch rejected",
'Enumeration and pairing are linear in consumed values. Materializing n comprehension results uses O(n) result storage; strict zip does not bound input length.',
['Use strict pairing when unequal lengths are invalid.','A one-line comprehension can still retain a large result.'],['python/python-functions','python/python-lists','python/generators'],subject='python-reference')

put('binary-search','Python binary search: use a half-open interval and require sorted input',
'Binary search narrows a sorted sequence to locate a boundary in logarithmically many comparisons.',
'The search returns the first index whose receipt timestamp is at least the requested value. Its interval is half-open: left is included and right is excluded. Equal values move the right bound, so duplicates return their first insertion boundary rather than an arbitrary equal index. A request after every timestamp returns the sequence length.',
'The function assumes ascending input. Sorting inside each query would add different work and alter caller ownership; rejecting or documenting unsorted input is a boundary decision. The fixture caps input length but does not spend a full linear scan verifying order on each call. [[python/python-lists|Sequence ownership]] and [[java/binary-search|The Java boundary search]] share the same invariant.',
'''def lower_bound(timestamps, target):
    if len(timestamps) > 10000:
        raise ValueError("sequence too large")
    left, right = 0, len(timestamps)
    while left < right:
        middle = (left + right) // 2
        if timestamps[middle] < target:
            left = middle + 1
        else:
            right = middle
    return left

print(lower_bound([10, 20, 20, 30], 20))
print(lower_bound([10, 20, 20, 30], 40))
print(lower_bound([], 20))''','1\n4\n0',
'For n already sorted bounded integer values, the search uses O(log n) comparisons and O(1) working slots. Sorting, validating order and arbitrary-size integer costs are outside that comparison count.',
['Keep the interval convention consistent.','The logarithmic search assumes sorted input.'],['python/python-lists','python/syntax-reference','java/binary-search'],subject='python-dsa')

put('graph-bfs','Python graph BFS: mark a vertex when it enters the queue',
'Breadth-first search visits an unweighted graph in layers and can compute the minimum number of edges from a start vertex.',
'The route fixture uses deque for endpoint queue operations and records a vertex’s distance when it is enqueued. Two routes may reach the same neighbor, but only the first enqueues it. Unreachable vertices keep distance negative one. The graph uses explicit numbered vertices rather than assuming labels correspond to list positions accidentally.',
'The contract validates vertex count and neighbor indices, then searches one connected reachability region. It is not a weighted shortest-path algorithm; edge weights require a different rule. [[python/sets|Membership]] and [[java/graph-bfs|Java BFS]] provide related state choices, while the graph input remains a prebuilt adjacency list.',
'''from collections import deque

def route_distances(graph, start):
    if type(start) is not int or not 1 <= len(graph) <= 1000 or not 0 <= start < len(graph):
        raise ValueError("graph bounds")
    if sum(map(len, graph)) > 10000 or any(type(vertex) is not int or not 0 <= vertex < len(graph) for row in graph for vertex in row):
        raise ValueError("edge bounds")
    distance = [-1] * len(graph)
    distance[start] = 0
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in graph[current]:
            if distance[neighbor] == -1:
                distance[neighbor] = distance[current] + 1
                pending.append(neighbor)
    return distance

print(route_distances([[1, 2], [3], [3], [], []], 0))''','[0, 1, 1, 2, -1]',
'Validation and traversal take O(v+e) time for v vertices and e adjacency entries. Distances and the queue retain O(v) additional state, excluding the supplied graph.',
['Mark a vertex on enqueue, not after repeated queue insertion.','BFS edge count is not a weighted route cost.'],['python/sets','python/python-lists','java/graph-bfs'],subject='python-dsa')

put('heap-top-k','Python heapq top-k: define ties before ranking frequencies',
'A heap-based top-k selection keeps the strongest k candidates while examining the supplied values.',
'The receipt-category fixture counts events, then asks nlargest for the two most frequent categories. The ranking key includes the category name as a tie-breaker, choosing reverse alphabetical order when counts match. Defining that policy prevents a test from accidentally relying on input dictionary order for equal frequencies.',
'Counting retains every distinct category before top-k selection, so a small k does not bound the entire pipeline’s memory. User-controlled category names also need length/count limits in a service. [[python/sets|Frequency loss]] explains why a set cannot replace Counter, and [[java/heap-top-k|Heap selection]] covers the related Java operation.',
'''from collections import Counter
from heapq import nlargest

categories = ["accepted", "rejected", "accepted", "queued", "rejected", "accepted"]
counts = Counter(categories)
ranked = nlargest(2, counts.items(), key=lambda item: (item[1], item[0]))
print(ranked)''',"[('accepted', 3), ('rejected', 2)]",
'Counting n events uses O(n) expected hash work and O(u) retained counts for u distinct categories. Selection commonly uses O(u log k) comparison work when k is small; sorting fallback/large-k behavior and string comparisons affect the exact implementation cost.',
['Declare a tie-breaker instead of relying on incidental order.','Small k does not limit the frequency map.'],['python/dictionaries','python/sets','java/heap-top-k'],subject='python-dsa')

put('bracket-stack','Python bracket stack: reject mismatches at the first invalid close',
'A bracket validator uses a stack of expected closing tokens to check properly nested bracket sequences.',
'The import expression parser pushes the matching closer for every opener. A closer must match the top expectation; a mismatched closer or a leftover opener makes the expression invalid. The fixture accepts only bracket characters and caps input length, so ordinary text cannot be silently ignored as though it were parsed.',
'This is bracket validation, not a Python parser. Quoted strings, comments and expression semantics require a grammar that knows whether a bracket is actually syntax. [[python/strings-bytes|Text representation]] defines an earlier layer, while [[java/stack-brackets|A Java stack]] checks the same nesting invariant.',
'''def balanced_brackets(text):
    if len(text) > 4096:
        raise ValueError("expression too long")
    closing = {"(": ")", "[": "]", "{": "}"}
    expected = []
    for token in text:
        if token in closing:
            expected.append(closing[token])
        elif token in ")]}":
            if not expected or expected.pop() != token:
                return False
        else:
            raise ValueError("brackets only")
    return not expected

print(balanced_brackets("{[()]}"))
print(balanced_brackets("([)]"))
print(balanced_brackets("(("))''','True\nFalse\nFalse',
'For n bracket tokens the scan is O(n) time and worst-case O(n) stack storage. Early mismatch can stop before consuming every token.',
['Validate the top expectation rather than only counting tokens.','A bracket checker is not a source-language parser.'],['python/python-lists','python/strings-bytes','java/stack-brackets'],subject='python-dsa')

put('memoization','Python memoization: cache bounded states without hiding recursion depth',
'Memoization stores a function result for an argument state so later calls can reuse that result.',
'The stock-packing recurrence computes the minimum number of package sizes needed for a target amount. A call-local cached function prevents repeated evaluation of the same remaining amount. An impossible target returns negative one rather than a plausible package count; the target and package count are bounded before recursion starts.',
'The cache lives inside one request to avoid retaining every historical target in a global cache. Recursion still has depth proportional to the target in the worst case; caching repeated states does not remove stack depth. The fixture caps target at one hundred and rejects non-positive package sizes. [[java/coin-change|Iterative coin change]] offers another evaluation order.',
'''from functools import lru_cache

def minimum_packages(sizes, target):
    if type(target) is not int or not 0 <= target <= 100 or not 1 <= len(sizes) <= 20:
        raise ValueError("packing bounds")
    if any(type(size) is not int or size <= 0 for size in sizes):
        raise ValueError("positive package sizes required")
    unreachable = target + 1
    @lru_cache(maxsize=None)
    def solve(remaining):
        if remaining == 0:
            return 0
        return min((1 + solve(remaining - size) for size in sizes if size <= remaining), default=unreachable)
    answer = solve(target)
    return -1 if answer >= unreachable else answer

print(minimum_packages((3, 5), 11))
print(minimum_packages((4, 6), 7))''','3\n-1',
'For t bounded target states and c package sizes, recurrence work is O(t*c) and cache/stack storage is O(t), ignoring integer digit costs. The declared depth cap is part of this recursive implementation.',
['Caching does not remove recursion depth.','Do not let a global unbounded cache retain every historical request.'],['python/closures','python/python-functions','java/coin-change'],subject='python-dsa')

BANKS={
'python-basics':('Python foundations quiz',[
('Assigning a list to a second name creates what?', ['A second reference to the same list','A recursive copy','A new immutable sequence'],0,'Assignment binds another name; mutation can be seen through both references.'),
('What does the quantity fixture reject despite bool being an int subclass?', ['Boolean quantities','Positive integer quantities','Zero-sized strings only'],0,'The contract requires the exact int type rather than an isinstance check that also accepts bool.'),
('What is -7 // 3?', ['-2','-3','2'],1,'Floor division rounds toward negative infinity.'),
('A for-else block runs its else when what happens?', ['The loop ends without break','Its first value is false','It has at least one iteration'],0,'Normal exhaustion, including an empty iterable, reaches else; break skips it.'),
('Does a type annotation reject a string supplied as an int argument automatically?', ['Yes','No','Only with a keyword argument'],1,'Annotations are metadata; runtime validation requires explicit code or a validator.'),
('Why does the tag function use None as its default?', ['It must return None','To create per-call mutable storage','To disable every argument'],1,'A mutable default would be allocated at function definition and shared.'),
('What does a main guard control?', ['Whether all imports are safe','Whether guarded statements run as the entrypoint','The interpreter package location'],1,'Unguarded module statements can still execute during import.'),
('What does raise ... from cause retain?', ['The failure relationship','Every input byte','A successful result'],0,'Explicit chaining preserves the original cause while translating the boundary.'),
('Where should per-session mutable rejection lists be allocated?', ['On the class once','In each instance initializer','In a global module variable'],1,'Instance allocation avoids sharing one class-owned mutable list across sessions.'),
('A rejected property update validates before assignment. What remains?', ['The old valid state','The rejected value','No attribute'],0,'The setter changes storage only after its check passes.'),
('Does formatting text with an f-string bind an SQL parameter?', ['Yes','No','Only if it is an integer'],1,'Formatting is not the database parameter-binding API.'),
('What does a virtual environment isolate?', ['All filesystem access','Its interpreter package installation location','Every network operation'],1,'Package isolation is not a process security sandbox.')]),
'python-collections':('Python collection ownership quiz',[
('A list slice copies what?', ['Outer references','Every nested object','Only numeric values'],0,'The outer list is separate but its nested references remain shared.'),
('Can a tuple containing a list be used as a dictionary key?', ['Yes, all tuples are hashable','No, that component is unhashable','Only when the list is empty'],1,'Hashing requires suitable components; a mutable list is unhashable.'),
('Replacing an existing dictionary value changes what?', ['The value, while keeping that key position','The key to the end automatically','The entire map into a set'],0,'Updating an existing key is distinct from inserting another key.'),
('Does dictionary get with a default insert the missing key?', ['Yes','No','Only for strings'],1,'get returns the fallback without creating an entry.'),
('What does deduplicating a list through a set lose?', ['All membership information','Multiplicity and promised input order','Hashable values only'],1,'A set retains distinct values rather than an ordered event history.'),
('How should deterministic set output be produced here?', ['Rely on hash order','Sort the displayed result','Change the process clock'],1,'Sorting establishes an explicit presentation order.'),
('What does list.append return?', ['The expanded list','None','The appended index'],1,'append mutates the existing list rather than returning a new list.'),
('Does a frozen dataclass freeze an inner list?', ['Yes','No','Only after equality is tested'],1,'Normal field assignment restrictions do not recursively freeze reachable objects.'),
('What happens to a completed generator when consumed again?', ['It starts over','It yields no remaining values','It copies all prior results'],1,'Create another generator to start another independent iteration.'),
('What is required before claiming a top-k pipeline uses O(k) memory?', ['Nothing beyond a small k','Accounting for its frequency map and input storage','An alphabetical category list'],1,'Counter can retain every distinct category before selection.'),
('Why reject duplicate receipt IDs before dictionary assignment?', ['To preserve evidence of invalid duplicates','To disable hashing','To sort every row'],0,'Assignment alone can overwrite the earlier record.'),
('Does copying a dictionary isolate its nested mutable values?', ['Yes','No','Only when keys are integers'],1,'A shallow mapping copy shares referenced values.')]),
'python-runtime':('Python runtime and input quiz',[
('Where does a generator’s deferred parsing error occur?', ['Only during its definition','When the failing iteration runs','Only at module import'],1,'Laziness defers execution and its failures until values are requested.'),
('What makes a thread-worker error visible to this caller?', ['Reading future.result()','Ignoring the future','Setting max_workers to two'],0,'The future carries the error and result re-raises it.'),
('Does max_workers bound every queued submission?', ['Yes','No','Only for integer input'],1,'Worker count bounds active workers, not this submit-all list of futures.'),
('What does a failed TaskGroup sibling cause here?', ['Automatic undo of commits','Cancellation of the waiting sibling and grouped failure','Conversion to a zero result'],1,'Cancellation and failure ownership do not roll back completed external effects.'),
('What does strict UTF-8 decoding do with a truncated sequence?', ['Reject it','Silently erase it','Guarantee a valid receipt schema'],0,'Decoding failure is separate from later field/schema checks.'),
('Does JSON parsing prove amount_minor is a positive integer?', ['Yes','No','Only when the object has one key'],1,'The application checks shape, exact type and positive range after parsing.'),
('Why use an object-pairs hook for duplicate JSON members?', ['To reject duplicates before replacement','To alphabetize all member names','To avoid UTF-8'],0,'A normal dictionary could lose earlier repeated-member evidence.'),
('What does the SQLite connection context manage?', ['Connection closure only','Commit or rollback, not closure','A production connection pool'],1,'The fixture closes its connection explicitly in finally.'),
('What parses a quoted comma in CSV correctly?', ['Splitting the line at commas','The CSV reader','An f-string'],1,'Quoting rules belong to the CSV parser rather than delimiter splitting.'),
('What is a context manager cleanup hook unable to guarantee by itself?', ['Release of its own local list references','Undo of a completed external payment','Execution of its finally block during the tested error'],1,'Cleanup is not automatic business compensation.'),
('Where should an exact decimal amount begin?', ['From a decimal string','From a float approximation first','From a log message'],0,'Converting an existing binary float carries its approximation into later work.'),
('What does a logger’s parameter formatting not prevent?', ['Every sensitive-data disclosure','Use of a selected formatter','Level and logger-name fields'],0,'The caller must select safe fields and define redaction and retention policies.')]),
'python-algorithms':('Python algorithm contract quiz',[
('What input rule is required by lower_bound?', ['Sorted ascending values','Unique values only','Nonempty input always'],0,'The half-open boundary search works with duplicates and empty input but assumes sorted order.'),
('What does lower_bound return after every supplied value?', ['The last index','The sequence length','Negative one'],1,'The insertion boundary can be one position after the final element.'),
('When should BFS mark a newly found neighbor?', ['When it enters the queue','After every duplicate dequeue','Only when a route is printed'],0,'Marking at enqueue avoids scheduling the same vertex repeatedly.'),
('What does unweighted BFS distance count?', ['Edges from the start','Arbitrary weight sum','Alphabetic label positions'],0,'Weighted shortest paths need a different selection rule.'),
('What is the bracket stack checking?', ['Nested closing expectations','Only opener and closer totals','Valid Python source'],0,'Equal counts alone cannot detect a crossed pair such as ([)].'),
('What does an unfinished opener leave?', ['A nonempty expectation stack','An accepted expression','An empty graph'],0,'A valid completed nesting requires all expected closers to be consumed.'),
('Does memoization remove recursive stack depth?', ['Yes','No','Only with a global cache'],1,'Cached state reduces repeated work but recursive calls still require depth.'),
('Why is the package-count cache local to one request?', ['To avoid retaining historical requests globally','To remove every allocation','To disable repeated state reuse'],0,'Call-local ownership limits cache lifetime for the bounded problem.'),
('What represents an unreachable package target here?', ['Negative one in the public result','Zero for every failure','An invented valid package size'],0,'Zero is the valid answer for target zero, so impossibility needs another result.'),
('When should the inventory project replace its stored map?', ['After every individual change','After the whole candidate passes','Before parsing any changes'],1,'Staging preserves old state when a later transition fails.'),
('What does the top-k example require for equal counts?', ['A declared tie-breaker','No policy at all','Changing keys into booleans'],0,'A ranking result needs an intentional equal-frequency ordering.'),
('What does strict zip detect?', ['Unequal consumed iterable lengths','Every incorrect domain value','Every unsorted array'],0,'Length equality is separate from validating values or their ordering.')])}
for slug,(title,questions) in BANKS.items():
 path='quizzes/'+slug;refs={'python-basics':['python/python-variables','python/python-functions','python/function-arguments','python/control-flow'],'python-collections':['python/python-lists','python/dictionaries','python/tuples','python/dataclasses'],'python-runtime':['python/json-validation','python/sqlite-transactions','python/thread-pools','python/async-task-groups'],'python-algorithms':['python/binary-search','python/graph-bfs','python/bracket-stack','python/memoization']}[slug]
 e=copy.deepcopy(lookup['quizzes/spring-core']);e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),path=path,title=title,summary='Twelve explained questions on '+title.lower().replace(' quiz','')+'.',subject='python-quizzes',category='Programming Languages',tags=['python','quiz'],sort_order=200+len(added),published_at=stamp,updated_at=stamp)
 e['body']=para('A Python self-check tests operation contracts through twelve questions with explanations.')+'<h2>Review the related lessons</h2><ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in refs)+'</ul><h3>Common Mistakes</h3>'+para('State the input and ownership rule before choosing an output. This browser self-check is not a credential or a hosted code judge.')
 e['data']={'subject_root':root,'section_path':paths['python-quizzes'],'content_format':'html','seo_ready':True,'questions':[{'prompt':q,'options':o,'answer':a,'explanation':x} for q,o,a,x in questions],'duration_minutes':15,'author_path':'authors/aitrove-editorial'};upsert(e);added.append(path)

put('comprehensions','Python comprehensions: build results without changing the input',
'A list comprehension builds a new list from an iterable using a transformation and optional filter.',
'The receipt import accepts positive exact integers and converts each accepted minor-unit amount to a display label. The fixture rejects booleans from this numeric field even though comparison alone would accept True. Both the filter and the representation policy are visible in one expression. It keeps input order and leaves the supplied sequence untouched.',
'An outer list is new; objects returned directly from a comprehension could still be shared. A comprehension also materializes every result immediately. For a long stream, consider [[python/generators|A generator]] and define when input failures should surface. Nested comprehensions can multiply work; compact syntax does not change the number of combinations visited.',
'''amounts = [125, 0, -10, True, 75]
labels = [f"minor:{amount}" for amount in amounts if type(amount) is int and amount > 0]
print(labels)
print(amounts)''',"['minor:125', 'minor:75']\n[125, 0, -10, True, 75]",
'For n values the fixture makes one pass and retains k labels, with O(n) iteration work and O(k) output entries. Formatting cost grows with each integer’s digits.',
['Do not hide a network call or state mutation inside a transformation.','A new result list does not imply its referenced objects are independent.'],['python/control-flow','python/python-lists','python/generators'])

put('slicing','Python list slicing: half-open ranges and shallow ownership',
'A Python list slice selects a half-open sequence range and creates a new outer list containing references to the selected objects.',
'The dispatch fixture selects the middle two receipt identifiers, reverses their order and asks for a range beyond the available end. Slice bounds are clipped, so the oversized range returns an empty list. Direct indexing has a different contract: it must name an existing position. The final operation rejects a zero step instead of pretending it can make progress.',
'A shallow slice does not recursively copy nested state. Reverse slicing materializes another list; reversed supplies an iterator instead. When a page reads a fixed window, distinguish clipped selection from a required count: a short slice does not prove enough records were loaded. [[python/python-lists|Shared nested values]] and [[python/binary-search|Half-open search boundaries]] depend on these ownership and endpoint rules.',
'''receipts = [41, 42, 43, 44]
print(receipts[1:3])
print(receipts[::-1])
print(receipts[20:30])
try:
    receipts[::0]
except ValueError:
    print("zero step rejected")''','[42, 43]\n[44, 43, 42, 41]\n[]\nzero step rejected',
'A slice with k selected entries takes O(k) time and O(k) outer-list storage. A full reverse slice therefore has O(n) retained references rather than bounded memory.',
['A clipped slice is not the same as a validated pagination count.','Nested objects remain shared after slicing.'],['python/python-lists','python/generators','python/binary-search'])

put('sorting','Python sorting: stable keys, independent output and explicit tie rules',
'Python sorted creates an ordered list, while list.sort changes an existing list and returns None.',
'The import queues receipts by minor-unit amount. Two equal amounts retain their incoming order; this is intentional because the input already records arrival order. The fixture prints the original sequence to show that sorted leaves its outer ordering intact, then sorts that owned input by identifier and records the returned None. Sorting the input has to be allowed by its owner.',
'Equal keys do not magically mean identical business records. If the input order is nondeterministic and the output must be reproducible, include a declared identifier tie-breaker. Keys must be comparable; a missing amount or a mixture of text and integers needs validation first. The output still refers to the same row objects, so it is not an immutable snapshot. [[python/heap-top-k|Top-k selection]] avoids sorting all records when only a small ranked subset is needed.',
'''receipts = [(43, 125), (41, 75), (42, 75)]
ranked = sorted(receipts, key=lambda receipt: receipt[1])
print(ranked)
print(receipts)
result = receipts.sort(key=lambda receipt: receipt[0])
print(result)
print(receipts)''','[(41, 75), (42, 75), (43, 125)]\n[(43, 125), (41, 75), (42, 75)]\nNone\n[(41, 75), (42, 75), (43, 125)]',
'Comparison sorting has O(n log n) worst-case comparison work for this list of bounded keys. sorted retains O(n) output entries; in-place sorting may also need O(n) working storage. An expensive key function adds its own per-record cost.',
['Do not assign the None result of list.sort as the ordered list.','Specify tie behavior when arrival order is not reliable.'],['python/closures','python/heap-top-k','python/python-lists'],subject='python-types')

put('pattern-matching','Python match statements: shape matching is not input validation',
'A Python match statement selects a case by structural pattern and an optional guard.',
'The command boundary accepts an object with exactly operation and receipt_id, then matches a read command guarded by an exact positive integer identifier. A matching shape alone would accept the wrong field type. The explicit key check also rejects extra members instead of letting a mapping pattern silently ignore them. This fixture performs no database action; it returns a checked routing decision.',
'A bare name in a case captures a value; it is not a comparison with a same-named local constant. Match order matters because the first successful case wins. Do not put a broad capture before a case intended to reject input. [[python/json-validation|JSON shape checks]] reject duplicate wire members before a dictionary reaches this function.',
'''def route_command(command):
    if not isinstance(command, dict) or set(command) != {"operation", "receipt_id"}:
        raise ValueError("command shape")
    match command:
        case {"operation": "read", "receipt_id": identifier} if type(identifier) is int and identifier > 0:
            return f"read:{identifier}"
        case _:
            raise ValueError("command rejected")

print(route_command({"operation": "read", "receipt_id": 41}))
for command in [{"operation": "read", "receipt_id": True}, {"operation": "read", "receipt_id": 41, "tenant": "a"}]:
    try:
        route_command(command)
    except ValueError:
        print("command rejected")''','read:41\ncommand rejected\ncommand rejected',
'The accepted object has two keys, so this fixture’s matching work is bounded. Building a set of keys still visits all members before rejecting an oversized object; bound the decoded document before this stage.',
['Mapping patterns allow extra keys unless your boundary rejects them.','A captured value still needs a field contract.'],['python/control-flow','python/json-validation','python/python-functions'])

put('type-hints','Python type hints: annotations do not enforce runtime arguments',
'A Python type annotation describes an intended type contract for tooling; it does not validate an argument when a function is called.',
'The unchecked identity function is annotated with integers but returns a supplied string without runtime rejection. The checked function accepts positive exact integers and rejects the same string. These are separate operations: static analysis can find some mistakes before execution, while runtime boundary checks inspect the actual values arriving from a wire or command line.',
'Python code must define whether a numeric contract includes bool, since bool is an int subclass. An annotation does not settle that domain choice. A cast from typing would change the type checker’s view, not convert or validate data. [[python/python-functions|Checked functions]] and [[python/input-exercise|Text parsing]] show where runtime checks belong. No static type checker is installed or invoked by this source.',
'''def declared_identifier(identifier: int) -> int:
    return identifier

def checked_identifier(identifier: int) -> int:
    if type(identifier) is not int or identifier <= 0:
        raise ValueError("positive integer identifier required")
    return identifier

print(declared_identifier("receipt-41"))
print(checked_identifier(41))
try:
    checked_identifier("receipt-41")
except ValueError:
    print("runtime value rejected")''','receipt-41\n41\nruntime value rejected',
'The boundary has fixed-size type and sign checks for these small integers. An annotation adds no automatic parse step, and recursive validation of a large object would carry separate input-size cost.',
['An annotation is not automatic input coercion or rejection.','Do not use a type cast to claim an untrusted value was checked.'],['python/python-functions','python/input-exercise','python/dataclasses'])

put('unittest-contracts','Python unittest: test rejected input and preserve state after failure',
'Python unittest runs assertions inside test cases and reports failures separately from uncaught test errors.',
'The receipt-total boundary requires a nonnegative exact integer quantity and a nonnegative exact integer price. Three tests check an ordinary total, the accepted zero-quantity boundary and rejection of bool. An in-memory runner suppresses variable timing text while the program prints the stable pass/fail result and executed test count. Tests use the standard library without a dependency install.',
'An accepted example cannot prove all inputs work. Choose tests for the failure contract and any state that must survive it. Catching every exception in a test can hide the wrong failure type; assertRaises states the exception the boundary promises. [[python/inventory-project|Staged inventory changes]] needs a before/after snapshot assertion when a later change fails. A successful unit suite is not a deployment or database-isolation test.',
'''import io
import unittest

def receipt_total(quantity, unit_minor):
    if type(quantity) is not int or type(unit_minor) is not int:
        raise TypeError("integer fields required")
    if quantity < 0 or unit_minor < 0:
        raise ValueError("negative field")
    return quantity * unit_minor

class ReceiptTotalChecks(unittest.TestCase):
    def test_total(self):
        self.assertEqual(receipt_total(3, 125), 375)
    def test_zero_quantity(self):
        self.assertEqual(receipt_total(0, 125), 0)
    def test_boolean_rejected(self):
        with self.assertRaises(TypeError):
            receipt_total(True, 125)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptTotalChecks)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print("passed:", result.wasSuccessful())
print("tests:", result.testsRun)''','passed: True\ntests: 3',
'The three fixtures perform bounded arithmetic and allocate one local result stream. Production data and concurrency schedules require their own tests; increasing the test count alone does not improve that coverage.',
['Check the promised exception type instead of swallowing every error.','Include state-preservation assertions for failed batches.'],['python/python-functions','python/inventory-project','python/collection-exercise'],subject='python-examples')

put('datetime-boundaries','Python datetime: require an offset before comparing timestamps',
'A timezone-aware Python datetime carries offset information, while a naive datetime does not identify its relation to UTC.',
'The ingestion boundary accepts a limited-length ISO timestamp that contains an offset and converts it to UTC. Two strings with different local clock readings represent the same instant. The fixture then rejects an otherwise valid timestamp that omits its offset, because the import has no rule for choosing a timezone on the sender’s behalf.',
'This is offset-aware parsing, not a complete wire-format validator: fromisoformat accepts forms beyond a single strict API schema. It also does not resolve named-region daylight-saving ambiguity from an offset-free local time. Define that policy before adding ZoneInfo. Comparing naive and aware values for ordering can fail; replacing tzinfo labels a clock reading and is not the same operation as converting its instant. [[java/zone-transitions|Java zone boundaries]] and [[python/input-exercise|Input contracts]] address related choices.',
'''from datetime import datetime, timezone

def receipt_instant(text):
    if not 1 <= len(text) <= 40:
        raise ValueError("timestamp length")
    instant = datetime.fromisoformat(text)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("offset required")
    return instant.astimezone(timezone.utc)

local = receipt_instant("2026-09-29T10:00:00+05:30")
print(local.isoformat())
print(local == receipt_instant("2026-09-29T04:30:00+00:00"))
try:
    receipt_instant("2026-09-29T10:00:00")
except ValueError:
    print("missing offset rejected")''','2026-09-29T04:30:00+00:00\nTrue\nmissing offset rejected',
'Input length is capped at forty characters, bounding parser work for this fixture. No timezone database lookup or external clock is used. Wider named-zone policies need versioned timezone data and transition tests.',
['Do not silently choose a sender timezone for an offset-free value.','Replacing tzinfo is not an instant-preserving conversion.'],['python/input-exercise','java/zone-transitions'],subject='python-examples')

put('regex-validation','Python regular expressions: use fullmatch for a complete field contract',
'Python re.fullmatch accepts a value only when the pattern matches the entire string.',
'The receipt identifier boundary requires uppercase R, a hyphen and exactly four ASCII digits. It checks length before matching and prints acceptance for a valid field, rejection for prefixed text, a trailing newline and fullwidth digits. The pattern spells out the wire alphabet instead of assuming every character classified as a digit belongs in that format.',
'A substring search answers whether a fragment exists, not whether the field is valid. Even fullmatch is not a complete application boundary: the matched identifier still needs authorization and existence checks before accessing a record. Avoid adding nested ambiguous repetitions to an attacker-controlled input path. [[python/input-exercise|ASCII numeric fields]] and [[python/json-validation|Decoded object shape]] solve different layers.',
'''import re

RECEIPT_ID = re.compile(r"R-[0-9]{4}")
def valid_receipt_id(text):
    return len(text) == 6 and RECEIPT_ID.fullmatch(text) is not None

for identifier in ["R-0041", "xR-0041", "R-0041\\n", "R-００４１"]:
    print(valid_receipt_id(identifier))''','True\nFalse\nFalse\nFalse',
'This fixed-length pattern and six-character gate bound matching work. This cost statement does not apply to an arbitrary regular expression or an unbounded document.',
['A matching identifier is not permission to read its record.','Use an explicit wire alphabet rather than an unintended Unicode class.'],['python/input-exercise','python/json-validation'],subject='python-examples')

exec((ROOT/'work/python-expansion.py').read_text(),globals())
exec((ROOT/'work/python-depth.py').read_text(),globals())
exec((ROOT/'work/python-completion.py').read_text(),globals())
exec((ROOT/'work/python-applied.py').read_text(),globals())
exec((ROOT/'work/python-service.py').read_text(),globals())
exec((ROOT/'work/python-lifetimes.py').read_text(),globals())
exec((ROOT/'work/python-assurance.py').read_text(),globals())
exec((ROOT/'work/python-workflows.py').read_text(),globals())
exec((ROOT/'work/python-boundaries.py').read_text(),globals())
exec((ROOT/'work/python-integrity.py').read_text(),globals())
modules={
'python':[('Interpreter and values',['setup-interpreter','python-variables','operators','control-flow','pattern-matching']),('Functions and failures',['python-functions','function-arguments','exceptions','modules','string-formatting','type-hints']),('Sequence expressions',['comprehensions','slicing']),('Object state',['classes','inheritance','properties'])],
'python-types':[('Sequence and key ownership',['python-lists','tuples','dictionaries','sets','sorting']),('Text and numeric representation',['strings-bytes','decimal-money'])],
'python-advanced':[('Deferred calls and cleanup',['generators','decorators','closures','context-managers','dataclasses']),('Task and worker ownership',['async-task-groups','thread-pools'])],
'python-interview':[('Trace object identity',['python-interview-questions'])],
'python-exercises':[('Validate before publication',['collection-exercise','input-exercise'])],
'python-examples':[('Text and file boundaries',['json-validation','csv-import','pathlib-files']),('Database and diagnostic boundaries',['sqlite-transactions','logging-context']),('Field and test boundaries',['regex-validation','datetime-boundaries','unittest-contracts'])],
'python-quizzes':[('Explained contract banks',list(BANKS))],
'python-projects':[('Local applications',['receipt-cli','inventory-project'])],
'python-reference':[('Operation reminders',['syntax-reference'])],
'python-dsa':[('Search and traversal',['binary-search','graph-bfs']),('Selection, nesting and cached state',['heap-top-k','bracket-stack','memoization'])]}
for subject,rows in EXTRA_MODULES.items():modules.setdefault(subject,[]).extend(rows)
tabs=[{'title':title,'path':path} for path,title,subject in HUBS]
for index,(path,title,subject) in enumerate(HUBS):
 e=copy.deepcopy(lookup.get(path,lookup['java/java']));rows=[{'title':name,'summary':'Answer the questions and read the explanations alongside their linked lessons.' if subject=='python-quizzes' else 'Read the contract, run its program and inspect the failure case.','lessons':[('quizzes/' if subject=='python-quizzes' else 'python/')+s for s in slugs]} for name,slugs in modules[subject]]
 lessons=[p for m in rows for p in m['lessons']]
 body=para('Python programs operate on objects with explicit input, ownership and failure contracts.')+'<h2>Learning roadmap</h2>'+para('This section contains '+str(len(lessons))+' written lessons or quiz banks. Programs are verified on CPython 3.14.6. Standard-library lessons target 3.11+ syntax; lessons using data, web, machine-learning or testing packages state their tested dependencies separately. Framework programs use local test clients, not a deployed service. Read the stated limits before adapting a fixture into an application.')
 for m in rows:body+='<h2>'+html.escape(m['title'])+'</h2>'+para(m['summary'])+'<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in m['lessons'])+'</ul>'
 body+='<h2>Continue learning</h2>'+para('Move between tutorial, collections, advanced material and practice using the subject tabs. The sidebar changes with each section; related examples keep one canonical lesson URL.')+'<ul>'+''.join('<li><a href="/'+t['path']+'">'+html.escape(t['title'])+'</a></li>' for t in tabs if t['path']!=path)+'</ul>'
 e.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://aitrove.in/'+path)),type='subject',path=path,title=title,subject=subject,category='Programming Languages',summary='Operation contracts, checked Python programs and connected learning resources.',body=body,tags=['python'],difficulty=None,sort_order=index,status='published',featured=False,published_at=stamp,updated_at=stamp)
 e['data']={'subject_root':root,'section_path':path,'resource_tabs':tabs,'modules':rows,'seo_ready':True,'content_format':'html','author_path':'authors/aitrove-editorial'};upsert(e)
# Resolve readable titles only after every lesson exists. Links remain outside executable source.
for path in added:
 e=lookup[path]
 def relabel(match):return '<a href="/'+match[1]+'">'+html.escape(lookup[match[1]]['title'])+'</a>'
 e['body']=re.sub(r'<a href="/([^"#]+)">[^<]+</a>',relabel,e['body'])
 for related in e['data'].get('related',[]):related['title']=lookup[related['path']]['title']
# Add reciprocal links where the programming contract overlaps, preserving existing prose.
reverse={'java/pass-by-value':['python/python-variables'],'java/arraylist':['python/python-lists'],'java/bigdecimal':['python/decimal-money'],'java/records':['python/dataclasses'],'java/lambdas':['python/closures'],'java/streams':['python/generators'],'java/try-with-resources':['python/context-managers'],'java/cancellation':['python/async-task-groups'],'java/executor-rejection':['python/thread-pools'],'java/jdbc-transactions':['python/sqlite-transactions'],'java/binary-search':['python/binary-search'],'java/graph-bfs':['python/graph-bfs'],'java/heap-top-k':['python/heap-top-k'],'java/coin-change':['python/memoization'],'spring/metric-cardinality':['python/logging-context']}
for path,targets in reverse.items():
 e=lookup[path];marker='<h2>Compare the Python boundary</h2>';e['body']=e['body'].split(marker)[0]+marker+para(', '.join('[['+p+'|'+lookup[p]['title']+']]' for p in targets)+'.');e['updated_at']=stamp
learning=lookup['learning-paths/python-foundations'];steps=['python/setup-interpreter','python/python-variables','python/control-flow','python/python-functions','python/python-lists','python/dictionaries','python/exceptions','python/json-validation','python/receipt-cli','quizzes/python-basics'];learning['body']=para('The Python foundations path orders interpreter setup, value ownership, control flow and checked application boundaries.')+'<h2>Read and run</h2>'+para('Run each standalone program, then explain its failure case before continuing. Quiz results stay in this browser; this path provides neither certification nor authenticated progress.')+'<ul>'+''.join('<li><a href="/'+p+'">'+html.escape(lookup[p]['title'])+'</a></li>' for p in steps)+'</ul>';learning['data']['steps']=[{'path':p,'title':lookup[p]['title'],'kind':'Quiz' if p.startswith('quizzes/') else 'Read'} for p in steps];learning['data']['content_format']='html';learning['data']['seo_ready']=True;learning['updated_at']=stamp
for entry in entries:
 old=original_lookup.get(entry['path'])
 if old is None:continue
 entry['published_at']=old['published_at']
 compared={key:value for key,value in entry.items() if key not in ('published_at','updated_at')}
 previous={key:value for key,value in old.items() if key not in ('published_at','updated_at')}
 if compared==previous:entry['updated_at']=old['updated_at']
FILE.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
(ROOT.parent.parent/'outputs/python-additions.json').write_text(json.dumps({'articles':[p for p in added if p.startswith('python/')],'quizBanks':[p for p in added if p.startswith('quizzes/')],'hubs':[p for p,t,s in HUBS],'reciprocalPages':len(reverse)},indent=2))
print('Python articles:',sum(e['type']=='article' and e['path'].startswith('python/') for e in entries),'quiz banks:',len(BANKS),'hubs:',len(HUBS))
