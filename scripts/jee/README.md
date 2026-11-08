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

PDF catalogs link only to Dekhoexams print editions. Place a reviewed replacement PNG in `public/jee-figures/<data-figure ID>.png`, then rebuild the archive and print editions from the cached records. Unreviewed diagrams are marked as pending; existing mathematical SVGs are kept. To regenerate only the print editions from published questions, run `python archive.py print`.
