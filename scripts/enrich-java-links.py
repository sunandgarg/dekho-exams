#!/usr/bin/env python3
"""Add relevant editorial links without changing code or producing duplicate anchors.

Reads the current fixtures, including entries added by other content scripts. The
--dry-run option writes only the link plan/report. No network or secrets are read.
"""
import argparse
from hashlib import sha256
from collections import Counter
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "src/data/fixtures.json"
OUTPUTS = ROOT.parents[1] / "outputs"

# Long phrases precede short phrases. Only prose text nodes inside paragraphs can
# match; headings, links, code, preformatted output and list examples are excluded.
CONCEPTS = [
    ("try-with-resources", "try-with-resources"),
    ("foreign memory", "foreign-memory"),
    ("structured concurrency", "structured-concurrency"),
    ("scoped values", "scoped-values"),
    ("virtual threads", "virtual-threads"),
    ("virtual thread", "virtual-threads"),
    ("prepared statement", "jdbc-prepared"),
    ("database transactions", "jdbc-transactions"),
    ("database transaction", "jdbc-transactions"),
    ("connection pooling", "connection-pool"),
    ("connection pool", "connection-pool"),
    ("isolation level", "database-isolation"),
    ("heap dump", "heap-dump-workflow"),
    ("garbage collection", "gc-diagnostics"),
    ("flight recording", "flight-recorder"),
    ("thread-local", "thread-local"),
    ("HTTP client", "http-client"),
    ("binary search tree", "binary-search-tree"),
    ("binary search", "binary-search"),
    ("binary heap", "binary-heap"),
    ("AVL tree", "avl-tree"),
    ("trie deletion", "trie-deletion"),
    ("strong components", "strong-components"),
    ("shortest paths", "dijkstra"),
    ("depth-first", "graph-dfs"),
    ("breadth-first", "graph-bfs"),
    ("minimum spanning tree", "minimum-spanning-tree"),
    ("topological", "topological-sort"),
    ("longest common subsequence", "longest-subsequence"),
    ("increasing subsequence", "increasing-subsequence"),
    ("edit distance", "edit-distance"),
    ("Fenwick tree", "fenwick-tree"),
    ("knapsack", "zero-one-knapsack"),
    ("memoization", "memoization"),
    ("recursion", "recursion"),
    ("backtracking", "backtracking"),
    ("regular expression", "regular-expressions"),
    ("Unicode", "unicode-encoding"),
    ("grapheme", "grapheme-boundaries"),
    ("normalization", "text-normalization"),
    ("collation", "collation-policy"),
    ("primitive types", "variables-types"),
    ("integer overflow", "operators"),
    ("autoboxing", "boxing"),
    ("overload resolution", "overload-resolution"),
    ("access control", "access-control"),
    ("package boundaries", "access-packages"),
    ("class initialization", "class-initialization"),
    ("class loader", "class-loaders"),
    ("named modules", "java-modules"),
    ("generic bounds", "generics"),
    ("type erasure", "generics"),
    ("immutable collections", "immutable-collections"),
    ("backed view", "collection-views"),
    ("backed views", "collection-views"),
    ("defensive copies", "pass-by-value"),
    ("reference value", "pass-by-value"),
    ("shared mutable state", "locks"),
    ("atomic update", "atomics"),
    ("blocking queue", "blocking-queues"),
    ("thread pool", "executors"),
    ("cancellation", "cancellation"),
    ("interruption", "cancellation"),
    ("reentrant lock", "locks"),
    ("semaphore", "semaphores"),
    ("encounter order", "linkedhashmap"),
    ("key equality", "equals-hashcode"),
    ("comparison order", "comparator-contracts"),
    ("reflection", "reflection"),
    ("annotations", "annotations"),
    ("lambda", "lambdas"),
    ("streams", "streams"),
    ("serialization", "serialization"),
    ("JUnit", "junit-tests"),
    ("Maven", "maven"),
    ("Gradle", "gradle-build"),
    ("JMH", "jmh-benchmarks"),
    ("ArrayList", "arraylist"),
    ("LinkedList", "linkedlist"),
    ("ArrayDeque", "arraydeque"),
    ("ConcurrentHashMap", "concurrent-map"),
    ("LinkedHashMap", "linkedhashmap"),
    ("HashMap", "hashmap"),
    ("HashSet", "hashset"),
    ("TreeMap", "treemap"),
    ("PriorityQueue", "priorityqueue"),
    ("iterators", "iterators"),
]

