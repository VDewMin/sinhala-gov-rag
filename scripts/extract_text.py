import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from pathlib import Path

# --- Your machine's specific paths ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"
OCR_LANG = "sin" 

BOILERPLATE_LINES = [
    "නොමිලේ බෙදා හැරීම සඳහා ය.",
]

CHAPTER_RANGES = {
    1: (11, 28),
    2: (29, 52),
    3: (53, 62),
    4: (63, 76),
    5: (77, 91),
    6: (92, 119),
    7: (120, 141),
    8: (142, 168),
}

GRADE10_CHAPTER_RANGES = {
    1: (11, 17),
    2: (20, 39),
    3: (41, 53),
    4: (54, 72),
    5: (73, 86),
    6: (88, 100),
    7: (101, 115),
    8: (116, 126),
    9: (127, 135),
    10: (136, 148),
}

def get_chapter_from_filename(filename: str, chapter_ranges: dict):
    """Extracts the page number from a filename like 'history 10 S_page-0042.jpg'
    and returns which chapter it belongs to, or None if outside all ranges."""
    import re
    match = re.search(r"page-(\d+)", filename)
    if not match:
        return None
    page_num = int(match.group(1))
    for chapter, (start, end) in chapter_ranges.items():
        if start <= page_num <= end:
            return chapter
    return None

def get_chapter(page_num: int):
    """Returns the chapter number a page belongs to, or None if it's front matter."""
    for chapter, (start, end) in CHAPTER_RANGES.items():
        if start <= page_num <= end:
            return chapter
    return None 

def remove_boilerplate(text: str) -> str:
    """Strips known repeated footer/header lines that appear on every page."""
    for line in BOILERPLATE_LINES:
        text = text.replace(line, "")
    return text.strip()

def is_valid_sinhala(text: str, min_ratio: float = 0.3) -> bool:
    """Checks that a meaningful proportion of characters are actual Sinhala Unicode,
    not just any character (catches legacy-font garbage that LOOKS like text)."""
    if not text.strip():
        return False
    sinhala_chars = sum(1 for ch in text if "\u0D80" <= ch <= "\u0DFF")
    return (sinhala_chars / len(text)) >= min_ratio


def extract_pdf_text(pdf_path: Path):
    """Extracts text page-by-page from a PDF, falling back to OCR for weak/invalid pages."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):

            chapter = get_chapter(i)
            if chapter is None:
                continue 

            text = (page.extract_text() or "").strip()
            if is_valid_sinhala(text):
                text = remove_boilerplate(text)
                results.append({"page": i, "chapter": chapter, "text": text, "method": "text_layer"})
            else:
                images = convert_from_path(
                    pdf_path, first_page=i, last_page=i, poppler_path=POPPLER_PATH
                )
                ocr_text = pytesseract.image_to_string(images[0], lang=OCR_LANG).strip()
                ocr_text = remove_boilerplate(ocr_text)
                results.append({"page": i, "chapter": chapter, "text": ocr_text, "method": "ocr_fallback"})
    return results

def extract_images_text(image_dir: Path, chapter_ranges: dict):
    """OCRs every image in a folder, in sorted filename order."""
    results = []
    image_paths = sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png"))
    for path in image_paths:
        chapter = get_chapter_from_filename(path.name, chapter_ranges)
        if chapter is None:
            continue
        text = pytesseract.image_to_string(str(path), lang=OCR_LANG).strip()
        text = remove_boilerplate(text)
        results.append({"page": path.name, "chapter": chapter, "text": text, "method": "ocr_image"})
    return results


if __name__ == "__main__":
    pdf_path = Path("data/history-textbook/grade11_history.pdf")
    image_dir = Path("data/history-textbook/grade10-images")

    print("=== Grade 11 PDF (text layer + OCR fallback) ===")
    pdf_results = extract_pdf_text(pdf_path)
    text_layer_count = sum(1 for r in pdf_results if r["method"] == "text_layer")
    ocr_count = sum(1 for r in pdf_results if r["method"] == "ocr_fallback")
    print(f"Pages via text layer: {text_layer_count}, via OCR fallback: {ocr_count}")
    print("\nSample from page 1:")
    print(pdf_results[0]["text"][:300])

    print("\n=== Grade 10 Images (pure OCR) ===")
    image_results = extract_images_text(image_dir, GRADE10_CHAPTER_RANGES)
    print(f"Total images processed: {len(image_results)}")
    if image_results:
        print("\nSample from first image:")
        print(image_results[0]["text"][:300])

    # Save full extracted text for inspection and later chunking
    output_path = Path("data/history-textbook/grade11_extracted.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for r in pdf_results:
            f.write(f"\n\n=== PAGE {r['page']} (Chapter {r['chapter']})===\n\n")
            f.write(r["text"])
    print(f"\nSaved extracted text to {output_path}")

    grade10_output_path = Path("data/history-textbook/grade10_extracted.txt")
    with open(grade10_output_path, "w", encoding="utf-8") as f:
        for r in image_results:
            f.write(f"\n\n=== {r['page']} (Chapter {r['chapter']}) ===\n\n")
            f.write(r["text"])
    print(f"\nSaved extracted text to {grade10_output_path}")