// Share disk blocks with the large PDF library on local APFS builds.
import { cpSync, constants } from "node:fs";
import { execFileSync } from "node:child_process";
if (process.platform === "darwin") execFileSync("/bin/cp", ["-cR", "public/.", "dist/client/"]);
else cpSync("public", "dist/client", { recursive: true, mode: constants.COPYFILE_FICLONE });
