import reportCss from "@/components/exams/mock-results.css?raw";

// Package the rendered review so the downloaded file also works without a connection.
export async function reportHtml(root: HTMLElement) {
  const copy = root.cloneNode(true) as HTMLElement;
  const sprites = new Map<string, Document>();
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  defs.setAttribute("width", "0");
  defs.setAttribute("height", "0");
  defs.setAttribute("aria-hidden", "true");
  const glyphs = new Set<string>();
  for (const use of copy.querySelectorAll("use")) {
    const href = use.getAttribute("href") || use.getAttribute("xlink:href") || "";
    const url = new URL(href, location.origin);
    if (
      url.origin !== location.origin ||
      !/^\/jee-(?:advanced-)?archive\/math\.svg$/.test(url.pathname)
    )
      throw Error("Unexpected math source");
    if (!sprites.has(url.pathname)) {
      const r = await fetch(url.pathname, { signal: AbortSignal.timeout(15000) });
      if (!r.ok) throw Error("Math unavailable");
      sprites.set(url.pathname, new DOMParser().parseFromString(await r.text(), "image/svg+xml"));
    }
    const glyph = sprites.get(url.pathname)!.getElementById(url.hash.slice(1));
    if (!glyph || glyph.tagName !== "path") throw Error("Math glyph unavailable");
    const id = `report-${url.pathname.includes("advanced") ? "advanced" : "main"}-${url.hash.slice(1)}`;
    if (!glyphs.has(id)) {
      const path = glyph.cloneNode(true) as Element;
      path.id = id;
      defs.append(path);
      glyphs.add(id);
    }
    use.removeAttribute("xlink:href");
    use.setAttribute("href", "#" + id);
  }
  copy.prepend(defs);
  const images = new Map<string, string>();
  // Sequential requests keep report generation light on the existing media service.
  for (const img of copy.querySelectorAll("img")) {
    const url = new URL(img.getAttribute("src") || "", location.origin);
    if (
      url.origin !== location.origin ||
      (!url.pathname.startsWith("/jee-figures/") &&
        !url.pathname.startsWith("/images/jee-main-reviewed/") &&
        url.pathname !== "/logos/dekhoexams-wordmark.png")
    )
      throw Error("Unexpected image source");
    if (!images.has(url.href)) {
      const r = await fetch(url.href, { signal: AbortSignal.timeout(15000) });
      if (!r.ok || !/^image\/(png|jpeg|webp)(;|$)/i.test(r.headers.get("content-type") || ""))
        throw Error("Diagram unavailable");
      const blob = await r.blob();
      const data = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(Error("Diagram unreadable"));
        reader.readAsDataURL(blob);
      });
      images.set(url.href, data);
    }
    img.src = images.get(url.href)!;
    img.removeAttribute("srcset");
    img.removeAttribute("loading");
  }
  const doc = document.implementation.createHTMLDocument("DekhoExams practice report");
  doc.documentElement.lang = "en";
  doc.head.insertAdjacentHTML(
    "afterbegin",
    '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
  );
  const style = doc.createElement("style");
  style.textContent =
    reportCss +
    "body {margin: 0 auto; padding: 20px; max-width: 1200px} @media print {body {padding:0;max-width:none}}";
  doc.head.append(style);
  doc.body.append(copy);
  return "<!doctype html>" + doc.documentElement.outerHTML;
}

export async function exportMockReport(root: HTMLElement, id: string, print: boolean) {
  const html = await reportHtml(root);
  const url = URL.createObjectURL(new Blob([html], { type: "text/html;charset=utf-8" }));
  if (!print) {
    const a = document.createElement("a");
    a.href = url;
    a.download = `DekhoExams-${id.replace(/[^a-z0-9-]/gi, "-")}-report.html`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    return;
  }
  const frame = document.createElement("iframe");
  frame.title = "Print DekhoExams report";
  frame.style.cssText = "position:fixed;width:1px;height:1px;right:0;bottom:0;border:0";
  const cleanup = () => {
    frame.remove();
    URL.revokeObjectURL(url);
  };
  frame.onload = () => {
    const win = frame.contentWindow;
    if (!win) return cleanup();
    win.addEventListener("afterprint", cleanup, { once: true });
    win.focus();
    win.print();
  };
  frame.src = url;
  document.body.append(frame);
  setTimeout(cleanup, 300000);
}
