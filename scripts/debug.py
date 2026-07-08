from embed_and_store import build_chunks

chunks = build_chunks()
print(f"Total chunks: {len(chunks)}")

# Break down by (book, chapter) to compare against chunk_text.py's own printout
from collections import Counter
breakdown = Counter((c["book"], c["chapter"]) for c in chunks)
for (book, chapter), count in sorted(breakdown.items()):
    print(f"  {book} chapter {chapter}: {count} chunks")