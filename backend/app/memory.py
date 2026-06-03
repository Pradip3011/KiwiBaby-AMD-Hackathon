import os
import uuid
import logging

# Initialize formal production logger
logger = logging.getLogger("kiwibaby.memory")

# 🛡️ Safe Extraction of Vector Package Binary Hooks
try:
    import chromadb

    # Disable ChromaDB on Windows
    if os.name == "nt":
        HAS_CHROMADB = False
    else:
        HAS_CHROMADB = True

except ImportError:
    HAS_CHROMADB = False
    logger.warning("ChromaDB binary packages unavailable. Activating fallback pipeline.")

# ---------------------------------------------------------
# 🧠 Hybrid Cross-Platform Embedding Engine
# ---------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer
    # Local Windows acceleration path
    model = SentenceTransformer("all-MiniLM-L6-v2")
    HAS_LOCAL_TRANSFORMERS = True
    logger.info("Memory Engine: Utilizing local SentenceTransformer acceleration.")
except ImportError:
    # Serverless Cloud path (Vercel Linux container)
    import google.generativeai as genai
    HAS_LOCAL_TRANSFORMERS = False
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    logger.info("Memory Engine: Heavy ML dependencies skipped. Switching to Gemini Cloud Embeddings.")


def generate_embedding(text: str) -> list:
    """
    Generates a dense vector embedding. Handles local 384-dim structural 
    vectors on Windows and 768-dim cloud vectors on serverless nodes.
    """
    if HAS_LOCAL_TRANSFORMERS:
        return model.encode(text).tolist()
    
    # Cloud execution fallback
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("Missing critical environment key: GEMINI_API_KEY")
        
    response = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"
    )
    return response['embedding']


# ---------------------------------------------------------
# 🗄️ Cloud-Resilient Vector Database Client Configuration
# ---------------------------------------------------------
IS_VERCEL = os.getenv("VERCEL") is not None

client = None
collection = None

if HAS_CHROMADB:
    try:
        if IS_VERCEL:
            # Ephemeral memory mapping to bypass serverless read-only disk restrictions
            client = chromadb.EphemeralClient()
            logger.info("ChromaDB: Initialized serverless cloud sandbox.")
        else:
            # Modernized persistent client architecture for local development
            db_path = os.path.join(os.getcwd(), "chroma_db")
            client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB: Connected to local storage at: {db_path}")
        
        collection = client.get_or_create_collection(name="testcase_memory")
    except Exception as runtime_err:
        logger.error(f"ChromaDB runtime initialization bypassed: {runtime_err}. Activating sandbox fallback mock.")
        client = None

# 🚀 BULLETPROOF FALLBACK MOCK: Keeps the server completely immune to Vercel boot crashes
if client is None or collection is None:
    class EphemeralFallbackCollection:
        def add(self, ids, documents, embeddings, metadatas):
            logger.info("Fallback Collection: Captured store command in sandbox.")
            return True
        def query(self, query_embeddings, n_results=2):
            logger.info("Fallback Collection: Captured query command in sandbox.")
            return {"documents": [[]], "metadatas": [[]]}
            
    collection = EphemeralFallbackCollection()
    logger.info("KiwiBaby Core: Ephemeral fallback virtual memory layer successfully mounted.")


# ---------------------------------------------------------
# 📥 Core Operational Framework Methods
# ---------------------------------------------------------

def store_memory(requirement: str, output: str, missing_scenarios=None):
    """Stores generated execution blueprints along with adaptive learning gaps."""
    try:
        embedding = generate_embedding(requirement)

        metadata = {
            "output": output
        }

        # Format and bound missing learning scenarios safely
        if missing_scenarios:
            metadata["missing"] = " || ".join(missing_scenarios[:10])

        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[requirement],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        logger.info("Memory Store: Successfully vector-indexed requirements.")

    except Exception as e:
        logger.error(f"[MEMORY STORE ERROR] Execution failed: {e}", exc_info=True)


def retrieve_similar(requirement: str, top_k=2):
    """Retrieves high-confidence historical context match records."""
    try:
        embedding = generate_embedding(requirement)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        if not results or not results.get("documents") or not results["documents"][0]:
            return []

        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]

        combined = []
        for doc, meta in zip(docs, metas):
            if not meta:
                continue
            output = meta.get("output", "")
            combined.append(f"Requirement: {doc}\nOutput: {output[:300]}")

        return combined

    except Exception as e:
        logger.error(f"[MEMORY RETRIEVE ERROR] Vector lookup failed: {e}", exc_info=True)
        return []


def retrieve_learning(requirement: str, top_k=2):
    """Extracts historically isolated missing logical validation gaps."""
    try:
        embedding = generate_embedding(requirement)

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        if not results or not results.get("metadatas") or not results["metadatas"][0]:
            return []

        metas = results["metadatas"][0]
        learned_gaps = []

        for meta in metas:
            if not meta:
                continue
            missing = meta.get("missing")
            if missing:
                parts = missing.split("||")
                learned_gaps.extend([p.strip() for p in parts if p.strip()])

        # Deduplicate results cleanly
        return list(set(learned_gaps))

    except Exception as e:
        logger.error(f"[MEMORY LEARNING ERROR] Gap analysis failed: {e}", exc_info=True)
        return []