# scoring/engine.py
def noter(data):
   """
   Exemple de moteur de scoring basique pour MunGrade.
   'data' est un dict avec les clés :
   moat, management, ROE, DetteEBITDA, PER
   """
   score = 0
   # Pondération simple
   moat_scores = {"Fort": 30, "Faible": 15, "Aucun": 0}
   management_scores = {"Excellent": 25, "Correct": 15, "Médiocre": 5}
   score += moat_scores.get(data.get("moat"), 0)
   score += management_scores.get(data.get("management"), 0)
   # ROE
   try:
       roe = float(data.get("ROE", 0))
       if roe > 15:
           score += 20
       elif roe > 10:
           score += 10
       else:
           score += 5
   except:
       pass
   # Dette / EBITDA (plus c'est bas, mieux c'est)
   try:
       ratio = float(data.get("DetteEBITDA", 0))
       if ratio < 1:
           score += 15
       elif ratio < 2:
           score += 10
       else:
           score += 5
   except:
       pass
   # PER (idéalement modéré)
   try:
       per = float(data.get("PER", 0))
       if 10 <= per <= 20:
           score += 10
       elif per < 10:
           score += 5
       else:
           score += 3
   except:
       pass
   # Label
   if score >= 80:
       label = "Excellent"
   elif score >= 60:
       label = "Bon"
   elif score >= 40:
       label = "Moyen"
   else:
       label = "Faible"
   return {"score": score, "label": label}