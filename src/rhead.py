from fastapi import FastAPI, UploadFile, File
import sqlite3
import hashlib
import time

app = FastAPI()

# DATABASE: The Hard Audit for Scientific Sources
def setup_db():
    db = sqlite3.connect("data/sources.db")
    db.execute("CREATE TABLE IF NOT EXISTS sources (id TEXT PRIMARY KEY, filename TEXT, hash TEXT, processed_at REAL)")
    db.execute("CREATE TABLE IF NOT EXISTS conversation_history (id TEXT PRIMARY KEY, step_index INTEGER, prompt TEXT, result TEXT, rigor_score REAL)")
    db.commit()
    return db

@app.post("/upload")
async def upload_source(file: UploadFile = File(...)):
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Store source metadata
    db = setup_db()
    db.execute("INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?)", 
               (str(time.time()), file.filename, file_hash, time.time()))
    db.commit()
    
    return {"status": "ingested", "filename": file.filename, "hash": file_hash}

@app.get("/history/undo")
def undo_step():
    db = setup_db()
    # Simple logic to drop the latest step
    db.execute("DELETE FROM conversation_history WHERE id = (SELECT max(id) FROM conversation_history)")
    db.commit()
    return {"status": "rewound"}

# Add health and other endpoints...
