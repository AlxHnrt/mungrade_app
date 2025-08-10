# data_providers/yahoo_client.py
from __future__ import annotations
import math
from typing import Optional, Dict
import yfinance as yf
def _safe_pct(x: Optional[float]) -> Optional[float]:
   if x is None or (isinstance(x, float) and math.isnan(x)):
       return None
   return float(x) * 100.0
def fetch_metrics(ticker: str) -> Dict[str, Optional[float]]:
   """
   Récupère quelques métriques simples pour le préremplissage MunGrade :
   - ROE (%) à partir de info['returnOnEquity'] si dispo
   - PER (trailing) à partir de info['trailingPE'] ou fast_info
   - Dette/EBITDA à partir de info['totalDebt'] / info['ebitda'] si dispo
   Renvoie des None si indisponible.
   """
   t = yf.Ticker(ticker)
   # yfinance peut retourner fast_info et info (plus lent)
   info = {}
   try:
       info = t.info or {}
   except Exception:
       info = {}
   fast = getattr(t, "fast_info", {}) or {}
   # ROE
   roe = info.get("returnOnEquity", None)
   roe_pct = _safe_pct(roe) if roe is not None else None
   # PER
   per = info.get("trailingPE", None)
   if per is None:
       per = fast.get("trailingPE", None)
   # Dette / EBITDA
   total_debt = info.get("totalDebt", None)
   ebitda = info.get("ebitda", None)
   debt_ebitda = None
   try:
       if total_debt and ebitda and ebitda != 0:
           debt_ebitda = float(total_debt) / float(ebitda)
   except Exception:
       debt_ebitda = None
   return {
       "ROE": None if roe_pct is None else round(roe_pct, 2),
       "PER": None if per is None else round(float(per), 2),
       "DetteEBITDA": None if debt_ebitda is None else round(debt_ebitda, 2),
   }