# mungrade_flask_starter.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from scoring.engine import noter  # <— ton moteur de scoring (dans scoring/engine.py)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# ---------- Routes ----------
@app.route("/playground", methods=["GET"])
def playground():
   return render_template("playground.html")
@app.route("/health", methods=["GET"])
def health():
   return jsonify({"status": "ok"}), 200
@app.route("/", methods=["GET"])
def home():
   # Formulaire HTML
   return render_template("index.html")
@app.route("/score", methods=["POST"])
def score_json():
   """Endpoint JSON pour l’app mobile / appels API"""
   data = request.get_json(silent=True) or {}
   result = noter(data)  # {"score": ..., "label": ...}
   return jsonify(result), 200
@app.route("/score-web", methods=["POST"])
def score_web():
   """Soumission du formulaire HTML -> résultat affiché dans la page"""
   raw = {
       "moat": request.form.get("moat", "").strip(),
       "management": request.form.get("management", "").strip(),
       "ROE": request.form.get("ROE", "").strip(),
       "DetteEBITDA": request.form.get("DetteEBITDA", "").strip(),
       "PER": request.form.get("PER", "").strip(),
   }
   # Validations simples
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
# ---------- Lancement ----------
if __name__ == "__main__":
   # Mode dev avec auto‑reload
   app.run(debug=True)