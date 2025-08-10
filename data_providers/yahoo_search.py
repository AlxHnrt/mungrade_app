# data_providers/yahoo_search.py
from __future__ import annotations
import time
import requests
from typing import List, Dict
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
# mini-cache mémoire (clé -> (expiry, data))
_cache: Dict[str, tuple[float, list[dict]]] = {}
TTL = 1800  # 30 min
def search_companies(query: str, limit: int = 8) -> List[Dict]:
   q = (query or "").strip()
   if not q:
       return []
   # cache
   now = time.time()
   if q in _cache and _cache[q][0] > now:
       return _cache[q][1]
   params = {
       "q": q,
       "quotesCount": limit,
       "newsCount": 0,
       "quotesQueryId": "tss_match_phrase_query",
   }
   try:
       r = requests.get(YAHOO_SEARCH_URL, params=params, timeout=6)
       r.raise_for_status()
       js = r.json()
   except Exception:
       return []
   out = []
   for it in js.get("quotes", []):
       # on filtre sur des actions/ADRs/ETF (exclut index, crypto…)
       if it.get("quoteType") not in ("EQUITY", "ETF"):
           continue
       out.append({
           "symbol": it.get("symbol"),
           "name": it.get("shortname") or it.get("longname") or it.get("symbol"),
           "exchange": it.get("exchDisp") or it.get("exchange"),
           "type": it.get("quoteType"),
       })
       if len(out) >= limit:
           break
   # enregistre cache
   _cache[q] = (now + TTL, out)
   return out