# The dependency sentence explains the relationship rather than appending a
# repeated list of every topic. The original fifteen zero-anchor bodies receive
# specific editorial prerequisites/comparison links.
DEPENDENCIES = {
    "quiz-preparation": [("variables-types", "types and numeric ranges", "Before choosing an answer, identify the value using {link}."), ("java-quizzes", "Java quiz banks", "Continue with the specific contracts in the {link}.")],
    "collection-choices": [("arraylist", "indexed sequence access", "Compare {link} with endpoint work before choosing storage."), ("arraydeque", "deque operations", "Use {link} to separate FIFO order from a capacity or delivery policy."), ("treemap", "ordered key lookup", "Use {link} when the result depends on nearest keys rather than insertion order.")],
    "annotations": [("reflection", "runtime reflection", "Retention determines whether {link} can read an annotation after compilation."), ("interfaces", "interface contracts", "An annotation records metadata; compare it with the behavior enforced by {link}.")],
    "jvm-memory": [("pass-by-value", "reference values", "Follow {link} before deciding which objects remain reachable."), ("gc-diagnostics", "memory diagnostics", "Use {link} to distinguish reachable retention from a capacity estimate.")],
    "jdbc-prepared": [("try-with-resources", "resource closure", "Apply {link} to statements and results even when SQL execution fails."), ("jdbc-transactions", "commit and rollback", "Parameter binding does not define {link} for a group of writes.")],
    "jdbc-transactions": [("jdbc-prepared", "bound SQL parameters", "Keep {link} separate from the atomic boundary of a transaction."), ("database-isolation", "transaction visibility", "Check {link} before assuming two connections observe the same state.")],
    "http-client": [("cancellation", "deadlines and cancellation", "Treat {link} as explicit request policy rather than proof that remote work stopped."), ("http-failure-project", "bounded HTTP retries", "Compare a single request with {link} before adding a retry loop.")],
    "pattern-switch": [("sealed-classes", "permitted type branches", "Exhaustiveness depends on the {link} known at compilation."), ("records", "record components", "Review {link} before treating a pattern match as a copy of nested mutable data.")],
    "tree-traversal": [("recursion", "call-stack depth", "Compare recursive traversal with {link} before accepting an unbounded input tree."), ("binary-search-tree", "search-tree ordering", "Traversal order alone does not establish {link}.")],
    "graph-bfs": [("arraydeque", "queue operations", "FIFO {link} preserve the layer order used by this traversal."), ("graph-dfs", "depth-first reachability", "Compare minimum-hop discovery with {link}; both can visit the same vertices while answering different questions.")],
    "graph-dfs": [("recursion", "stack depth", "An explicit work stack changes the {link} failure boundary."), ("strong-components", "strong components", "One traversal is not enough to establish mutual reachability; study {link}.")],
    "memoization": [("recursion", "recursive progress", "Caching a result does not repair missing base cases or {link}."), ("tabulation", "bottom-up state evaluation", "Compare cached calls with {link} to account for traversal order and stack use.")],
    "inventory-project": [("treemap", "ordered stock lookup", "The project uses {link} for repeatable display, not as proof of thread safety."), ("multi-index-invariants", "shared stock invariants", "Review {link} before splitting the state across independently updated containers.")],
    "enum-collections": [("enums", "enum state definitions", "Membership depends on the fixed constants described by {link}."), ("collection-views", "returned collection views", "Choose ownership for {link} separately from the enum-backed representation.")],
    "manifest-project": [("console-input", "input validation", "Separate {link} from the decision to publish a file."), ("concurrent-import-project", "failure-preserving imports", "Compare a single import with {link} before introducing workers.")],
}

