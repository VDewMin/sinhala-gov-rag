"""
Takes the chunks produced by chunk_text.py, embeds them using a
multilingual model, and stores them in a local ChromaDB collection.

Usage:
    python scripts/embed_and_store.py
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

from chunk_text import parse_extracted_file, merge__by_chapter, chunk_all

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "history_textbooks_sinhala"
EMBED_MODEL_NAME = "intfloat/multilingual-e5-large"

def build_chunks():
    """Reuses same parsing/chunking pipeline from chunk_text.py"""
    grade11_entries = parse_extracted_file(
        Path("data/history-textbook/grade11_extracted.txt"), 
        book_name="grade11"
    )
    grade10_entries = parse_extracted_file(
        Path("data/history-textbook/grade11_extracted.txt"), 
        book_name="grade10"
    )

    all_entries = grade11_entries + grade10_entries
    merged = merge__by_chapter(all_entries)
    return chunk_all(merged)

def main():
    print("Rebuilding chunks from extracted text...")
    chunks = build_chunks()
    print(f" {len(chunks)} chunks ready")

    print(f"Loading embedding model: {EMBED_MODEL_NAME} (downloads ~ 2GB on first run)...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    #multilingual -e5 models require this "passage" prefix
    texts_for_embedding = [f"passage: {c['text']}" for c in chunks]

    print("Embdedding all chunks (this may take a few minutes on CPU)...")
    embeddings = model.encode(texts_for_embedding, show_progress_bar=True, batch_size=16)

    print("Storing in Chroma DB...")
    client = chromadb.PersistentClient(path = str(CHROMA_DIR))

    #Drop any existing collection so re-runs don't make duplicates
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[f"{c['book']}_ch{c['chapter']}_{c['chunk_index']}" for c in chunks],
        embeddings = embeddings.tolist(),
        documents = [c["text"] for c in chunks],
        metadatas = [
            {"book": c["book"], "chapter":c["chapter"], "chunk_index": c["chunk_index"]}
            for c in chunks
        ],
    )

    print(f"\nDone. {collection.count()} chunks stored in {CHROMA_DIR}")

if __name__ == "__main__":
    main()
