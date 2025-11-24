@echo off
echo Starting Backend Server...
cd backend
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)
python main.py
