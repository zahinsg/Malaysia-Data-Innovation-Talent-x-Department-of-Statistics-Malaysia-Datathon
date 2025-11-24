# Construction Safety System
AI-Powered Worker Identification & PPE Compliance Check

## Overview
This system combines **Face Recognition** and **PPE Detection** into a single web application for construction site safety management.

### Features
- **Stage 1**: Face recognition to identify workers
- **Stage 2**: PPE detection to verify safety compliance (Helmet + Vest)
- **Real-time feedback** via WebSocket connection
- **Modern UI** built with React + Tailwind CSS

---

## Project Structure

```
CombinedSystem/
├── backend/
│   ├── main.py                      # FastAPI server with WebSocket
│   ├── requirements.txt             # Python dependencies
│   ├── models/
│   │   ├── face_detection.pt        # YOLO model for face detection
│   │   └── ppe_detection.pt         # YOLO model for PPE detection
│   └── data/
│       ├── workers.csv              # Worker database (ID num, full name)
│       └── training_dataset/        # Face recognition training images
│
└── frontend/
    ├── src/
    │   ├── App.jsx                  # Main React component with camera
    │   └── index.css                # Tailwind styles
    ├── package.json
    ├── tailwind.config.js
    └── postcss.config.js
```

---

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd CombinedSystem/backend
```

2. Create virtual environment (optional but recommended):
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify files:
   - `models/face_detection.pt` exists
   - `models/ppe_detection.pt` exists
   - `data/workers.csv` exists with columns: `ID num`, `full name`
   - `data/training_dataset/` contains worker face images (format: `Name_ID.jpg`)

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd CombinedSystem/frontend
```

2. Install dependencies:
```bash
npm install
```

---

## Running the Application

### 1. Start Backend Server

```bash
cd backend
python main.py
```

Server runs on: `http://localhost:8000`

### 2. Start Frontend (in a new terminal)

```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:5173`

### 3. Open Browser

Navigate to `http://localhost:5173` and grant camera permissions.

---

## How It Works

### Backend Logic Flow (`main.py`)

```python
def process_frame(frame):
    # Stage 1: Identification
    1. Detect face using YOLO (face_detection.pt)
    2. Recognize worker using DeepFace (ArcFace model)
    3. Look up worker name from workers.csv
    
    # If Unknown:
    return "Unknown User"
    
    # If Recognized:
    # Stage 2: Safety Check
    4. Run PPE detection (ppe_detection.pt)
    5. Check for required PPE: helmet + safety-vest
    
    # If all PPE present:
    return "Access Granted: [Name] - Safety Clear"
    
    # If PPE missing:
    return "Access Denied: [Name] - Missing [Items]"
```

### Frontend (`App.jsx`)

- **Camera Access**: Uses `getUserMedia()` to access webcam
- **Frame Capture**: Captures frames at 10 FPS using Canvas API
- **WebSocket Communication**: Sends base64-encoded frames to backend
- **Real-time Display**: Shows annotated video with detection results
- **Status Panel**: Displays worker info, PPE status, and instructions

---

## API Endpoints

### WebSocket: `/ws`

**Client sends**: Base64-encoded JPEG frame

**Server responds**: JSON object
```json
{
  "status": "Access Granted" | "Access Denied" | "Unknown User",
  "message": "Welcome, John - Safety Clear",
  "user": "John Doe",
  "missing_ppe": ["helmet", "safety-vest"],
  "annotated_frame": "base64_encoded_image"
}
```

---

## Configuration

### Backend (`main.py`)

**Model Paths**:
- `FACE_MODEL_PATH`: Path to face detection YOLO model
- `PPE_MODEL_PATH`: Path to PPE detection YOLO model

**Required PPE** (line 31):
```python
REQUIRED_PPE = {"helmet", "safety-vest"}
```
Adjust based on your PPE model's class names.

**Worker Database**:
- CSV format: `ID num, full name, Group` (optional)
- Training images: `Name_ID.jpg` format in `training_dataset/`

### Frontend (`App.jsx`)

**WebSocket URL** (line 52):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws')
```

**Frame Rate** (line 60):
```javascript
setInterval(() => {
  captureAndSendFrame(ws)
}, 100) // 100ms = 10 FPS
```

---

## Customization

### Add More PPE Requirements

Edit `backend/main.py` line 31:
```python
REQUIRED_PPE = {"helmet", "safety-vest", "gloves", "face-mask"}
```

### Change UI Colors

Edit `frontend/tailwind.config.js`:
```javascript
colors: {
  primary: '#00ADB5',    // Teal
  secondary: '#FFD369',  // Gold
  dark: '#222831',       // Dark background
  darker: '#393E46',     // Card background
}
```

### Update Messages

Edit response messages in `backend/main.py`:
- Line 166: Unknown user message
- Line 190: Access granted message  
- Line 197: Access denied message

---

## Troubleshooting

### Backend Issues

**Models not loading**:
- Verify `.pt` files exist in `models/` directory
- Check file paths in `main.py`

**DeepFace errors**:
- Ensure `training_dataset/` has worker images
- Images should be clear face photos (JPEG format)

**CSV errors**:
- Check `workers.csv` has correct column names
- Ensure no special characters in IDs

### Frontend Issues

**Camera not working**:
- Grant browser camera permissions
- Use HTTPS or localhost only
- Check if camera is being used by another app

**WebSocket connection failed**:
- Verify backend is running on port 8000
- Check firewall settings
- Ensure no port conflicts

**No video display**:
- Check browser console for errors
- Verify WebSocket is receiving responses
- Check `annotated_frame` is being sent from backend

---

## Dependencies

### Backend (Python)
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket support
- `ultralytics` - YOLO models
- `deepface` - Face recognition
- `opencv-python` - Image processing
- `pandas` - CSV handling
- `tf-keras` - DeepFace backend

### Frontend (Node.js)
- `react` - UI framework
- `vite` - Build tool
- `tailwindcss` - CSS framework
- `lucide-react` - Icons

---

## Example Usage

### Scenario: Worker "Zatul" arrives at construction site

1. Zatul stands in front of camera
2. System detects face → recognizes as "Zatul" (from workers.csv)
3. System checks PPE:
   - ✅ Helmet detected
   - ❌ Safety vest NOT detected
4. Display: **"Access Denied: Zatul - Missing safety-vest"**
5. Zatul puts on safety vest
6. System re-checks:
   - ✅ Helmet detected
   - ✅ Safety vest detected
7. Display: **"Access Granted: Zatul - Safety Clear"**

---

## License
MIT License - Feel free to modify and use for your projects.

## Credits
- Built with FastAPI, React, YOLO, and DeepFace
- Based on Malaysia Data Innovation Talent Datathon project
- Worker safety compliance automation
