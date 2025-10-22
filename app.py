import sys, math
from pathlib import Path
import pandas as pd
from jinja2 import Environment, FileSystemLoader

DATA = Path(__file__).parent / "data"
TPLS = Path(__file__).parent / "templates"

ELDERLY_SENSITIVE = {"health supplements","Physiotherapy device","Therapy patches","health care equipment"}

def time_decay(days): return math.exp(-max(days,0)/365.0)

def authority_score(row):
    base = 60*int(row.get("has_record",0)) + 20*int(row.get("has_cert",0))
    penalty = 10*min(int(row.get("penalty_count",0)),3)
    return max(0.0, min(100.0, base - penalty))

def consumer_score(revs: pd.DataFrame):
    if revs.empty: return 50.0
    today = pd.Timestamp.today()
    weights, vals = [], []
    for _, r in revs.iterrows():
        days = (today - pd.to_datetime(r["review_date"])).days if pd.notnull(r["review_date"]) else 365
        w = float(r.get("reviewer_reputation",0.5)) * time_decay(days)
        weights.append(w); vals.append((float(r["rating"])/5.0)*100*w)
    return sum(vals)/(sum(weights) or 1.0)

def combined(A, C, wA=0.6): return round(wA*A + (1-wA)*C, 2)

def risk_flags(prod, auth, revs):
    flags=[]
    if str(prod.get("category","")) in ELDERLY_SENSITIVE: flags.append("ELDERLY_SENSITIVE")
    if int(auth.get("has_record",0))==0: flags.append("NO_AUTH_RECORD")
    if int(auth.get("penalty_count",0))>=1: flags.append("PENALTY_HISTORY")
    recent = revs[ pd.to_datetime(revs["review_date"]) >= (pd.Timestamp.today()-pd.Timedelta(days=180)) ]
    if not recent.empty and recent["rating"].mean()<3.0: flags.append("LOW_RECENT_RATING")
    A, C = authority_score(auth), consumer_score(revs)
    if (A>=70 and C<=40) or (A<=40 and C>=70): flags.append("EVIDENCE_CONFLICT")
    return flags

def load_csvs():
    prods = pd.read_csv(DATA/"products.csv")
    prods["aliases"]=prods["aliases"].fillna("").apply(lambda s:[a.strip() for a in s.split("|") if a.strip()])
    auth = pd.read_csv(DATA/"authorities.csv")
    revs = pd.read_csv(DATA/"reviews.csv", parse_dates=["review_date"])
    return prods, auth, revs

def find_candidates(prods, q):
    q=q.lower().strip()
    m = (
        prods["product_id"].astype(str).str.lower().str.contains(q) |
        prods["name"].str.lower().str.contains(q) |
        prods["brand"].str.lower().str.contains(q) |
        prods["aliases"].apply(lambda lst: any(q in a.lower() for a in lst))
    )
    return prods[m]

def render_report(product, authority, revs, scores, flags, breakdown):
    env = Environment(loader=FileSystemLoader(str(TPLS)))
    tpl = env.get_template("report.html.j2")
    html = tpl.render(
        product=product, authority=authority, recent_reviews=revs.sort_values("review_date",ascending=False).head(3).to_dict(orient="records"),
        scores=scores, flags=flags, breakdown=breakdown
    )
    out = Path(f"report_{product['product_id']}.html")
    out.write_text(html, encoding="utf-8")
    return out

def main():
    if len(sys.argv)<2:
        print("Usage: python app.py <product id or keyword>"); return
    q = sys.argv[1]
    prods, auth, revs = load_csvs()
    found = find_candidates(prods, q)
    if found.empty:
        print("No product found. Try another keyword / ID."); return

    for _, p in found.iterrows():
        pid = p["product_id"]
        a = auth[auth["product_id"]==pid].iloc[0].to_dict() if not auth[auth["product_id"]==pid].empty else {}
        r = revs[revs["product_id"]==pid].copy()
        A, C = authority_score(a) if a else 0.0, consumer_score(r)
        T = combined(A, C, wA=0.6)
        flags = risk_flags(p, a, r)
        breakdown = [
            f"Authority base={A:.1f} (record={a.get('has_record',0)}, cert={a.get('has_cert',0)}, penalty={a.get('penalty_count',0)})",
            f"Consumer ~{C:.1f} (time-decay, reviewer rep)",
            f"Combined={T:.1f} (wA=0.6)"
        ]
        print("="*70)
        print(f"[{pid}] {p['brand']} - {p['name']} (category: {p['category']})")
        print(f"AuthorityScore={A:.1f} | ConsumerScore={C:.1f} | Combined={T:.1f}")
        print(f"Risk Flags: {', '.join(flags) if flags else 'NONE'}")
        if a.get("notice_url"): print(f"Authority notice: {a['notice_url']}")
        for _, rr in r.sort_values('review_date',ascending=False).head(3).iterrows():
            print(f" - {rr['review_date'].date()} rating={rr['rating']} rep={rr['reviewer_reputation']}  {rr.get('evidence_url','')}")
        out = render_report(p.to_dict(), a, r, {"A":round(A,1),"C":round(C,1),"total":round(T,1)}, flags, breakdown)
        print(f"HTML report generated: {out}")
    print("="*70)

if __name__=="__main__":
    main()
