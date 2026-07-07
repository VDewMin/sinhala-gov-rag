import pytesseract
from pdf2image import convert_from_path
import pdfplumber
from pathlib import Path

# --- Your machine's specific paths ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"
OCR_LANG = "sin" 

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
            text = (page.extract_text() or "").strip()
            if is_valid_sinhala(text):
                results.append({"page": i, "text": text, "method": "text_layer"})
            else:
                images = convert_from_path(
                    pdf_path, first_page=i, last_page=i, poppler_path=POPPLER_PATH
                )
                ocr_text = pytesseract.image_to_string(images[0], lang=OCR_LANG).strip()
                results.append({"page": i, "text": ocr_text, "method": "ocr_fallback"})
    return results

def extract_images_text(image_dir: Path):
    """OCRs every image in a folder, in sorted filename order."""
    results = []
    image_paths = sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png"))
    for path in image_paths:
        text = pytesseract.image_to_string(str(path), lang=OCR_LANG).strip()
        results.append({"page": path.name, "text": text, "method": "ocr_image"})
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
    image_results = extract_images_text(image_dir)
    print(f"Total images processed: {len(image_results)}")
    if image_results:
        print("\nSample from first image:")
        print(image_results[0]["text"][:300])