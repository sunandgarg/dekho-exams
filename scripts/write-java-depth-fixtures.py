"""Add source-only access and controlled diagnostic checks to the public kit."""
import html,json,pathlib,re,shutil,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];kit=ROOT/'work/java-finish/source-kit';OUT=ROOT.parent.parent/'outputs'
def write(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.strip()+'\n')
files={
 'src/in/aitrove/base/Quantity.java':'package in.aitrove.base;\npublic class Quantity { protected int units=7; private int internal=3; int packageUnits(){return units;} }',
 'src/in/aitrove/adapter/DeliveryQuantity.java':'package in.aitrove.adapter;\nimport in.aitrove.base.Quantity;\npublic class DeliveryQuantity extends Quantity {public int readOwn(){return units;} public int readCompatible(DeliveryQuantity other){return other.units;}}',
 'src/in/aitrove/app/Main.java':'package in.aitrove.app;\nimport in.aitrove.adapter.DeliveryQuantity;\npublic class Main {public static void main(String[] args){DeliveryQuantity quantity=new DeliveryQuantity();System.out.println(quantity.readOwn());System.out.println(quantity.readCompatible(quantity));}}',
 'negative/WrongReceiver.java':'package in.aitrove.adapter;\nimport in.aitrove.base.Quantity;\npublic class WrongReceiver extends Quantity {int read(Quantity other){return other.units;}}',
 'negative/PackageRead.java':'package in.aitrove.adapter;\nimport in.aitrove.base.Quantity;\npublic class PackageRead extends Quantity {int read(){return packageUnits();}}',
 'negative/PrivateRead.java':'package in.aitrove.adapter;\nimport in.aitrove.base.Quantity;\npublic class PrivateRead extends Quantity {int read(){return internal;}}'}
for path,text in files.items():write(kit/'access-packages'/path,text)
es=json.loads((ROOT/'src/data/fixtures.json').read_text());body=next(e['body'] for e in es if e['path']=='java/heap-dump-workflow')
source=html.unescape(re.search(r'<pre><code class="language-java">([\s\S]*?)</code></pre>',body)[1]);write(kit/'diagnostics/RetainedReceiptFixture.java',source)
write(kit/'verify-boundaries.py',r'''
"""Verify only the included package sources and the JVM this script starts."""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
parser=argparse.ArgumentParser();parser.add_argument('--jdk-home');args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parent
bin=pathlib.Path(args.jdk_home)/'bin' if args.jdk_home else None
def tool(name):
    path=str(bin/name) if bin else shutil.which(name)
    if not path:raise RuntimeError('Missing JDK tool: '+name)
    return path
def run(command):
    return subprocess.run(command,capture_output=True,text=True,timeout=20)
with tempfile.TemporaryDirectory(prefix='aitrove-owned-fixture-') as temporary:
    work=pathlib.Path(temporary);classes=work/'classes';classes.mkdir()
    good=list((root/'access-packages/src').rglob('*.java'))
    compiled=run([tool('javac'),'--release','8','-d',str(classes),*map(str,good)])
    assert compiled.returncode==0,compiled.stderr
    launched=run([tool('java'),'-cp',str(classes),'in.aitrove.app.Main'])
    assert launched.returncode==0 and launched.stdout.strip()=='7\n7',launched.stderr
    negatives=[]
    for path in sorted((root/'access-packages/negative').glob('*.java')):
        bad=run([tool('javac'),'--release','8','-cp',str(classes),'-d',str(classes),str(path)])
        assert bad.returncode!=0 and 'error:' in bad.stderr,path.name
        negatives.append(path.name)
    compiled=run([tool('javac'),'--release','21','-d',str(classes),str(root/'diagnostics/RetainedReceiptFixture.java')])
    assert compiled.returncode==0,compiled.stderr
    process=subprocess.Popen([tool('java'),'-Xmx64m','-cp',str(classes),'RetainedReceiptFixture','--inspect'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='retained=50'
        assert process.stdout.readline().strip()=='ready'
        histogram=run([tool('jcmd'),str(process.pid),'GC.class_histogram'])
        assert histogram.returncode==0,histogram.stderr
        assert re.search(r'\s+50\s+\d+\s+RetainedReceiptFixture\$Entry(?:\s|$)',histogram.stdout),histogram.stdout
        dump=work/'owned-fixture.hprof'
        capture=run([tool('jcmd'),str(process.pid),'GC.heap_dump',str(dump)])
        assert capture.returncode==0,capture.stderr
        assert dump.stat().st_size>1000
        with dump.open('rb') as file:assert file.read(12)==b'JAVA PROFILE'
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
    print(json.dumps({'positivePackageLaunch':'7 / 7','negativeCompilations':negatives,'histogramRetainedEntries':50,'heapCaptureVerified':True,'onlyOwnedProcessInspected':True,'temporaryDumpRemovedOnExit':True,'passed':True}))
''')
readme=kit/'README.md';text=readme.read_text();text+='''\n## Package-access and heap-capture checks\n\nRun `python3 verify-boundaries.py --jdk-home /path/to/jdk21` from this kit. It compiles the valid cross-package sources, requires three invalid accesses to fail compilation, and captures a histogram and heap dump from the synthetic JVM it starts. The temporary dump is removed on exit; no other JVM is inspected. Use a full JDK with javac, java and jcmd. A managed machine may restrict attaching even to a process you own.\n''';readme.write_text(text)
files=[p for p in kit.rglob('*') if p.is_file() and not any(part in {'target','build','.gradle','out'} for part in p.relative_to(kit).parts)]
archive=ROOT/'public/downloads/aitrove-java-source-kit.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,'aitrove-java-source-kit/'+str(p.relative_to(kit)))
shutil.copyfile(archive,OUT/archive.name)
print(json.dumps({'sourceKitFiles':len(files),'zipBytes':archive.stat().st_size}))
