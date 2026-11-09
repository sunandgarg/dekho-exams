import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";

const release = "https://github.com/sunandgarg/dekho-exams/releases/download/jee-main-pdfs-2-4";
const files = (await Promise.all([2,3,4].map(async part =>
  JSON.parse(await readFile(new URL("../../docs/jee-main/part-"+part+"-pdfs.json", import.meta.url))).files
))).flat();
async function restore(r) {
  if (!/^[a-z0-9-]+$/.test(r.paper) || !/^(en|hi|bn)(-dark)?\.pdf$/.test(r.file)) throw Error("Invalid paper manifest path");
  const dir = new URL("../../public/jee-papers/jee-main/"+r.paper+"/",import.meta.url);
  const dest = new URL(r.file,dir), tmp = new URL(r.file+"."+process.pid+".tmp",dir);
  if (existsSync(dest)) return; // The catalog test checks the hashes of existing files.
  await mkdir(dir,{recursive:true});
  let last;
  for (let i=0;i<4;i++) {
    try {
      const res=await fetch(release+"/"+r.paper+"-"+r.file,{signal:AbortSignal.timeout(90000)});
      if (!res.ok) throw Error("HTTP "+res.status);
      const bytes=Buffer.from(await res.arrayBuffer());
      if (bytes.length!==r.bytes || createHash("sha256").update(bytes).digest("hex")!==r.sha256) throw Error("checksum mismatch");
      await writeFile(tmp,bytes);await rename(tmp,dest);return;
    } catch(e) {
      last=e;await rm(tmp,{force:true});
      if(i<3) await new Promise(ok=>setTimeout(ok,1000*2**i));
    }
  }
  throw Error("Cannot restore "+r.paper+"/"+r.file+": "+last);
}
const pending=files.filter(r=>!existsSync(new URL("../../public/jee-papers/jee-main/"+r.paper+"/"+r.file,import.meta.url)));
if (pending.length) console.log("Restoring "+pending.length+" verified PDF files from the project release.");
let next=0;await Promise.all(Array.from({length:4},async()=>{while(next<pending.length)await restore(pending[next++]);}));
