"""Package the inherited computing examples under the site's current project and package names."""
from pathlib import Path
import re, zipfile

root=Path(__file__).resolve().parents[1]
def brand(text):
 return re.sub(r'ai ?trove',lambda m:'DEKHOEXAMS' if m[0].isupper() else 'dekhoexams' if m[0].islower() else 'Dekhoexams',text,flags=re.I)

for old in sorted((root/'docs/legacy-kits').glob('*.zip')):
 target=root/'public/downloads'/brand(old.name)
 with zipfile.ZipFile(old) as src, zipfile.ZipFile(target,'w') as dest:
  for entry in src.infolist():
   data=src.read(entry)
   # Third-party notices and licence files keep their original names and contents.
   if re.search('copyright|licen[sc]e|notice',entry.filename,re.I):dest.writestr(entry,data);continue
   info=zipfile.ZipInfo(brand(entry.filename),entry.date_time)
   info.compress_type=zipfile.ZIP_DEFLATED
   info.external_attr=entry.external_attr
   dest.writestr(info,brand(data.decode()).encode())
 with zipfile.ZipFile(target) as check:
  assert check.testzip() is None and len(check.namelist())==len(set(check.namelist()))
