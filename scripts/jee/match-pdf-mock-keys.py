"""Offline: match printed MCQ keys to English archive prompts and ordered options (PyMuPDF)."""
import gzip
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata

import pymupdf

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "public/jee-archive"
def norm(text):
    return "".join(unicodedata.normalize("NFKC", text).split()).replace("−", "-")

def plain(markup):
    markup = re.sub(r'<svg\b[^>]*aria-label="([^"]*)"[^>]*>.*?</svg>', r"\1", markup, flags=re.S)
    return norm(html.unescape(re.sub(r"<[^>]+>", "", markup)))

def generate():
    questions = {}
    for f in (ARCHIVE / "q").glob("*.bin"):
        for q in json.load(gzip.open(f)).values():
            if q["chapter"] or q["kind"] != "mcq" or len(q["options"]) != 4:
                continue
            opts = [plain(v) for v in q["options"]]
            if len(set(opts)) != 4 or not all(opts): continue
            digest = hashlib.sha256(json.dumps([q["body"], q["options"]],ensure_ascii=False).encode()).hexdigest()
            questions[q["slug"]] = (plain(q["body"]), opts, digest, q.get("choiceKey"))
    verified, conflicts = {}, set()
    for path in sorted((ROOT / "public/jee-papers/jee-main").glob("*/en.pdf")):
        paper = path.parent.name
        rows = json.load(gzip.open(ARCHIVE / "paper" / (paper+".bin")))
        with pymupdf.open(path) as pdf:
            keypage = next(x[2]-1 for x in pdf.get_toc() if x[1] == "Answer Key")
            text = "\n".join(pdf[i].get_text() for i in range(1,keypage))
            key = "\n".join(pdf[i].get_text() for i in range(keypage,len(pdf)))
        parts = re.split(r"(?m)^Q(\d+)\.\s*\n", text)
        if list(map(int,parts[1::2])) != list(range(1,len(rows)+1)): continue
        printed = re.findall(r"(?m)^(\d+)\.\s*([A-D])[ \t]*$",key)
        if len({n for n,_ in printed}) != len(printed): continue
        for number,letter in printed:
            n=int(number)
            if not 1<=n<=len(rows): continue
            q = questions.get(rows[n-1]["id"])
            if not q: continue
            stem,opts,digest,old = q
            section = parts[2*n]
            choices = re.split(r"(?m)^\(([A-D])\)\s*",section)
            if choices[1::2] != list("ABCD") or len(stem)<18 or stem not in norm(choices[0]): continue
            # Footer text may follow D. Require all four complete choices, in order.
            contents = [norm(re.split(r"(?m)^(?:JEE MAIN\s*\||DekhoExams\s*\||dekhoexams\.com\s*$|Chemistry\s*$|Physics\s*$|Mathematics\s*$)",v)[0]) for v in choices[2::2]]
            if contents != opts: continue
            idx=ord(letter)-65
            if (old is not None and old!=idx) or (digest in verified and verified[digest]!=idx):
                conflicts.add(digest)
            elif old is None:
                verified[digest] = idx
    for k in conflicts: verified.pop(k,None)
    target = ROOT / "scripts/jee/main-mock-pdf-keys.json"
    target.write_text(json.dumps(verified,sort_keys=True,indent=1)+"\n")
    print(len(verified),"additional exact matches;",len(conflicts),"conflicting matches excluded")

if __name__ == "__main__":
    generate()