QUIZZES = {
    "java-basics": ("A Java basics self-check tests value types, expression results, array bounds and loop termination.", "Check primitive types, integer division, array bounds and loop behavior with explained Java basics questions.", [("variables-types", "primitive types"), ("operators", "numeric promotion"), ("control-flow", "conditions and loops")], "Predict the result before choosing an option. Track the declared type and valid index range; the intended business result cannot change the expression's rules.", "Do not treat integer division as decimal division or use length as the last valid array index."),
    "java-linkedlist": ("A LinkedList self-check tests endpoint operations, overloaded removal, iterator ownership and traversal cost.", "Test Java LinkedList endpoint methods, positional removal, null results, iterator edits and indexed traversal costs.", [("linkedlist", "LinkedList contracts"), ("iterators", "iterator edits"), ("arraylist", "indexed storage")], "Identify the selected overload, the empty-list policy and who owns the edit before choosing an answer. A matching output on a populated list does not establish the empty-input contract.", "An int argument can mean a position rather than a stored Integer. A null return is not the same behavior as an exception."),
    "java-collections": ("A collection-contract self-check tests ordering, membership, backed views and the cost of access patterns.", "Review ordering, equality, backed views, queue priority and access costs across Java collection implementations.", [("collection-choices", "collection choices"), ("collection-views", "backed views"), ("comparator-contracts", "comparison rules")], "Name the implementation as well as the interface. Determine whether the returned data is a view, a shallow snapshot or independently owned values.", "Priority removal does not imply sorted iteration. Copying membership does not copy mutable element state."),
    "java-advanced": ("A runtime and concurrency self-check tests visibility, resource closure, reflection and worker completion.", "Check Java volatile updates, reflection failures, runtime metadata and resource ownership with explained answers.", [("atomics", "atomic transitions"), ("reflection", "reflection failures"), ("try-with-resources", "resource closure")], "Separate visibility, atomicity and successful completion. For reflection, distinguish the wrapper exception from the exception thrown by the target method.", "A volatile field does not make a read-modify-write sequence atomic. Successful submission does not prove completed work."),
    "java-modern": ("A modern-Java self-check tests record ownership, sealed branches and version-labelled Java17 and Java21 features.", "Check Java17/21 records, sealed subtype rules, pattern matching, sequenced collections and virtual-thread boundaries.", [("records", "record ownership"), ("sealed-classes", "sealed branches"), ("pattern-switch", "pattern-switch release rules")], "Check the release label before evaluating syntax. Identify whether the rule concerns a final reference, a mutable object or the permitted subtype tree.", "A record is not automatically deeply immutable. Do not assume an API is available in the oldest release used elsewhere on the site."),
    "java-oop": ("An object-ownership self-check tests copied reference values, polymorphic dispatch and stable equality contracts.", "Review Java pass-by-value, final references, dispatch, constructor rules and object equality through ownership questions.", [("pass-by-value", "copied references"), ("polymorphism", "method dispatch"), ("equals-hashcode", "equality and hashing")], "Draw the object references first. Then decide which declaration is selected at compilation and which implementation runs at runtime.", "Reassigning a parameter does not reassign the caller's variable. A final reference can still point to mutable state."),
    "java-generics": ("A generics self-check tests invariant containers, wildcard bounds and the compiler's choice of a method overload.", "Check Java generic invariance, wildcard reads and writes, erasure and overloaded method selection.", [("generics", "generic bounds"), ("overload-resolution", "overload selection"), ("casts", "cast boundaries")], "Track the static type and captured bound instead of substituting a value observed in one run. Determine what the compiler can permit for every legal caller.", "A List of one numeric subtype is not a List of every numeric subtype. A cast does not validate each generic element."),
    "java-streams": ("A stream self-check tests lazy demand, one-use pipelines, encounter order and reduction contracts.", "Review Java stream demand, reuse, encounter order, collectors and reduction laws through explained contract questions.", [("streams", "stream execution"), ("streams-interview", "reduction contracts"), ("stream-gatherers", "gatherer state")], "Identify the terminal operation and any state shared across callbacks. Decide whether the result depends on ordering or a valid associative reduction.", "A stream is not a cached collection. Parallel execution does not repair shared mutable state or an invalid reduction rule."),
    "java-concurrency": ("A concurrency self-check tests admission, visibility, atomic transitions, cancellation and completion boundaries.", "Check Java task admission, queue bounds, atomics, cancellation and worker shutdown with explained concurrency answers.", [("executors", "task admission"), ("cancellation", "cancellation and completion"), ("blocking-queues", "bounded pending work")], "Ask what event the code actually observes: queued, started, stopped, or completed. Identify the owner of every shared transition.", "A cancelled future does not prove a remote side effect was rolled back. A worker count does not bound an unbounded pending queue."),
    "java-io": ("An input and I/O self-check tests parsing, character encoding, file ownership and network failure boundaries.", "Review Java validation, Unicode encoding, stream closure, partial I/O and HTTP failure policies.", [("console-input", "input validation"), ("unicode-encoding", "encoding boundaries"), ("file-channels", "partial file I/O")], "Distinguish bytes from characters and parsing from business validation. Check partial reads, truncated output and who closes each resource.", "A successful read can return fewer bytes than requested. Parsed input can still violate the operation's business range."),
    "java-algorithms": ("An algorithm self-check tests progress, ordering, graph reachability and the invariants that justify a result.", "Check Java tree ordering, trie membership, graph traversal, heap operations and algorithm invariants.", [("binary-search-tree", "tree ordering"), ("trie", "prefix membership"), ("binary-heap", "heap ordering")], "State the invariant before predicting the output. Separate a membership test from prefix reachability and a priority queue from sorted traversal.", "A heap need not be globally sorted. A reachable trie prefix is not necessarily a stored complete key."),
    "java-25": ("A Java25 self-check tests final scoped-value lifetime, gatherer state, source syntax and monitor-related thread rules.", "Test Java25 scoped values, stream gatherers, compact source files, module imports and monitor behavior with explained answers.", [("scoped-values", "scoped-value lifetime"), ("stream-gatherers", "gatherer operations"), ("compact-source", "compact source rules"), ("virtual-thread-monitors", "monitor behavior")], "Use the Java25 baseline stated by the question. Follow nested binding restoration and distinguish ordinary child threads from APIs with explicit scoped inheritance.", "Binding an object does not freeze it. An API final in Java25 can differ from an earlier preview API with the same conceptual purpose."),
    "java-graphs": ("A graph-boundary self-check tests mutual reachability, all-pairs costs, cycle rejection and component interpretation.", "Check Java strong components, all-pairs shortest paths, negative-cycle rejection and graph input bounds.", [("strong-components", "strong components"), ("floyd-warshall", "all-pairs paths"), ("graph-exercises", "reachability checks")], "Distinguish one-way reachability from a shared strong component. Separate an absent edge from a finite cost before reasoning about path arithmetic.", "Component numbers are not stable business identifiers. A shortest-path result cannot ignore a negative cycle within its stated contract."),
    "java-dp": ("A DP and index self-check tests state transitions, subsequence order, item reuse and prefix-range arithmetic.", "Review Java LCS, strict LIS, zero-one knapsack, Fenwick prefix sums and DP state-update direction.", [("longest-subsequence", "common subsequence order"), ("increasing-subsequence", "strict increasing subsequences"), ("zero-one-knapsack", "zero-one item use"), ("fenwick-tree", "prefix sums")], "Name what each cached state means and which prior states the update may read. Check whether equal values, repeated items or an empty interval change the result.", "The LIS tails array does not necessarily reconstruct a chosen subsequence. Updating capacities in the wrong direction can reuse a zero-one item."),
}

