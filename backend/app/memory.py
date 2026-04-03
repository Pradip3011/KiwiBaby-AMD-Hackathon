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
        persist_directory="./chroma_db"
    )
)

collection = client.get_or_create_collection(name="testcase_memory")


# -------------------------
# STORE MEMORY (UPGRADED)
# -------------------------
def store_memory(requirement: str, output: str, missing_scenarios=None):
    try:
        embedding = model.encode(requirement).tolist()

        metadata = {
            "output": output
        }

        # 🔥 NEW: store missing scenarios (learning signal)
        if missing_scenarios:
            metadata["missing"] = " || ".join(missing_scenarios[:10])

        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[requirement],
            embeddings=[embedding],
            metadatas=[metadata]
        )

    except Exception as e:
        print("[MEMORY STORE ERROR]", e)


# -------------------------
# RETRIEVE MEMORY (EXISTING)
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

        combined = []
        for doc, meta in zip(docs, metas):
            output = meta.get("output", "")
            combined.append(f"Requirement: {doc}\nOutput: {output[:300]}")

        return combined

    except Exception as e:
        print("[MEMORY RETRIEVE ERROR]", e)
        return []


# -------------------------
# 🔥 NEW: RETRIEVE LEARNED GAPS
# -------------------------
def retrieve_learning(requirement: str, top_k=2):
    try:
        embedding = model.encode(requirement).tolist()

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        if not results or not results.get("metadatas"):
            return []

        metas = results["metadatas"][0]

        learned_gaps = []

        for meta in metas:
            missing = meta.get("missing")
            if missing:
                parts = missing.split("||")
                learned_gaps.extend([p.strip() for p in parts if p.strip()])

        return list(set(learned_gaps))

    except Exception as e:
        print("[MEMORY LEARNING ERROR]", e)
        return []
