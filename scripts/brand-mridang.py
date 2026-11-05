"""Create a separate Pencil2Pen reading copy without changing NCERT page artwork."""

from io import BytesIO
from pathlib import Path
import sys

from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


SOURCE_FILES = ["aemr1ps.pdf", *(f"aemr1{number:02}.pdf" for number in range(1, 10))]
MARGIN = 30
FONT = "Pencil2PenNunito"


def draw_wordmark(page: canvas.Canvas, x: float, y: float, size: int, right: bool = False) -> None:
    parts = (("pencil", "#202329"), ("2", "#bf601e"), ("pen", "#202329"))
    if right:
        x -= sum(pdfmetrics.stringWidth(text, FONT, size) for text, _ in parts)
    page.setFont(FONT, size)
    for text, color in parts:
        page.setFillColor(HexColor(color))
        page.drawString(x, y, text)
        x += pdfmetrics.stringWidth(text, FONT, size)


def brand_layer(width: float, height: float) -> PageObject:
    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=(width, height))
    draw_wordmark(page, width - MARGIN, height - 20, 11, right=True)
    draw_wordmark(page, MARGIN, 11, 10)
    page.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def main(source_dir: Path, output: Path) -> None:
    pdfmetrics.registerFont(
        TTFont(FONT, Path(__file__).resolve().parents[1] / "public/fonts/font-3.ttf")
    )
    missing = [name for name in SOURCE_FILES if not (source_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing NCERT source sections: {', '.join(missing)}")

    writer = PdfWriter()
    count = 0
    for name in SOURCE_FILES:
        for original in PdfReader(source_dir / name).pages:
            width = float(original.mediabox.width)
            height = float(original.mediabox.height)
            page = PageObject.create_blank_page(width=width + 2 * MARGIN, height=height + 2 * MARGIN)
            page.merge_transformed_page(original, Transformation().translate(MARGIN, MARGIN))
            page.merge_page(brand_layer(width + 2 * MARGIN, height + 2 * MARGIN))
            writer.add_page(page)
            count += 1

    writer.add_metadata({
        "/Title": "Mridang - Class 1 English (Pencil2Pen reading copy)",
        "/Author": "NCERT",
        "/Subject": "Original NCERT textbook pages with Pencil2Pen marks in added margins",
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        writer.write(stream)
    print(f"Wrote {count} pages to {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: brand-mridang.py SOURCE_DIR OUTPUT_PDF")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