class ProseLinker(HTMLParser):
    def __init__(self, body, source, routes, limit=5):
        super().__init__(convert_charrefs=False)
        self.parts=[];self.stack=[];self.source=source;self.routes=routes;self.limit=limit
        self.used=set(re.findall(r'href=["\']/([^"\'#]+)',body));self.added=[]
    def handle_starttag(self, tag, attrs):
        self.parts.append(self.get_starttag_text());self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):self.parts.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        self.parts.append('</'+tag+'>')
        if tag in self.stack:self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self, text):
        if 'p' not in self.stack or any(t in self.stack for t in ('a','code','pre','h2','h3')) or len(self.added)>=self.limit:
            self.parts.append(text);return
        matches=[]
        for phrase,slug in CONCEPTS:
            target='java/'+slug
            if target==self.source or target not in self.routes or target in self.used:continue
            for m in re.finditer(r'(?<![\w.])'+re.escape(phrase)+r'(?![\w.])',text,re.I):
                # Avoid qualified method/API member fragments or code-like calls.
                if text[m.end():m.end()+1] and text[m.end():m.end()+1] in '(.':continue
                matches.append((m.start(),-len(m.group()),m.end(),target,m.group()));break
        selected=[];end=-1
        for start,_,stop,target,label in sorted(matches):
            if start<end or target in self.used or len(self.added)+len(selected)>=self.limit:continue
            selected.append((start,stop,target,label));self.used.add(target);end=stop
        pos=0
        for start,stop,target,label in selected:
            self.parts.append(text[pos:start]);self.parts.append('<a href="/'+target+'">'+label+'</a>');pos=stop
            self.added.append({'target':target,'anchor':label,'kind':'context'})
        self.parts.append(text[pos:])
    def handle_entityref(self,name):self.parts.append('&'+name+';')
    def handle_charref(self,name):self.parts.append('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.parts.append('<!'+decl+'>')

def current_targets(body):return set(re.findall(r'href=["\']/([^"\'#]+)',body))

def add_dependencies(entry, routes, added, limit=5):
    body=entry['body'];used=current_targets(body);slug=entry['path'].split('/',1)[1]
    chosen=[]
    for target,label,sentence in DEPENDENCIES.get(slug,[]):
        path='java/'+target
        if path in routes and path!=entry['path'] and path not in used and len(added)+len(chosen)<limit:
            chosen.append({'target':path,'anchor':label,'sentence':sentence});used.add(path)
    # Existing editors already specified deliberate dependencies in related.
    # Insert them only where a body still has fewer than three distinct targets.
    for rel in entry.get('data',{}).get('related',[]):
        path=rel.get('path');label=rel.get('title')
        if len(used)>=3 or len(added)+len(chosen)>=limit:break
        if path not in routes or path==entry['path'] or path in used or not label:continue
        chosen.append({'target':path,'anchor':label,'sentence':'Compare the boundary explained in {link} with the assumptions made by this program.'});used.add(path)
    # A prerequisite and one purposeful onward path for older bodies with no
    # related metadata. Only used when no useful lesson link is present.
    if not used:
        fallback=[('java/setup','the JDK toolchain','Check {link} before treating a compile failure as a failure of the algorithm.'),('java/test-boundaries','boundary tests','Use {link} to turn the stated input and failure contracts into checks.')]
        for path,label,sentence in fallback:
            if path in routes and path!=entry['path'] and len(added)+len(chosen)<limit:
                chosen.append({'target':path,'anchor':label,'sentence':sentence});used.add(path)
    if chosen:
        paragraphs=[]
        for d in chosen:
            link='<a href="/'+d['target']+'">'+escape(d['anchor'])+'</a>'
            paragraphs.append('<p>'+d['sentence'].format(link=link)+'</p>')
            added.append({'target':d['target'],'anchor':d['anchor'],'kind':'dependency'})
        block='<h2>Connect the contracts</h2>'+''.join(paragraphs)
        # Place dependency discussion before the existing onward-reading section.
        if '<h2>Read next</h2>' in body:body=body.replace('<h2>Read next</h2>',block+'<h2>Read next</h2>',1)
        else:body+=block
    entry['body']=body


def enrich_article(entry, routes):
    data=entry.setdefault('data',{})
    digest=sha256(entry['body'].encode()).hexdigest()
    if data.get('java_link_enriched_sha256')==digest:return []
    linker=ProseLinker(entry['body'],entry['path'],routes)
    linker.feed(entry['body']);linker.close();entry['body']=''.join(linker.parts)
    add_dependencies(entry,routes,linker.added)
    data['java_link_enriched_sha256']=sha256(entry['body'].encode()).hexdigest()
    return linker.added


def run(dry_run=False):
    entries=json.loads(FIXTURES.read_text());routes={e['path'] for e in entries if e['status']=='published' and e['type']!='course'}
    plan=[];marked=Counter();before=Counter();after=Counter()
    for e in entries:
        is_java=e['path'].startswith('java/') or e['path'].startswith('quizzes/java')
        if not is_java or e['status']!='published':continue
        d=e.setdefault('data',{})
        if e['type']=='article' and d.get('content_format')=='html':
            before[len(current_targets(e['body']))]+=1
            added=enrich_article(e,routes)
            after[len(current_targets(e['body']))]+=1
            if added:plan.append({'path':e['path'],'links':added})
            d['seo_ready']=True;marked['article']+=1
        elif e['type']=='subject':d['seo_ready']=True;marked['subject']+=1
        elif e['type']=='quiz':
            slug=e['path'].split('/',1)[1]
            if slug not in QUIZZES:continue
            definition,summary,lessons,approach,mistake=QUIZZES[slug]
            anchors=[(path,label) for path,label in [('java/'+q,t) for q,t in lessons] if path in routes]
            review=', '.join('<a href="/'+q+'">'+escape(t)+'</a>' for q,t in anchors)
            e['summary']=summary;e['body']='<p>'+definition+'</p><h2>Review the contracts</h2><p>Review '+review+' before answering.</p><h2>Choose and explain an answer</h2><p>'+approach+'</p><p>Select an answer for every question, then check the result and read each explanation. Progress remains in this browser; this is a self-check, not a judged program submission or a credential.</p><h3>Common Mistakes</h3><p>'+mistake+'</p>'
            d['subject_root']='java/java';d['section_path']='java/java-quizzes'
            d['content_format']='html';d['seo_ready']=True;marked['quiz']+=1
    # Qualify duplicate titles while keeping unfinished AI-tool bodies unreviewed.
    for e in entries:
        if e['type']=='article' and e['path'].startswith('ai-tools/'):
            tool='ChatGPT / Codex' if '/chatgpt-codex/' in e['path'] else 'Claude / Claude Code' if '/claude-claude-code/' in e['path'] else None
            if tool:
                if not e['title'].startswith(tool+': '):e['title']=tool+': '+e['title']
                e.setdefault('data',{})['seo_ready']=False
    author=next((e for e in entries if e['path']=='authors/aitrove-editorial'),None)
    if author:
        author['summary']='AI Trove’s editorial process covers original explanations, runnable examples, stated release requirements and corrections.'
        author['body']='<p>AI Trove Editorial prepares programming lessons with original explanations, application examples and explicit input and failure contracts.</p><h2>How material is prepared</h2><p>AI-assisted drafting is used in this project. Technical facts are checked against official specifications and API documentation; a copied program with different values is not the writing process. Lessons separate public API guarantees from implementation details and name the Java release required by their examples.</p><h2>What code checks establish</h2><p>Java examples with complete programs are checked with the stated compiler target and compared with their displayed output. Some examples require documented external dependencies or project fixtures. Reproducible source files accompany the Java lessons. Compilation and local test results do not prove production safety, performance under load or correctness for every possible input.</p><h2>Review and corrections</h2><p>Readers can report an incorrect statement, a failing program or a missing boundary through <a href="/about/contact-us">AI Trove contact details</a>. A correction should identify the lesson, Java release, input and observed result. Content dates should reflect a substantive revision rather than an automatic freshness claim.</p><h3>Editorial limits</h3><p>This profile describes a process, not a professional qualification. No individual author credentials, independent review, affiliation or search ranking are claimed. Unfinished preview material is kept separate from content marked ready for indexing.</p>'
        author.setdefault('data',{})['content_format']='html';author['data']['seo_ready']=True;marked['author']+=1
    totals=sum(len(item['links']) for item in plan)
    result={'at':datetime.now(timezone.utc).isoformat(),'dryRun':dry_run,'javaArticles':marked['article'],'javaHubs':marked['subject'],'javaQuizzes':marked['quiz'],'markedTypes':dict(marked),'changedLinkBodies':len(plan),'addedLinks':totals,'beforeUniqueTargetsHistogram':dict(sorted(before.items())),'afterUniqueTargetsHistogram':dict(sorted(after.items())),'quizDescriptionsUnique':len({e['summary'] for e in entries if e['type']=='quiz' and e['path'].startswith('quizzes/java')}),'plan':plan}
    if not dry_run:FIXTURES.write_text(json.dumps(entries,indent=2,ensure_ascii=False)+'\n')
    (ROOT/'work/java-publish-link-plan.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    OUTPUTS.mkdir(exist_ok=True);(OUTPUTS/'java-publish-link-enrichment.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='plan'},indent=2))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dry-run',action='store_true');run(parser.parse_args().dry_run)
