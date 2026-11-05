const { createCanvas, GlobalFonts } = require("@napi-rs/canvas");
const { readFileSync, writeFileSync, mkdirSync } = require("node:fs");
const { resolve } = require("node:path");

// Offline asset generation only; the website serves the committed PNGs.
const output = resolve("public/images/discovery");
mkdirSync(output, { recursive: true });
const fontsRoot = process.env.PENPENCIL_FONTS || "/System/Library/Fonts";
const fontFiles = {
  latin: "Supplemental/Arial Rounded Bold.ttf",
  hindi: "Kohinoor.ttc",
  marathi: "Kohinoor.ttc",
  kannada: "NotoSansKannada.ttc",
  tamil: "Supplemental/Tamil Sangam MN.ttc",
  telugu: "KohinoorTelugu.ttc",
  bengali: "KohinoorBangla.ttc",
  gujarati: "KohinoorGujarati.ttc",
  malayalam: "Supplemental/Malayalam Sangam MN.ttc",
  odia: "NotoSansOriya.ttc",
  punjabi: "Supplemental/Gurmukhi Sangam MN.ttc",
  assamese: "KohinoorBangla.ttc",
  urdu: "Supplemental/Arial Unicode.ttf",
};
for (const [name, file] of Object.entries(fontFiles)) {
  if (!GlobalFonts.registerFromPath(resolve(fontsRoot, file), name))
    throw new Error(`Missing font: ${file}`);
}
const palette = ["1746D1", "08795C", "BA382E", "932A67", "946300", "30333B"];
function artwork(name, glyph, color, font = "latin") {
  const canvas = createCanvas(192, 192);
  const ctx = canvas.getContext("2d");
  const rect = (x, y, w, h, radius, fill) => {
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, radius);
    ctx.fill();
  };
  // Original book-cover silhouette with page edges, spine and bookmark.
  rect(12, 16, 168, 168, 23, "#202329");
  rect(20, 24, 156, 154, 17, "#ffffff");
  rect(12, 8, 168, 157, 23, `#${color}`);
  rect(27, 24, 3, 127, 0, "#ffffff38");
  ctx.fillStyle = "#ffd45c";
  ctx.beginPath();
  ctx.moveTo(139, 8);
  ctx.lineTo(157, 8);
  ctx.lineTo(157, 34);
  ctx.lineTo(148, 28);
  ctx.lineTo(139, 34);
  ctx.closePath();
  ctx.fill();
  let size = font === "latin" ? (glyph.length > 1 ? 91 : 108) : 90;
  ctx.font = `700 ${size}px "${font}"`;
  let metrics = ctx.measureText(glyph);
  const width = metrics.actualBoundingBoxLeft + metrics.actualBoundingBoxRight;
  if (width > 126) {
    size *= 126 / width;
    ctx.font = `700 ${size}px "${font}"`;
    metrics = ctx.measureText(glyph);
  }
  ctx.fillStyle = "#ffffff";
  ctx.fillText(
    glyph,
    101 + (metrics.actualBoundingBoxLeft - metrics.actualBoundingBoxRight) / 2,
    88 + (metrics.actualBoundingBoxAscent - metrics.actualBoundingBoxDescent) / 2,
  );
  writeFileSync(resolve(output, `${name}.png`), canvas.toBuffer("image/png"));
}
for (let grade = 1; grade <= 12; grade++)
  artwork(`class-${grade}`, String(grade), palette[(grade - 1) % palette.length]);
const languages = JSON.parse(readFileSync("src/data/language-art.json", "utf8"));
for (const [slug, art] of Object.entries(languages))
  artwork(`language-${slug}`, art.glyph, art.color, slug === "english" ? "latin" : slug);
console.log(`Generated 12 number badges and ${Object.keys(languages).length} language badges.`);
