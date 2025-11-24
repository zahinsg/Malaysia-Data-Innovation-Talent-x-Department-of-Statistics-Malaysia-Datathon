import cv2
import numpy as np
import base64
import os
import pandas as pd
import time
import requests
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from deepface import DeepFace
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

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
TRAINING_DATASET_DIR = os.path.join(DATA_DIR, "training_dataset")
WORKERS_CSV = os.path.join(DATA_DIR, "workers.csv")

FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_detection.pt")
PPE_MODEL_PATH = os.path.join(MODELS_DIR, "ppe_detection.pt")

# Required PPE classes
REQUIRED_PPE = {"helmet", "safety-vest"}

# Telegram Configuration
TELEGRAM_BOT_TOKEN = #bot token
TELEGRAM_CHAT_ID = #chat id 
ALERT_DELAY_SECONDS = 20

# --- Global State ---
face_model = None
ppe_model = None

def load_models():
    global face_model, ppe_model
    # Load Face Model
    try:
        print("Loading Face Detection Model...")
        face_model = YOLO(FACE_MODEL_PATH)
    except Exception as e:
        print(f"⚠️ Error loading custom Face model: {e}")
        print("🔄 Switching to standard YOLOv8n model for Face Detection (Fallback)...")
        face_model = YOLO("yolov8n.pt")

    # Load PPE Model
    try:
        print("Loading PPE Detection Model...")
        ppe_model = YOLO(PPE_MODEL_PATH)
        print("✅ Custom PPE Model loaded successfully!")
    except Exception as e:
        print(f"⚠️ Error loading custom PPE model: {e}")
        print("🔄 Switching to standard YOLOv8n model for PPE Detection (Fallback)...")
        ppe_model = YOLO("yolov8n.pt")
    
    print("Models loaded.")

# Initialize models on startup
load_models()

def get_worker_name(worker_id):
    """
    Look up worker name from CSV based on ID.
    Assumes ID is part of the filename/identity string.
    """
    if not os.path.exists(WORKERS_CSV):
        return "Unknown"
    
    try:
        df = pd.read_csv(WORKERS_CSV)
        # Clean up column names if needed
        df.columns = [c.strip() for c in df.columns]
        
        # Adjust these column names based on your actual CSV structure
        if "ID num" in df.columns and "full name" in df.columns:
            df["ID num"] = df["ID num"].astype(str).str.strip()
            worker_id = str(worker_id).strip()
            match = df[df["ID num"] == worker_id]
            if not match.empty:
                return match.iloc[0]["full name"]
    except Exception as e:
        print(f"Error reading CSV: {e}")
        
    return "Unknown"

def send_telegram_alert(image, missing_items):
    """
    Send a photo and message to Telegram.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        msg = f"🚨 PPE Missing Alert!\nMissing: {', '.join(missing_items)}"
        filename = "ppe_alert.jpg"
        # Save temp image
        cv2.imwrite(filename, image)
        
        with open(filename, 'rb') as photo:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            files = {'photo': photo}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': msg}
            response = requests.post(url, files=files, data=data)
            print(f"[INFO] Telegram alert sent. Response: {response.status_code}")
            
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def process_frame(frame, state):
    """
    Main pipeline:
    1. Detect Face -> Recognize User (Every N frames)
    2. If User Recognized -> Detect PPE (Every frame)
    3. Return Status
    """
    response = {
        "status": "idle",
        "message": "Initializing...",
        "user": state.get("user_name"),
        "missing_ppe": [],
        "annotated_frame": None
    }

    # --- Stage 1: Identification ---
    # Detect faces using YOLO (Always run this to get the box)
    face_results = face_model(frame, verbose=False)
    
    detected_face_crop = None
    face_box = None
    
    # Get the largest face
    largest_area = 0
    for result in face_results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area > largest_area:
                largest_area = area
                face_box = (x1, y1, x2, y2)
                detected_face_crop = frame[y1:y2, x1:x2]

    # Decide whether to run DeepFace Recognition
    state["frame_count"] += 1
    should_recognize = (state["user_name"] == "Unknown" or state["user_name"] is None) or (state["frame_count"] % 10 == 0)

    user_name = state.get("user_name", "Unknown")

    if detected_face_crop is not None and should_recognize:
        try:
            # Save temp file for DeepFace
            temp_face_path = os.path.join(BASE_DIR, "temp_face.jpg")
            cv2.imwrite(temp_face_path, detected_face_crop)

            # DeepFace Recognition
            dfs = DeepFace.find(
                img_path=temp_face_path,
                db_path=TRAINING_DATASET_DIR,
                model_name="ArcFace",
                distance_metric="cosine",
                enforce_detection=False,
                detector_backend="opencv",
                silent=True
            )
            
            new_user_name = "Unknown"
            if len(dfs) > 0 and not dfs[0].empty:
                match_path = dfs[0].iloc[0]["identity"]
                filename = os.path.basename(match_path)
                name_part = os.path.splitext(filename)[0]
                
                if "_" in name_part:
                    user_id = name_part.split("_")[-1]
                    found_name = get_worker_name(user_id)
                    if found_name == "Unknown":
                         found_name = name_part.split("_")[0]
                    new_user_name = found_name
                else:
                    new_user_name = name_part
            
            # Update state
            state["user_name"] = new_user_name
            user_name = new_user_name

        except Exception as e:
            print(f"Recognition Error: {e}")
            pass
    elif detected_face_crop is None:
        state["user_name"] = "Unknown"
        user_name = "Unknown"

    # Logic Branching
    if user_name == "Unknown" or detected_face_crop is None:
        response["status"] = "Unknown User"
        response["message"] = "Please look at the camera." if detected_face_crop is None else "User not recognized."
        response["user"] = None
        
        if face_box:
            x1, y1, x2, y2 = face_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, "Unknown", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    else:
        # --- Stage 2: Safety Check ---
        response["user"] = user_name
        
        # Run PPE Detection (Always run this)
        ppe_results = ppe_model(frame, verbose=False, conf=0.25)
        
        detected_ppe = set()
        
        for result in ppe_results:
            names = result.names
            for box in result.boxes:
                cls = int(box.cls[0])
                class_name = names[cls]
                detected_ppe.add(class_name)
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = (0, 255, 0) if class_name in REQUIRED_PPE else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, class_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        missing = []
        for item in REQUIRED_PPE:
            if item not in detected_ppe:
                missing.append(item)
        
        response["missing_ppe"] = missing
        
        # Telegram Alert Logic
        current_time = time.time()
        if len(missing) > 0:
            if state.get("last_missing_time") is None:
                state["last_missing_time"] = current_time
            elif current_time - state["last_missing_time"] >= ALERT_DELAY_SECONDS:
                # Trigger Alert
                threading.Thread(target=send_telegram_alert, args=(frame.copy(), missing)).start()
                state["last_missing_time"] = current_time # Reset timer
        else:
            state["last_missing_time"] = None

        if len(missing) == 0:
            response["status"] = "Access Granted"
            response["message"] = f"Welcome, {user_name}. Safety Clear."
            if face_box:
                x1, y1, x2, y2 = face_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                cv2.putText(frame, user_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        else:
            response["status"] = "Access Denied"
            response["message"] = f"Hi {user_name}, missing: {', '.join(missing)}"
            if face_box:
                x1, y1, x2, y2 = face_box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(frame, user_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # Encode frame
    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    response["annotated_frame"] = jpg_as_text
    
    return response

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    # Client State
    state = {
        "frame_count": 0,
        "user_name": "Unknown",
        "last_missing_time": None
    }
    
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

            # Process with state
            result = process_frame(frame, state)
            
            # Send back JSON
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
