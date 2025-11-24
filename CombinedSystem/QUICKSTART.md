# 🚀 Quick Start Guide

## One-Time Setup

```bash
cd CombinedSystem
setup.bat
```

## Running the System

### Option 1: Use Batch Scripts (Recommended)

**Terminal 1:**
```bash
start_backend.bat
```

**Terminal 2:**
```bash
start_frontend.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Access the Application

Open browser: **http://localhost:5173**

---

## 🎯 Quick Test

1. Click **"Start Safety Check"**
2. Allow camera access
3. Look at camera
4. System will:
   - Identify you (or say "Unknown")
   - Check your PPE
   - Show "Access Granted" or "Access Denied"

---

## 🔧 Quick Configuration

### Add a Worker

**File:** `backend/data/workers.csv`
```csv
ID num,full name,Group
2025001,John Doe,Construction
```

**Training Image:** `backend/data/training_dataset/John_2025001.jpg`

### Change Required PPE

**File:** `backend/main.py` (line 31)
```python
REQUIRED_PPE = {"helmet", "safety-vest"}  # Add more: "gloves", "goggles"
```

---

## ⚡ Key Shortcuts

- **Ctrl+C** in terminal: Stop server
- **F12** in browser: Open DevTools
- **Ctrl+Shift+I**: Inspect WebSocket messages

---

## 📊 System Check

### Backend Running?
Check terminal for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend Running?
Check terminal for:
```
VITE v7.x.x  ready in XXXms
➜  Local:   http://localhost:5173/
```

### WebSocket Connected?
Browser console should show:
```
Connected to backend
```

---

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not working | Allow camera permissions in browser |
| WebSocket fails | Ensure backend is running on port 8000 |
| Unknown user | Add worker to CSV + training image |
| PPE not detected | Adjust model confidence in main.py |
| Port in use | Kill process or change port |

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | Server logic |
| `frontend/src/App.jsx` | Camera UI |
| `backend/data/workers.csv` | Worker database |
| `backend/models/*.pt` | AI models |
| `backend/data/training_dataset/` | Face images |

---

## 🎨 Customization Quick Edits

### Change UI Colors
`frontend/tailwind.config.js`:
```javascript
colors: {
  primary: '#00ADB5',    // Main accent
  secondary: '#FFD369',  // Secondary accent
}
```

### Change Messages
`backend/main.py`:
- Line 166: Unknown user message
- Line 190: Access granted
- Line 197: Access denied

### Adjust Frame Rate
`frontend/src/App.jsx` (line 60):
```javascript
}, 100) // 100ms = 10 FPS
```

---

## 📞 Need Help?

- **Full Documentation:** `README.md`
- **Architecture:** `ARCHITECTURE.md`
- **All Features:** `DELIVERABLES.md`

---

**That's it! You're ready to go! 🎉**
