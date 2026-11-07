# JEE Main archive

The frontend reads the published archive from this repo through its Cloudflare assets binding. A student does not need WordPress credentials. The WordPress backend remains on Hostinger.

To refresh this JEE Main snapshot, use Python with lxml and curl. Set `JEE_CACHE` to a scratch directory outside Git, `JEE_CONTENT_ORIGIN` to the authorized question catalog HTTPS origin, and `JEE_PDF_ORIGIN` to the authorized PDF catalog HTTPS origin. The directory and PDF lists in `src/data/jee-main-*.json` describe this inventory; inspect changes to them before refreshing. Run:

```sh
python archive.py index
python archive.py fetch
python archive.py hindi
python chapters.py
python archive.py build
python archive.py reconcile
python archive.py build
python verify.py
```

Collection respects the public crawl rules. Only published HTML is collected; PDF download and private answer endpoints are not requested. A missing translation stays missing. Browsers can open a catalogued external edition or print the local paper view.

Question routes keep both chapter slugs and case-sensitive paper IDs. Assets are gzip-compressed JSON split by the first three hex digits of the SHA-256 of the ID. The importer retains semantic text, approved diagram URLs and the local mathematics glyphs. It discards scripts, styles, handlers and navigation from question HTML. Automatic grading requires a published numerical key or an explicitly identified final choice. The full verifier checks questions against their directory, neighbors, canonical paper association and glyph set.
