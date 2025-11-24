import shutil
import os
import sys
import torch
from ultralytics import YOLO

# 1. Skip copy for now, just test existing face model
dest = "models/face_detection.pt"

# 2. Try to load it
print(f"Attempting to load model {dest}...")
try:
    model = YOLO(dest)
    print("✅ Face Model loaded successfully WITHOUT patch!")
except Exception as e:
    print(f"⚠️ Load failed: {e}")
    print("Applying patch...")
    
    # Apply patch
    try:
        # Try to import block module
        try:
            import ultralytics.nn.modules.block as block
        except ImportError:
            # If block module doesn't exist, try to create it or find where it is
            import ultralytics.nn.modules as modules
            if not hasattr(modules, 'block'):
                from types import ModuleType
                block = ModuleType('ultralytics.nn.modules.block')
                sys.modules['ultralytics.nn.modules.block'] = block
            else:
                block = modules.block
                
        print(f"Available in block: {[x for x in dir(block) if not x.startswith('_')]}")
        
        # Try to patch ELAN1
        if not hasattr(block, 'ELAN1'):
            print("Patching ELAN1...")
            # Map to C2f or RepNCSPELAN4 if available
            if hasattr(block, 'RepNCSPELAN4'):
                block.ELAN1 = block.RepNCSPELAN4
                print("Mapped ELAN1 to RepNCSPELAN4")
            elif hasattr(block, 'C2f'):
                block.ELAN1 = block.C2f
                print("Mapped ELAN1 to C2f")
            else:
                # Create dummy
                class ELAN1(torch.nn.Module):
                    def __init__(self, *args, **kwargs):
                        super().__init__()
                    def forward(self, x):
                        return x
                block.ELAN1 = ELAN1
                print("Mapped ELAN1 to Dummy Class")

        # Try loading again
        model = YOLO(dest)
        print("✅ Face Model loaded successfully WITH patch!")
        
    except Exception as e2:
        print(f"❌ Failed to load even with patch: {e2}")
        import traceback
        traceback.print_exc()
