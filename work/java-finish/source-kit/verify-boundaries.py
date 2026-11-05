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
