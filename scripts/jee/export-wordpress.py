from pathlib import Path
import gzip,base64,json,zlib,subprocess,sys
from collections import Counter
r=Path(__file__).resolve().parents[2]; out=Path(sys.argv[1]);counts=Counter();seen=set()
with gzip.open(out,'wt',compresslevel=1) as f:
 f.write("CREATE TABLE IF NOT EXISTS wp_dekho_content_v1 (collection VARBINARY(32) NOT NULL, kind VARBINARY(20) NOT NULL, slug VARBINARY(1024) NOT NULL, body MEDIUMBLOB NOT NULL, PRIMARY KEY(collection,kind,slug)) ENGINE=InnoDB;\n")
 batch=[];size=0
 def flush():
  global size
  if batch:f.write('INSERT INTO wp_dekho_content_v1 VALUES '+','.join(batch)+' ON DUPLICATE KEY UPDATE body=VALUES(body);\n');batch.clear();size=0
 def add(exam,kind,slug,obj):
  global size
  key=(exam,kind,slug);assert key not in seen and len(slug.encode())<=1024;seen.add(key);counts[exam]+=1
  body=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode();compressed=zlib.compress(body);assert zlib.decompress(compressed)==body
  vals=[exam.encode(),kind.encode(),slug.encode(),compressed]
  row='('+','.join("X'"+v.hex()+"'" for v in vals)+')';batch.append(row);size+=len(row)
  if size>350000:flush()
 for exam,dirname in [('jee-main','jee-archive'),('jee-advanced','jee-advanced-archive')]:
  for kind in ['q','chapter','paper','meta']:
   folder=r/'public'/dirname/kind
   for path in sorted(folder.rglob('*.bin')):
    obj=json.loads(gzip.decompress(path.read_bytes()))
    if kind=='q':
     for slug,rec in obj.items():add(exam,kind,slug,rec)
    else:add(exam,kind,path.relative_to(folder).with_suffix('').as_posix(),obj)
 for path in sorted((r/'src/data').glob('*.json')):add('site','catalog',path.stem,json.loads(path.read_bytes()))
 for lesson in json.loads(subprocess.check_output(['node','--input-type=module','-e',"import {SCHOOL_LESSONS} from './src/lib/school-content.ts'; console.log(JSON.stringify(SCHOOL_LESSONS))"],cwd=r)):add('school','lesson',lesson['slug'],lesson)
 for rec in json.loads(gzip.decompress(base64.b64decode((r/'public/__data/cms-snapshot.txt').read_bytes()))):add('computing','entry',rec[0],rec)
 flush()
print(counts,len(seen),out.stat().st_size,flush=True)
