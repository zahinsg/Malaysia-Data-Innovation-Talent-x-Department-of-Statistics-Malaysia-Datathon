import cv2
import numpy as np
import base64
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Starting Construction Safety System...")
print("✅ FastAPI server initialized")

def process_frame_simple(frame):
    """
    Simplified processing for testing
    """
    response = {
        "status": "idle",
        "message": "System is ready. Testing mode activated.",
        "user": None,
        "missing_ppe": [],
        "annotated_frame": None
    }
    
    # Add simple text overlay to test
    cv2.putText(frame, "Construction Safety System - DEMO MODE", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, "Backend Connected Successfully!", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # Encode frame back to base64 for display
    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    response["annotated_frame"] = jpg_as_text
    response["status"] = "Demo Mode"
    response["message"] = "Backend is connected! AI models will be loaded next."
    
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client connected to WebSocket")
    try:
        while True:
            data = await websocket.receive_text()
            
            # Decode image
            if "," in data:
                header, encoded = data.split(",", 1)
            else:
                encoded = data
                
            image_data = base64.b64decode(encoded)
            np_arr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue

            # Process
            result = process_frame_simple(frame)
            
            # Send back JSON
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print("❌ Client disconnected")
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            await websocket.close()
        except:
            pass

@app.get("/")
async def root():
    return {"message": "Construction Safety System API", "status": "running", "version": "1.0-demo"}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🏗️  CONSTRUCTION SAFETY SYSTEM - BACKEND SERVER")
    print("="*60)
    print("📡 Starting server on http://0.0.0.0:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
