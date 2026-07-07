import pdfplumber
from pathlib import Path

PDF_PATH = Path("data/history-textbook/grade11_history.pdf")
MIN_CHARS_PER_PAGE = 20  # below this, we treat the page as "no usable text"

def check_pages(pdf_path: Path):
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            has_text = len(text.strip()) > MIN_CHARS_PER_PAGE
            results.append((i, has_text, len(text.strip())))
    return results

if __name__ == "__main__":
    results = check_pages(PDF_PATH)
    needs_ocr_pages = [r for r in results if not r[1]]

    print(f"Total pages: {len(results)}")
    print(f"Pages with usable text: {len(results) - len(needs_ocr_pages)}")
    print(f"Pages needing OCR: {len(needs_ocr_pages)}")

    if needs_ocr_pages:
        print("\nPages that need OCR:")
        for page_num, _, char_count in needs_ocr_pages:
            print(f"  Page {page_num}: only {char_count} chars extracted")