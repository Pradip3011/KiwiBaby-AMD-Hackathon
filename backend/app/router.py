import re
import time
import logging
from .config import settings

logger = logging.getLogger("kiwibaby.router")

def evaluate_requirement_complexity(prompt: str) -> dict:
    """
    High-speed linguistic and lexical structural routing layer.
    Executes in < 2ms on CPU platforms to determine target execution tier.
    """
    start_time = time.perf_counter()
    
    # Early out for malformed or empty inputs
    if not prompt or not prompt.strip():
        return {
            "destination": "LOCAL_CPU",
            "tier": 1,
            "latency_ms": (time.perf_counter() - start_time) * 1000,
            "requires_compression": False,
            "reason": "Empty or malformed payload fallback."
        }

    clean_text = prompt.lower()
    word_count = len(clean_text.split())
    
    # 🧠 High-Complexity Structural Indicators (Track 1 Performance Targets)
    high_complexity_keywords = [
        "state machine", "race condition", "biometric", "compliance", 
        "pci dss", "gdpr", "multi-tenant", "oauth", "jwt architecture", 
        "microservices", "async queue", "deadlock", "concurrency"
    ]
    
    # Match criteria
    has_high_complexity_terms = any(term in clean_text for term in high_complexity_keywords)
    
    # Count logical branch conditions (if, when, then, must, should, ensure)
    condition_density = len(re.findall(r"\b(if|when|then|must|should|ensure|verify)\b", clean_text))
    
    # 📊 Decision Matrix (Minimizing tokens while protecting target accuracy boundaries)
    if has_high_complexity_terms or word_count > 150 or condition_density >= 5:
        destination = "REMOTE_AMD"
        tier = 3
        requires_compression = False
        reason = "High logical complexity or long context profile requires full model precision."
        
    elif word_count > 45 or condition_density >= 2:
        destination = "COMPRESSED_REMOTE"
        tier = 2
        requires_compression = True
        reason = "Medium structural weight. Passing to remote engine via token compression."
        
    else:
        destination = "LOCAL_CPU"
        tier = 1
        requires_compression = False
        reason = "Simple, direct requirement. Resolvable on local resource with zero cloud cost."

    latency_ms = (time.perf_counter() - start_time) * 1000
    
    # Log warning if routing engine exceeds the strict hackathon threshold
    if latency_ms > settings.ROUTER_OVERHEAD_THRESHOLD_MS:
        logger.warning(f"Router overhead spiked: {latency_ms:.2f}ms exceeds {settings.ROUTER_OVERHEAD_THRESHOLD_MS}ms target.")
        
    return {
        "destination": destination,
        "tier": tier,
        "latency_ms": round(latency_ms, 4),
        "requires_compression": requires_compression,
        "reason": reason
    }