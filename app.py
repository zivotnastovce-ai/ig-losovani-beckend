import os
import re
import random
import hashlib
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from time import time

app = FastAPI(title="Instagram Giveaway Smart Backend")

# --- Datové modely ---
class DrawRequest(BaseModel):
    url: str
    winners_count: int = 1
    rules: list[str] = []

# --- Pomocná funkce: stáhne komentáře ---
def get_comments_from_instagram(post_url: str):
    """
    🔹 Simulované získání komentářů.
    Pokud nemáš přístup k API, použij nahraný seznam nebo web scraping.
    """
    # Tohle je MOCK — pro testování použijme simulovaná data
    # V reálné verzi se sem připojí Instagram Graph API nebo scraper
    fake_comments = [
        "Tahle soutěž je top! @michal @jirka",
        "Chci vyhrát @karel",
        "Zkouším štěstí @lucie",
        "Bez označení",
        "Další pokus @ondra @petr",
    ]
    return fake_comments

# --- Hlavní endpoint ---
@app.post("/draw")
def draw(req: DrawRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="Instagram URL je povinná.")
    
    # 1️⃣ Získání komentářů
    comments = get_comments_from_instagram(req.url)
    if not comments:
        raise HTTPException(status_code=400, detail="Žádné komentáře nebyly nalezeny.")
    
    # 2️⃣ Ověření podmínky označení kamaráda
    valid_participants = []
    tag_required = any(r in req.rules for r in ["tag", "označ kamaráda"])
    
    for comment in comments:
        # Najdi všechny tagy typu @jmeno
        tags = re.findall(r"@([A-Za-z0-9_.]+)", comment)
        
        if tag_required:
            if len(tags) >= 1:  # musí označit alespoň 1 člověka
                valid_participants.append(comment)
        else:
            valid_participants.append(comment)
    
    if not valid_participants:
        raise HTTPException(status_code=400, detail="Nikdo nesplnil podmínky soutěže.")

    # 3️⃣ Náhodné losování výherců
    winners_count = min(req.winners_count, len(valid_participants))
    winners = random.sample(valid_participants, winners_count)

    # 4️⃣ Výsledek
    return {
        "timestamp": int(time()),
        "participants_total": len(comments),
        "qualified": len(valid_participants),
        "winners_count": winners_count,
        "winners": winners,
        "rules": req.rules
    }

# --- Spuštění na Renderu ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
