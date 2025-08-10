# mungrade_flask_starter.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from scoring.engine import noter  # ton moteur de scoring
from typing import Dict, Optional
from data_providers.yahoo_client import fetch_metrics
from data_providers.yahoo_search import search_companies  # ✅ Import ajouté
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# ---------- Mappage noms -> tickers Yahoo ----------
NAME_TO_TICKER: Dict[str, str] = {
   "rr.l": "RR.L",
   "rolls-royce": "RR.L",
   "rolls royce": "RR.L",
   "ge": "GE",
   "general electric": "GE",
   "su.pa": "SU.PA",
   "schneider electric": "SU.PA",
   "mc.pa": "MC.PA",
   "lvmh": "MC.PA",
}
def _norm(q: str) -> str:
   return q.strip().lower()
def _resolve_to_ticker(q: str) -> Optional[str]:
   qn = _norm(q)
   if "." in qn or qn.isupper():
       return q.strip()
   return NAME_TO_TICKER.get(qn)
def _infer_moat_mgmt(roe: Optional[float], debt_ebitda: Optional[float]) -> Dict[str, str]:
   moat = "Aucun"
   mgmt = "Correct"
   if roe is not None and roe >= 25 and (debt_ebitda is None or debt_ebitda <= 1.5):
       moat = "Fort"
       mgmt = "Excellent"
   elif roe is not None and roe >= 12:
       moat = "Faible"
       mgmt = "Correct"
   if debt_ebitda is not None and debt_ebitda > 3:
       mgmt = "Médiocre"
   return {"moat": moat, "management": mgmt}
# ---------- Routes ----------
@app.route("/playground", methods=["GET"])
def playground():
   return render_template("playground.html")
@app.route("/health", methods=["GET"])
def health():
   return jsonify({"status": "ok"}), 200
@app.route("/", methods=["GET"])
def home():
   return render_template("index.html")
@app.route("/score", methods=["POST"])
def score_json():
   data = request.get_json(silent=True) or {}
   result = noter(data)
   return jsonify(result), 200
@app.route("/score-web", methods=["POST"])
def score_web():
   raw = {
       "moat": request.form.get("moat", "").strip(),
       "management": request.form.get("management", "").strip(),
       "ROE": request.form.get("ROE", "").strip(),
       "DetteEBITDA": request.form.get("DetteEBITDA", "").strip(),
       "PER": request.form.get("PER", "").strip(),
   }
   errors = []
   allowed_moat = {"Aucun", "Faible", "Fort"}
   allowed_mgmt = {"Médiocre", "Correct", "Excellent"}
   if raw["moat"] not in allowed_moat:
       errors.append("Champ 'Moat' invalide.")
   if raw["management"] not in allowed_mgmt:
       errors.append("Champ 'Management' invalide.")
   def to_float(name, label, min_allowed=None, max_allowed=None):
       try:
           val = float(raw[name].replace(",", "."))
       except ValueError:
           errors.append(f"'{label}' doit être un nombre.")
           return None
       if min_allowed is not None and val < min_allowed:
           errors.append(f"'{label}' doit être ≥ {min_allowed}.")
       if max_allowed is not None and val > max_allowed:
           errors.append(f"'{label}' doit être ≤ {max_allowed}.")
       return val
   roe = to_float("ROE", "ROE (%)", -100, 200)
   de  = to_float("DetteEBITDA", "Dette / EBITDA", 0, 20)
   per = to_float("PER", "PER", 0, 500)
   if errors:
       return render_template("index.html", form=raw, errors=errors)
   clean = {
       "moat": raw["moat"],
       "management": raw["management"],
       "ROE": roe,
       "DetteEBITDA": de,
       "PER": per,
   }
   result = noter(clean)
   return render_template("index.html", form=raw, result=result)
@app.route("/prefill", methods=["GET"])
def prefill():
   q = request.args.get("q", "").strip()
   if not q:
       return jsonify({"error": "Paramètre q manquant"}), 400
   ticker = _resolve_to_ticker(q) or q
   try:
       metrics = fetch_metrics(ticker)
   except Exception as e:
       return jsonify({"found": False, "message": f"Erreur provider: {e}"}), 502
   if all(v is None for v in metrics.values()):
       return jsonify({"found": False, "message": "Données insuffisantes pour ce titre"}), 404
   # 🔹 Ajout récupération nom + logo
   import yfinance as yf
   stock = yf.Ticker(ticker)
   info = stock.info
   company_name = info.get("longName", ticker)
   domain_guess = company_name.split()[0].lower() + ".com"
   logo_url = f"https://logo.clearbit.com/{domain_guess}"
   hints = _infer_moat_mgmt(metrics.get("ROE"), metrics.get("DetteEBITDA"))
   data = {
       "moat": hints["moat"],
       "management": hints["management"],
       "ROE": metrics.get("ROE"),
       "DetteEBITDA": metrics.get("DetteEBITDA"),
       "PER": metrics.get("PER"),
       "ticker": ticker,
       "companyName": company_name,
       "companyLogo": logo_url
   }
   return jsonify({"found": True, "data": data})
# ✅ Recherche
@app.route("/search", methods=["GET"])
def search():
   q = request.args.get("q", "").strip()
   results = search_companies(q, limit=8)
   return jsonify({"query": q, "results": results})
# ---------- Lancement ----------
if __name__ == "__main__":
   app.run(debug=True)