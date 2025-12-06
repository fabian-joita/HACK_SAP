# backend/backend.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow frontend (Vite, React) to access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/run-main")
def run_main():
    try:
        result = subprocess.run(
            ["python3", "-m", "rotables.main"],
            cwd="../",     # Run inside HACK_SAP
            capture_output=True,
            text=True,
            check=True
        )

        return {"success": True, "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
