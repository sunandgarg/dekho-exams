# Pencil2Pen Discovery Artwork

25 locally authored book-badge compositions: numbers 1-12 and representative letters for all 13 language directories. No competitor artwork, logos, stock images or remote image services are used.

The design source is `scripts/generate-discovery-art.cjs`; language glyphs and labels live in `src/data/language-art.json`. PNGs are 192 x 192 pixels with transparent surroundings, displayed at 40-64 CSS pixels. Keep the visible class/language label next to each decorative image. Letters and numbers are ordinary writing symbols, not exclusive Pencil2Pen marks.

Regeneration uses Node with `@napi-rs/canvas` and locally installed macOS fonts, whose files are not bundled or redistributed. Set `NODE_PATH` to a tooling installation containing that package, then run `node scripts/generate-discovery-art.cjs` from the project root. `PENPENCIL_FONTS` can override the font directory; the script lists required font files. The production site only needs the checked-in PNG files, not the generation tools.
