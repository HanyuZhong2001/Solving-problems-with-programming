# app_web.py
from flask import Flask, render_template, request
import pandas as pd
from app_logic import load_data, find_product, authority_score, consumer_score, combined_score, risk_flags

app = Flask(__name__)
prods, auth, revs = load_data()

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        pid = (request.form.get("product_id") or "").strip()
        if not pid:
            message = "Please enter a product ID."
            return render_template("index.html", message=message)
        found = find_product(prods, pid)
        if found.empty:
            message = "No product found for this ID."
            return render_template("index.html", message=message)
        p = found.iloc[0].to_dict()
        a_row_df = auth[auth["product_id"] == p["product_id"]]
        a_row = a_row_df.iloc[0].to_dict() if not a_row_df.empty else {}
        r_df = revs[revs["product_id"] == p["product_id"]].copy()

        A = round(authority_score(a_row), 1)
        C = round(consumer_score(r_df), 1)
        T = combined_score(A, C, wA=0.6)
        flags = risk_flags(p, a_row, r_df)

        breakdown = [
            f"Authority: {A} (record={a_row.get('has_record',0)}, cert={a_row.get('has_cert',0)}, penalties={a_row.get('penalty_count',0)})",
            f"Consumer: {C} (time-decay, reviewer reputation, avg rating)",
            f"Combined: {T} (wA=0.6)"
        ]
        recent = (
            r_df.sort_values("review_date", ascending=False)[["review_date","rating","reviewer_reputation","evidence_url"]]
            .head(3)
            .to_dict(orient="records")
        )
        return render_template("report.html",
                               product=p,
                               authority=a_row,
                               scores={"A":A, "C":C, "T":T},
                               flags=flags,
                               breakdown=breakdown,
                               recent_reviews=recent)
    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
