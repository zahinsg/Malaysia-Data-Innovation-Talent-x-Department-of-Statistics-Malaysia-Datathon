import sys
import torch
from ultralytics import YOLO

# Patch for older models
# Attempt to map missing modules to existing ones
try:
    import ultralytics.nn.modules.block
except ImportError:
    # If block module is missing, try to map it to conv or create a dummy
    # In newer ultralytics, some blocks might be in different places
    # But often it's just a path issue.
    # Let's try to find where C2f and Bottleneck are.
    import ultralytics.nn.modules as modules
    if not hasattr(modules, 'block'):
        # Create a dummy module structure
        from types import ModuleType
        block = ModuleType('ultralytics.nn.modules.block')
        sys.modules['ultralytics.nn.modules.block'] = block
        
        # Map common classes that might be looked for
        if hasattr(modules, 'C2f'):
            block.C2f = modules.C2f
        if hasattr(modules, 'Bottleneck'):
            block.Bottleneck = modules.Bottleneck
        if hasattr(modules, 'SPPF'):
            block.SPPF = modules.SPPF
        if hasattr(modules, 'C3'):
            block.C3 = modules.C3
            
    print("Applied sys.modules patch for ultralytics.nn.modules.block")

try:
    print("Attempting to load model...")
    model = YOLO('models/ppe_detection.pt')
    print("✅ Model loaded successfully!")
    
    # Try to export it to update the internal structure
    print("Saving updated model...")
    model.save('models/ppe_detection_fixed.pt')
    print("✅ Model saved as ppe_detection_fixed.pt")
    
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    import traceback
    traceback.print_exc()
