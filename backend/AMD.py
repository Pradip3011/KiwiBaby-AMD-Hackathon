import torch
# Check if HIP is available
if torch.backends.hip.is_available():
    print(f"AMD HIP is available! Device: {torch.cuda.get_device_name(0)}")
else:
    print("HIP not detected. Check PATH environment variables.")