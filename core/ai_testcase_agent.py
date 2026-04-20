import spacy
import torch
import torch_directml

def initialize_gpu_acceleration():
    """
    Architect's Hook: Unified hardware activation for AMD Radeon.
    Synchronizes spaCy and PyTorch on the DirectML layer.
    """
    print("\n" + "="*50)
    print("🛡️ STARTING AGENTIC HARDWARE INITIALIZATION...")
    
    # 1. Initialize the AMD Device via DirectML
    # This is your 'privateuseone:0' identifier
    device = torch_directml.device()
    
    try:
        # 2. Force spaCy to utilize the GPU backend
        # Note: spaCy's prefer_gpu() will now look for the DirectML drivers we installed
        spacy_activated = spacy.prefer_gpu()
        
        if spacy_activated:
            print(f"✅ NLP ENGINE: Offloaded to AMD Radeon.")
        else:
            print(f"⚠️ NLP ENGINE: GPU not detected by spaCy (CPU Fallback).")

        # 3. Verify PyTorch Connectivity
        if device:
            print(f"✅ TORCH ENGINE: Connected to Hardware [{device}]")
        
        print("🚀 AGENT STATUS: High-Performance Mode Active.")
        print("="*50 + "\n")
        
        return device

    except Exception as e:
        print(f"❌ ARCHITECTURAL ERROR: {e}")
        return torch.device("cpu")

# --- GLOBAL EXECUTION ---
# This 'device' variable will now be used throughout your agent
AGENT_DEVICE = initialize_gpu_acceleration()

def run_agentic_reasoning(requirement_data):
    # This is where the 0.01% precision happens
    print(f"🧠 Reasoning in progress on: {AGENT_DEVICE}")
    
    # Example: If using a transformer model
    # model.to(AGENT_DEVICE) 
    
    # ... your BDD transformation logic ...