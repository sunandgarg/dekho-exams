import reportCss from "@/components/exams/mock-results.css?raw";

// Export only the performance card; question review stays on the website.
export async function reportHtml(root: HTMLElement) {
  const card = root.matches("[data-performance-report]")
    ? root
    : root.querySelector("[data-performance-report]");
  if (!card) throw Error("Performance report unavailable");
  const copy = card.cloneNode(true) as HTMLElement;
  const images = new Map<string, string>();
  // Sequential requests keep report generation light on the existing media service.
  for (const img of copy.querySelectorAll("img")) {
    const url = new URL(img.getAttribute("src") || "", location.origin);
    if (url.origin !== location.origin || url.pathname !== "/logos/dekhoexams-wordmark.png")
      throw Error("Unexpected image source");
    if (!images.has(url.href)) {
      const r = await fetch(url.href, { signal: AbortSignal.timeout(15000) });
      if (!r.ok || !/^image\/(png|jpeg|webp)(;|$)/i.test(r.headers.get("content-type") || ""))
        throw Error("Logo unavailable");
      const blob = await r.blob();
      const data = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(Error("Logo unreadable"));
        reader.readAsDataURL(blob);
      });
      images.set(url.href, data);
    }
    img.src = images.get(url.href)!;
    img.removeAttribute("srcset");
    img.removeAttribute("loading");
  }
  const doc = document.implementation.createHTMLDocument("DekhoExams performance report");
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
