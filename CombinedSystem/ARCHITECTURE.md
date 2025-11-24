# System Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│                     http://localhost:5173                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐       ┌──────────────┐      ┌──────────────┐ │
│  │   Camera     │  -->  │   Canvas     │ -->  │  WebSocket   │ │
│  │  getUserMedia│       │ toBase64()   │      │   Client     │ │
│  └──────────────┘       └──────────────┘      └──────┬───────┘ │
│                                                        │          │
└────────────────────────────────────────────────────────┼─────────┘
                                                         │
                                        WebSocket ws://localhost:8000/ws
                                                         │
┌────────────────────────────────────────────────────────┼─────────┐
│                                                        │          │
│  ┌──────────────┐                            ┌────────▼───────┐ │
│  │  WebSocket   │  <-- JSON Response -----   │   WebSocket  │ │
│  │   Server     │                            │   Handler    │ │
│  └──────────────┘                            └────────┬─────┘ │
│                                                        │        │
│                    BACKEND (FastAPI)                  │        │
│                  http://localhost:8000                │        │
│                                                        ▼        │
│  ┌────────────────────────────────────────────────────────────┐│
│  │              process_frame(frame)                          ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │ STAGE 1: IDENTIFICATION                              │ ││
│  │  │  1. YOLO Face Detection (face_detection.pt)         │ ││
│  │  │  2. DeepFace Recognition (ArcFace model)            │ ││
│  │  │  3. Lookup in workers.csv                           │ ││
│  │  │                                                      │ ││
│  │  │  IF Unknown --> Return "Unknown User"               │ ││
│  │  │  IF Recognized --> Proceed to Stage 2 ↓             │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  │  ┌──────────────────────────────────────────────────────┐ ││
│  │  │ STAGE 2: SAFETY CHECK                               │ ││
│  │  │  4. YOLO PPE Detection (ppe_detection.pt)           │ ││
│  │  │  5. Check Required PPE: {helmet, safety-vest}       │ ││
│  │  │                                                      │ ││
│  │  │  IF All Present --> "Access Granted"                │ ││
│  │  │  IF Missing --> "Access Denied + Missing Items"     │ ││
│  │  └──────────────────────────────────────────────────────┘ ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Models/    │  │    Data/     │  │   Dependencies       │ │
│  │              │  │              │  │                      │ │
│  │ face_det.pt  │  │ workers.csv  │  │ - ultralytics        │ │
│  │ ppe_det.pt   │  │ training_    │  │ - deepface           │ │
│  │              │  │ dataset/     │  │ - opencv-python      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Sequential Logic Flow

```
User approaches camera
         │
         ▼
┌─────────────────────┐
│ Frame Captured      │
│ (10 FPS)            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STAGE 1: Who is this person?        │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ YOLO detects face in frame      │ │
│ └─────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│ ┌─────────────────────────────────┐ │
│ │ DeepFace matches face to DB     │ │
│ └─────────────┬───────────────────┘ │
│               │                      │
│          ┌────┴────┐                │
│          │         │                │
│      Match?     No Match            │
│          │         │                │
└──────────┼─────────┼────────────────┘
           │         │
       YES │         │ NO
           │         ▼
           │    ┌──────────────────┐
           │    │ "Unknown User"   │
           │    │ Return & Stop    │
           │    └──────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ STAGE 2: Is this worker safe?       │
│                                      │
│ Worker: [Name]                       │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ YOLO detects PPE in frame       │ │
│ │ Classes: helmet, vest, etc.     │ │
│ └─────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│ ┌─────────────────────────────────┐ │
│ │ Check Required PPE              │ │
│ │ Required: {helmet, safety-vest} │ │
│ │ Detected: {helmet, ____}        │ │
│ └─────────────┬───────────────────┘ │
│               │                      │
│          ┌────┴────┐                │
│          │         │                │
│     All PPE?   Missing?             │
│          │         │                │
│      ┌───┘         └───┐            │
│      │                 │            │
└──────┼─────────────────┼────────────┘
       │                 │
       ▼                 ▼
┌──────────────┐  ┌───────────────────┐
│ ACCESS       │  │ ACCESS DENIED     │
│ GRANTED      │  │                   │
│              │  │ "Hi [Name],       │
│ "Welcome,    │  │ please put on     │
│ [Name] -     │  │ your helmet"      │
│ Safety Clear"│  │                   │
└──────────────┘  └───────────────────┘
       │                 │
       └────────┬────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Send JSON Response    │
    │ + Annotated Frame     │
    │ to Frontend           │
    └───────────────────────┘
                │
                ▼
    ┌───────────────────────┐
    │ Display on Screen     │
    │ - Status Badge        │
    │ - Worker Info         │
    │ - Missing PPE List    │
    │ - Annotated Video     │
    └───────────────────────┘
```

## Example Responses

### Scenario 1: Unknown Person
```json
{
  "status": "Unknown User",
  "message": "User not recognized.",
  "user": null,
  "missing_ppe": [],
  "annotated_frame": "base64..."
}
```

### Scenario 2: Worker Without PPE
```json
{
  "status": "Access Denied",
  "message": "Hi Zatul, missing: helmet, safety-vest",
  "user": "Zatul",
  "missing_ppe": ["helmet", "safety-vest"],
  "annotated_frame": "base64..."
}
```

### Scenario 3: Worker With Complete PPE
```json
{
  "status": "Access Granted",
  "message": "Welcome, Zatul. Safety Clear.",
  "user": "Zatul",
  "missing_ppe": [],
  "annotated_frame": "base64..."
}
```
