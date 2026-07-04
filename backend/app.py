from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI(title="Hackathon API POC")

# Enable CORS so the frontend can call this backend easily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

@app.get("/items")
def get_items():
    # Load dummy dataset from seeds.json
    seeds_path = os.path.join(os.path.dirname(__file__), "seeds.json")
    try:
        with open(seeds_path, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []
