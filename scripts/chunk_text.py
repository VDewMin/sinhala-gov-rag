from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import re

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

#Priority order for where to break text
SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size = CHUNK_SIZE,
    chunk_overlap = CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

def parse_extracted_file(path:Path, book_name: str):
    """Reads a grade10/grade11_extracted.txt file and splits it back into
    per-page entries with their chapter numbers, using the '=== ... (Chapter N) ===' markers."""
    content = path.read_text(encoding="utf-8")

    #our own page markers
    pattern = r"=== .*?\(Chapter (\d+)\)\s*=== *\n"

    parts = re.split(pattern, content)

    entries = []
    for i in range(1, len(parts), 2):
     chapter_num = int(parts[i])
     text = parts[i+1].strip()
     if text:
        entries.append({"book": book_name, "chapter": chapter_num, "text": text})
    return entries

def merge__by_chapter(entries:list[dict]) -> list[dict]:
   """Combines all pages belonging to the same (book, chapter) into one text block,
    so chunking happens across page boundaries, not awkwardly restarting each page."""
   merged = {}
   for e in entries:
      key = (e["book"], e["chapter"])
      merged.setdefault(key, []).append(e["text"])
    
   return[
       {"book": book, "chapter": chapter, "text": "\n\n".join(texts)}
       for (book, chapter), texts in merged.items()
    ]

def chunk_all(merged_entries:list[dict]) -> list[dict]:
   """Splits each (book, chapter) block into overlapping chunks"""
   chunks = []
   for entry in merged_entries:
      pieces = SPLITTER.split_text(entry["text"])
      for i, piece in enumerate(pieces):
         chunks.append({
            "book": entry["book"],
            "chapter": entry["chapter"],
            "chunk_index": i,
            "text": piece,
         })
   return chunks

if __name__ == "__main__":
   grade11_entries = parse_extracted_file(
      Path("data/history-textbook/grade11_extracted.txt"), book_name = "grade11"
   )

   grade10_entries = parse_extracted_file(
      Path("data/history-textbook/grade10_extracted.txt"), book_name="grade10"
   )

   all_entries = grade11_entries + grade10_entries
   print(f"Total pages parsed: {len(all_entries)}")

   merged = merge__by_chapter(all_entries)
   print(f"Merged into {len(merged)} (book, chapter) blocks")
   for m in merged:
      print(f" {m['book']} chapter {m['chapter']}: {len(m['text'])} chars")

   chunks = chunk_all(merged)
   print(f"\nTotal chunks produced: {len(chunks)}")
   print("\nSample chunk:")
   print(chunks[0])