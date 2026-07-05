import os

from sentence_transformers import SentenceTransformer
import chromadb


CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")


class SemanticMemory:
    def __init__(self, collection_name: str = "task_memory"):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def store(self, task: str, document: str, score: int):
        embedding = self.encoder.encode(task).tolist()
        doc_id = f"task_{abs(hash(task))}"
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[{"task": task, "score": score}],
        )

    def query(self, task: str, n: int = 3) -> list[str]:
        count = self.collection.count()
        if count == 0:
            return []
        embedding = self.encoder.encode(task).tolist()
        results = self.collection.query(
            query_embeddings=[embedding], n_results=min(n, count)
        )
        docs = results.get("documents", [[]])
        return docs[0] if docs else []


memory = SemanticMemory()
