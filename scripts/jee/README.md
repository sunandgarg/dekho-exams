# JEE archive

The frontend reads the versioned archive from Cloudflare static assets. Set `JEE_EXAM` to `jee-main` or `jee-advanced`, `JEE_CACHE` to a separate scratch directory for each exam, and `JEE_CONTENT_ORIGIN` to the authorized HTTPS question catalog origin. The collector requires Python, lxml and curl.

```sh
python collect.py
python archive.py build
python archive.py reconcile
python archive.py build
python verify.py "$JEE_EXAM"
```

The collector discovers chapter URLs and question groups first, followed by the paper directory. The reconciliation step checks missing records using their individual public URLs. The verifier checks every indexed question, its neighbors, mathematical glyphs, paper association, language coverage and printable editions against the release inventory.

Chapter and paper routes preserve the published identifiers. Both exams share one canonical question URL format. Paper IDs are case-sensitive. Multiple-choice selections and numerical responses are graded only when the published material explicitly identifies the answer or accepted range. Students can choose whether to include explanations when they print.

The JEE Main catalog also offers 152 local Dekhoexams PDF downloads for the 38 shifts in 2025–2026. The downloadable papers contain answer keys; the separate print editions offer optional worked solutions. The source files shipped for these shifts only. Each published PDF is inventoried with its SHA-256 and page count in `docs/jee-main/part-1-pdfs.json`; changed copies also record the source hash and the questions with pending figures. Six missing key entries are recorded explicitly. The education tests check the download menu against every published checksum.

 Place a reviewed replacement PNG in `public/jee-figures/<data-figure ID>.png`, then rebuild the archive and print editions from the cached records. When tagged editions use different drawings for the same source ID, name each PNG by the first 24 hex characters of SHA-256 of the original ID, a newline, and the exact UTF-8 figure label. Only match a figure after confirming its paper position, language and prompt or choice; leave ambiguous matches pending. Unreviewed diagrams are marked as pending; existing mathematical SVGs are kept. To regenerate only the print editions from published questions, run `python archive.py print`.
