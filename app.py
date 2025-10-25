import re, random, httpx, time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup

app = FastAPI(title="Instagram Giveaway (no login version)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELY
# =========================
class Rules(BaseModel):
    min_tags: int = 0
    require_keyword: Optional[str] = None
    disqualify_duplicates: bool = True

class DrawRequest(BaseModel):
    url: str
    rules: Rules
    winners_count: int = 1

class DrawResult(BaseModel):
    timestamp: int
    total_comments: int
    valid_candidates: int
    winners: List[str]
    audit: List[dict]

# =========================
# FUNKCE
# =========================
def extract_usernames_from_comment(text: str):
    """Najde všechna @označení v komentáři."""
    return list({m.group(1).lower() for m in re.finditer(r'@([A-Za-z0-9._]+)', text)})

async def fetch_instagram_comments(post_url: str) -> List[dict]:
    """Získá komentáře z veřejného Instagram postu (bez přihlášení)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        r = await client.get(post_url, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Nepodařilo se načíst příspěvek.")

    soup = BeautifulSoup(r.text, "html.parser")
    comments = []

    # Instagram často ukládá komentáře jako JSON ve scriptu
    scripts = soup.find_all("script", type="application/ld+json")
    for s in scripts:
        text = s.text
        if '"comment"' in text:
            match = re.findall(r'"author":\s*{\s*"name":\s*"([^"]+)"[^}]*},\s*"text":\s*"([^"]+)"', text)
            for m in match:
                comments.append({"user": m[0], "text": m[1]})
    return comments

def apply_rules(comments: List[dict], rules: Rules):
    """Vyhodnotí podmínky soutěže."""
    valid = []
    audit = []
    seen_users = set()

    for c in comments:
        reasons = []
        tags = extract_usernames_from_comment(c["text"])

        if rules.min_tags and len(tags) < rules.min_tags:
            reasons.append(f"Má jen {len(tags)} tagů (min. {rules.min_tags})")

        if rules.require_keyword and rules.require_keyword.lower() not in c["text"].lower():
            reasons.append(f"Chybí klíčové slovo '{rules.require_keyword}'")

        if rules.disqualify_duplicates and c["user"].lower() in seen_users:
            reasons.append("Duplicitní komentář")

        if not reasons:
            valid.append(c)
            seen_users.add(c["user"].lower())

        audit.append({
            "user": c["user"],
            "text": c["text"],
            "tags_found": tags,
            "reasons": reasons or ["OK ✅"]
        })
    
    return valid, audit

def pick_winners(candidates: List[dict], count: int):
    """Vylosuje náhodné výherce."""
    if not candidates:
        return []
    random.seed(time.time())
    return random.sample(candidates, min(count, len(candidates)))

# =========================
# ENDPOINT
# =========================
@app.post("/draw", response_model=DrawResult)
async def draw(req: DrawRequest):
    comments = await fetch_instagram_comments(req.url)
    valid, audit = apply_rules(comments, req.rules)
    winners = pick_winners(valid, req.winners_count)

    return DrawResult(
        timestamp=int(time.time()),
        total_comments=len(comments),
        valid_candidates=len(valid),
        winners=[w["user"] for w in winners],
        audit=audit
    )
