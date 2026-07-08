"""
Quick sanity check: embeds a test question and retrieves the closest
chunks from ChromaDB, so we can verify retrieval quality before
building the full chatbot.

Usage:
    python scripts/test_retrieval.py
"""

from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "history_textbooks_sinhala"
EMBED_MODEL_NAME = "intfloat/multilingual-e5-large"
TOP_K = 3

def main():
    print("Loading embedding model and vector store...")
    model = SentenceTransformer(EMBED_MODEL_NAME)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    print(f"Collection has {collection.count()} chunks.\n")

    print("Type a question in Sinhala (or 'exit' to quit):\n")
    while True:
        question = input("ප්‍රශ්නය > ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        #e5 models require the "query: " prefix
        query_vec = model.encode([f"query: {question}"])[0].tolist()
        results = collection.query(query_embeddings=[query_vec], n_results=TOP_K)
        print(f"\nTop {TOP_K} matches:\n")
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            print(f"--- {meta['book']} / Chapter {meta['chapter']} (distance: {dist:.3f}) ---")
            print(doc[:200])
            print()

if __name__ == "__main__":
    main()   