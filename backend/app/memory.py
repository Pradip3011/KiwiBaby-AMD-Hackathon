import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# -------------------------
# Load embedding model
# -------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------
# Persistent ChromaDB
# -------------------------
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="./chroma_db"  # 🔥 persists memory
    )
)

collection = client.get_or_create_collection(name="testcase_memory")


# -------------------------
# STORE MEMORY
# -------------------------
def store_memory(requirement: str, output: str):
    try:
        embedding = model.encode(requirement).tolist()

        collection.add(
            ids=[str(uuid.uuid4())],  # 🔥 FIXED
            documents=[requirement],
            embeddings=[embedding],
            metadatas=[{"output": output}]  # 🔥 FIXED KEY
        )

    except Exception as e:
        print("[MEMORY STORE ERROR]", e)


# -------------------------
# RETRIEVE MEMORY
# -------------------------
def retrieve_similar(requirement: str, top_k=2):
    try:
        embedding = model.encode(requirement).tolist()

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        if not results or not results.get("documents"):
            return []

        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]

        # 🔥 Combine requirement + output
        combined = []
        for doc, meta in zip(docs, metas):
            output = meta.get("output", "")
            combined.append(f"Requirement: {doc}\nOutput: {output[:300]}")

        return combined

    except Exception as e:
        print("[MEMORY RETRIEVE ERROR]", e)
        return []
