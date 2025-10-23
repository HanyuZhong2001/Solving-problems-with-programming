# app_logic.py
from pathlib import Path
import math
import pandas as pd

DATA = Path(__file__).parent / "data"
ELDERLY_SENSITIVE = {"保健品","理疗仪","理疗贴","保健器械"}

def time_decay(days):
    return math.exp(-max(days,0)/365.0)

def authority_score(a_row: dict) -> float:
    if not a_row:
        return 0.0
    base = 60*int(a_row.get("has_record",0)) + 20*int(a_row.get("has_cert",0))
    penalty = 10*min(int(a_row.get("penalty_count",0)), 3)
    return max(0.0, min(100.0, base - penalty))

def consumer_score(revs: pd.DataFrame) -> float:
    if revs.empty: return 50.0
    today = pd.Timestamp.today()
    weights, vals = [], []
    for _, r in revs.iterrows():
        days = (today - pd.to_datetime(r["review_date"])).days if pd.notnull(r["review_date"]) else 365
        rep = float(r.get("reviewer_reputation",0.5))
        w = rep * time_decay(days)
        weights.append(w)
        vals.append((float(r["rating"])/5.0)*100*w)
    return sum(vals)/(sum(weights) or 1.0)

def combined_score(A: float, C: float, wA: float=0.6) -> float:
    return round(wA*A + (1-wA)*C, 1)

def risk_flags(prod_row: dict, a_row: dict, revs: pd.DataFrame):
    flags=[]
    if str(prod_row.get("category","")) in ELDERLY_SENSITIVE:
        flags.append("ELDERLY_SENSITIVE")
    if int(a_row.get("has_record",0)) == 0:
        flags.append("NO_AUTH_RECORD")
    if int(a_row.get("penalty_count",0)) >= 1:
        flags.append("PENALTY_HISTORY")
    if not revs.empty:
        recent = revs[pd.to_datetime(revs["review_date"]) >= (pd.Timestamp.today()-pd.Timedelta(days=180))]
        if not recent.empty and recent["rating"].mean() < 3.0:
            flags.append("LOW_RECENT_RATING")
    A = authority_score(a_row)
    C = consumer_score(revs)
    if (A >= 70 and C <= 40) or (A <= 40 and C >= 70):
        flags.append("EVIDENCE_CONFLICT")
    return flags

def load_data():
    prods = pd.read_csv(DATA/"products.csv")
    prods["aliases"] = prods["aliases"].fillna("").apply(lambda s: [a.strip() for a in s.split("|") if a.strip()])
    auth = pd.read_csv(DATA/"authorities.csv", parse_dates=["last_notice_date"])
    revs = pd.read_csv(DATA/"reviews.csv", parse_dates=["review_date"])
    return prods, auth, revs

def find_product(prods: pd.DataFrame, query: str):
    q = str(query).strip().lower()
    mask = (
        prods["product_id"].astype(str).str.lower() == q
    )  # 为了简洁：这里做“精确ID匹配”（大小写不敏感）
    return prods[mask].copy()
