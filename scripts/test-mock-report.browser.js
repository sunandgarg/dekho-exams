// Run in the browser on a submitted mock. Checks the actual download, without saving a file.
async function checkMockReportDownload() {
  const assert = (value, message) => {
    if (!value) throw Error(message);
  };
  const card = document.querySelector("[data-performance-report]");
  assert(card && document.querySelector(".mock-result"), "Submit a mock first");
  const create = URL.createObjectURL;
  const click = HTMLAnchorElement.prototype.click;
  let report;
  try {
    URL.createObjectURL = (blob) => {
      report = blob;
      return create(blob);
    };
    HTMLAnchorElement.prototype.click = function () {};
    [...document.querySelectorAll("button")]
      .find((b) => b.textContent === "Download report")
      .click();
    const deadline = Date.now() + 20000;
    while (!report && Date.now() < deadline) await new Promise((r) => setTimeout(r, 100));
    assert(report, "Report download failed");
    const html = await report.text();
    const doc = new DOMParser().parseFromString(html, "text/html");
    assert(doc.querySelector("[data-performance-report]"), "Missing performance card");
    assert(
      !doc.querySelector(".mock-result, .mock-question, .mock-answer, .mock-options, .jee-prose"),
      "Question content leaked into report",
    );
    assert(doc.querySelectorAll(".mock-kpis > div").length === 8, "Missing KPIs");
    assert(
      doc.querySelectorAll(".mock-subject").length ===
        card.querySelectorAll(".mock-subject").length,
      "Missing subject breakdown",
    );
    assert(doc.body.textContent === card.textContent, "Export differs from displayed results");
    assert(
      doc.images.length === 1 && doc.images[0].src.startsWith("data:image/png;base64,"),
      "Logo is not embedded",
    );
    assert(
      !doc.querySelector("script, iframe, svg, link, [srcset]"),
      "Unexpected external content",
    );
    assert(!/NaN|Infinity/.test(doc.body.textContent), "Invalid report metrics");
    return { bytes: report.size, kpis: 8, questionContent: 0, embeddedLogos: 1, html };
  } finally {
    URL.createObjectURL = create;
    HTMLAnchorElement.prototype.click = click;
  }
}
