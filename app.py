from fastapi import FastAPI
from pydantic import BaseModel
import random
import hashlib
import time

app = FastAPI(title="Instagram Giveaway Draw")

class DrawRequest(BaseModel):
    participants: list[str]
    rules: str | None = None
    winners_count: int = 1  # počet výherců, výchozí = 1

@app.post("/draw")
def draw(req: DrawRequest):
    if not req.participants:
        return {"error": "No participants provided"}
    if req.winners_count < 1:
        return {"error": "Winners count must be at least 1"}
    if req.winners_count > len(req.participants):
        return {"error": "Winners count cannot exceed number of participants"}

    # náhodný seed (pro audit)
    seed = str(time.time())
    random.seed(seed)

    # náhodný výběr výherců bez opakování
    winners = random.sample(req.participants, req.winners_count)

    return {
        "timestamp": int(time.time()),
        "seed_hash": hashlib.sha256(seed.encode()).hexdigest(),
        "rules": req.rules,
        "participants_count": len(req.participants),
        "winners_count": req.winners_count,
        "winners": winners

# --- zbytek tvého kódu nech tak, jak je ---

import os

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
  
  }
