import streamlit as st
import anthropic
import json
import re
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.parse
import html as html_lib

def esc(value):
    """Escape user-provided strings before embedding in HTML to prevent XSS."""
    if value is None: return ''
    return html_lib.escape(str(value))

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analyzer - Claude",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] { font-family: 'Space Mono', monospace; background: #060a0f; color: #e2e8f0; }

.main { background: #060a0f; }
.block-container { padding: 1.5rem 1.5rem 4rem; max-width: 900px; }

h1 { font-family: 'Syne', sans-serif !important; font-size: 22px !important; color: #f0f6ff !important; letter-spacing: -0.5px; }
h2 { font-family: 'Syne', sans-serif !important; font-size: 14px !important; color: #3b82f6 !important; letter-spacing: 3px; text-transform: uppercase; }
h3 { font-family: 'Syne', sans-serif !important; font-size: 12px !important; color: #93c5fd !important; letter-spacing: 2px; text-transform: uppercase; }

/* Inputs */
input[type="text"], input[type="number"] {
    background: #060c15 !important; border: 1px solid #1a2e48 !important;
    color: #ffffff !important; font-family: 'Space Mono', monospace !important;
    font-size: 14px !important; font-weight: 700 !important;
}
input::placeholder { color: rgba(255,255,255,0.4) !important; }

/* Buttons */
.stButton > button {
    background: #3b82f6 !important; color: #fff !important; border: none !important;
    font-family: 'Syne', sans-serif !important; font-size: 13px !important;
    font-weight: 700 !important; letter-spacing: 2px !important;
    text-transform: uppercase !important; width: 100% !important;
    padding: 0.75rem !important;
}
.stButton > button:hover { background: #2563eb !important; }
.stButton > button:disabled { background: #1e2d3d !important; color: #7a9ab8 !important; }



/* Stop button */
.stop-btn > button { background: transparent !important; border: 1px solid #dc2626 !important; color: #f87171 !important; }
.stop-btn > button:hover { background: #150505 !important; }

/* Cards */
.card { background: #0d1825; border: 1px solid #1a2e48; padding: 14px; margin-bottom: 10px; }
.card-blue { border-color: #3b82f655; background: #080f1f; }
.card-purple { border-color: #7c3aed55; background: #0c0818; }
.card-green { border-color: #16a34a55; background: #060f09; }
.card-gold { border-color: #f59e0b; background: #0d0b02; }
.card-gray { border-color: #6b7280; background: #0a0c0f; }
.card-win { border-color: #f59e0b44; }

.label { font-size: 8px; letter-spacing: 2px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }
.big-val { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; color: #f0f6ff; }
.big-val-purple { color: #a78bfa; }
.big-val-green { color: #4ade80; }
.big-val-blue { color: #93c5fd; }
.big-val-gold { color: #f59e0b; }
.sub-text { font-size: 9px; color: #cbd5e1; margin-top: 3px; line-height: 1.5; }

.badge-up { display:inline-block; font-size:8px; padding:2px 7px; border:1px solid #16a34a44; background:#061508; color:#4ade80; text-transform:uppercase; }
.badge-dn { display:inline-block; font-size:8px; padding:2px 7px; border:1px solid #dc262644; background:#150505; color:#f87171; text-transform:uppercase; }
.badge-fl { display:inline-block; font-size:8px; padding:2px 7px; border:1px solid #ca8a0444; background:#0f1208; color:#fbbf24; text-transform:uppercase; }

.verdict-bull { background:#061508; border:1px solid #16a34a55; padding:12px; margin-bottom:8px; }
.verdict-bear { background:#150505; border:1px solid #dc262655; padding:12px; margin-bottom:8px; }
.verdict-neut { background:#0f1208; border:1px solid #ca8a0455; padding:12px; margin-bottom:8px; }
.verdict-label-bull { font-family:'Syne',sans-serif; font-size:13px; font-weight:800; color:#4ade80; }
.verdict-label-bear { font-family:'Syne',sans-serif; font-size:13px; font-weight:800; color:#f87171; }
.verdict-label-neut { font-family:'Syne',sans-serif; font-size:13px; font-weight:800; color:#fbbf24; }
.verdict-tag { font-size:8px; letter-spacing:1.5px; text-transform:uppercase; opacity:0.8; }
.verdict-tag-bull { color:#4ade80; }
.verdict-tag-bear { color:#f87171; }
.verdict-tag-neut { color:#fbbf24; }
.verdict-reason { font-size:13px; color:#e2e8f0; margin-top:3px; line-height:1.5; }

.sec-hdr { font-family:'Syne',sans-serif; font-size:11px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#3b82f6; padding:8px 12px; background:#0d1825; border-bottom:1px solid #111c2a; margin-bottom:0; }
.sec-body { padding:12px; font-size:13px; line-height:1.85; color:#e2e8f0; background:#090f1a; border:1px solid #111c2a; margin-bottom:8px; }

.divider { height:1px; background:#111c2a; margin:16px 0; }
.disc { font-size:9px; color:#4a6a88; text-align:center; letter-spacing:1.5px; padding:20px 0; }

/* Rank badge */
.rank-gold { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:#f59e0b; margin-right:4px; }
.rank-silver { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; color:#9ca3af; margin-right:4px; }

/* Table */
.data-table { width:100%; border-collapse:collapse; font-size:13px; }
.data-table th { text-align:left; padding:8px 11px; font-size:10px; letter-spacing:2px; color:#94a3b8; text-transform:uppercase; border-bottom:1px solid #111c2a; background:#0d1825; font-family:'Syne',sans-serif; }
.data-table td { padding:10px 11px; border-bottom:1px solid #090f1a; vertical-align:top; color:#e2e8f0; }
.data-table tr:last-child td { border-bottom:none; }
.sig-good { color:#4ade80; font-size:12px; } .sig-bad { color:#f87171; font-size:12px; } .sig-ok { color:#fbbf24; font-size:12px; }

.stExpander { border:1px solid #1a2e48 !important; background:#0a1420 !important; }
.stExpander > div > div { background:#0d1825 !important; }

hr { border-color: #111c2a !important; }
.stAlert { background:#150505 !important; border:1px solid #dc2626 !important; color:#f87171 !important; }

</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_json(txt):
    if not txt: return None
    # Strip markdown fences
    txt = re.sub(r'```json\s*', '', txt, flags=re.I)
    txt = re.sub(r'```\s*', '', txt)
    txt = txt.strip()
    # Try direct parse
    try: return json.loads(txt)
    except: pass
    # Try extracting outermost { }
    a, b = txt.find('{'), txt.rfind('}')
    if a >= 0 and b > a:
        try: return json.loads(txt[a:b+1])
        except: pass
    # Response was truncated — try to repair it
    # Find the furthest valid { position
    start = txt.find('{') if txt.find('{') >= 0 else 0
    fragment = txt[start:]
    # Remove trailing incomplete key/value pairs
    fragment = re.sub(r',\s*"[^"]*"?\s*:\s*[^,}\]]*$', '', fragment)
    fragment = re.sub(r',\s*"[^"]*"?\s*$', '', fragment)
    fragment = re.sub(r',\s*$', '', fragment)
    # Count and close open brackets/braces
    depth_brace = 0
    depth_bracket = 0
    in_str = False
    escaped = False
    for ch in fragment:
        if escaped: escaped = False; continue
        if ch == '\\': escaped = True; continue
        if ch == '"' and not escaped: in_str = not in_str; continue
        if in_str: continue
        if ch == '{': depth_brace += 1
        elif ch == '}': depth_brace -= 1
        elif ch == '[': depth_bracket += 1
        elif ch == ']': depth_bracket -= 1
    # Close open structures
    fragment += ']' * max(0, depth_bracket)
    fragment += '}' * max(0, depth_brace)
    try: return json.loads(fragment)
    except: pass
    return None

def delta_badge(target, current):
    try:
        t = float(re.sub(r'[^0-9.-]','', str(target or '')))
        c = float(re.sub(r'[^0-9.-]','', str(current or '')))
        if c == 0: return ''
        p = ((t - c) / c) * 100
        if p > 0: return f'<span class="badge-up">▲ {p:.1f}%</span>'
        if p < 0: return f'<span class="badge-dn">▼ {abs(p):.1f}%</span>'
    except: pass
    return ''

def verdict_cls(v):
    v = (v or '').upper()
    if 'BULL' in v: return 'bull'
    if 'BEAR' in v: return 'bear'
    return 'neut'

def verdict_icon(v):
    v = (v or '').upper()
    if 'BULL' in v: return '▲'
    if 'BEAR' in v: return '▼'
    return '◆'

def rating_cls(r):
    r = (r or '').lower()
    if 'buy' in r or 'outperform' in r: return 'sig-good'
    if 'sell' in r or 'underperform' in r: return 'sig-bad'
    return 'sig-ok'

def render_verdict(tag, verdict, reason, port=False):
    cls = verdict_cls(verdict)
    ic = verdict_icon(verdict)
    tag_cls = f'verdict-tag-{cls}'
    lbl_cls = f'verdict-label-{cls}'
    div_cls = f'verdict-{cls}'
    context = "Portfolio Synergy" if port else "Standalone Verdict"
    st.markdown(f"""
    <div class="{div_cls}">
      <div class="verdict-tag {tag_cls}">{context}</div>
      <div class="{lbl_cls}">{ic} {verdict}</div>
      <div class="verdict-reason">{reason or ''}</div>
    </div>
    """, unsafe_allow_html=True)

FUND_LABELS = [
    ("revenue","Revenue"),("grossMargin","Gross Margin"),("operatingMargin","Op Margin"),
    ("netMargin","Net Margin"),("eps","EPS"),("forwardEPS","Fwd EPS"),
    ("peRatio","P/E"),("forwardPE","Fwd P/E"),("evEbitda","EV/EBITDA"),
    ("debtToEquity","Debt/Equity"),("freeCashFlow","Free Cash Flow"),
    ("roe","ROE"),("divYield","Div Yield"),
]

# ── FMP Data Fetching ────────────────────────────────────────────────────────

def finnhub_quote(ticker, fh_key):
    """Fetch real-time quote from Finnhub. Returns dict with c=current, pc=prev_close, dp=chg_pct."""
    if not fh_key: return {"_error": "no key"}
    # Safety: strip spaces and non-alphanumeric chars — Finnhub needs clean symbol
    import re as _re
    clean_ticker = _re.sub(r'[^A-Z0-9.-]', '', ticker.upper().upper().strip())
    if not clean_ticker: return {"_error": "invalid ticker"}
    url = f"https://finnhub.io/api/v1/quote?symbol={clean_ticker}&token={fh_key}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
            if data.get("c",0) == 0:
                return {"_error": f"price=0 or no data for {ticker}"}
            return data
    except Exception as e:
        return {"_error": str(e)}

def finnhub_sentiment(ticker, fh_key):
    """Fetch news sentiment from Finnhub /news-sentiment endpoint.
    Returns dict with buzz score, sentiment score, weekly/monthly article counts."""
    if not fh_key: return {}
    import re as _re
    clean = _re.sub(r'[^A-Z0-9.-]', '', ticker.upper().strip())
    url = f"https://finnhub.io/api/v1/news-sentiment?symbol={clean}&token={fh_key}"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
            if not data or not data.get("buzz"): return {}
            return data
    except Exception:
        return {}

def fmp_get(endpoint, fmp_api_key, params=None):
    """Fetch a single FMP endpoint. Returns dict/list or None on error."""
    base = "https://financialmodelingprep.com/api"
    url = f"{base}{endpoint}?apikey={fmp_api_key}"
    if params:
        url += "&" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
            return data
    except Exception:
        return None

def fmp_fetch_all(ticker, fmp_api_key):
    """Fetch all relevant FMP data for a ticker in parallel threads."""
    endpoints = {
        "quote":       f"/v3/quote/{ticker}",
        "profile":     f"/v3/profile/{ticker}",
        "ratios":      f"/v3/ratios-ttm/{ticker}",
        "income":      f"/v3/income-statement/{ticker}",
        "cashflow":    f"/v3/cash-flow-statement/{ticker}",
        "balance":     f"/v3/balance-sheet-statement/{ticker}",
        "estimates":   f"/v3/analyst-estimates/{ticker}",
        "targets":     f"/v4/price-target-consensus",
        "target_list": f"/v4/price-target",
        "dcf":         f"/v3/discounted-cash-flow/{ticker}",
        "earnings_est":   f"/v3/earnings-surprises/{ticker}",
        "earnings_next":  f"/v3/historical/earning_calendar/{ticker}",
        "earnings_upcoming": f"/v3/earning_calendar",
    }
    results = {}
    def fetch_one(key, ep):
        if key in ("targets", "target_list"):
            params = {"symbol": ticker}
        elif key == "earnings_upcoming":
            from datetime import datetime as _dt2, timedelta as _td
            today = _dt2.now().strftime("%Y-%m-%d")
            future = (_dt2.now() + _td(days=180)).strftime("%Y-%m-%d")
            params = {"symbol": ticker, "from": today, "to": future}
        else:
            params = None
        return key, fmp_get(ep, fmp_api_key, params)

    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_one, k, v): k for k, v in endpoints.items()}
        for fut in as_completed(futures):
            key, data = fut.result()
            results[key] = data
    return results

def format_fmp_context(ticker, raw):
    """Format FMP raw data into a clean text block for the Claude prompt."""
    lines = [f"=== LIVE MARKET DATA FOR {ticker} (from Financial Modeling Prep) ==="]

    # Quote
    q = (raw.get("quote") or [{}])
    q = q[0] if isinstance(q, list) and q else q if isinstance(q, dict) else {}
    if q:
        price = q.get("price","N/A")
        chg   = q.get("changesPercentage","N/A")
        mktcap= q.get("marketCap","N/A")
        hi52  = q.get("yearHigh","N/A")
        lo52  = q.get("yearLow","N/A")
        pe    = q.get("pe","N/A")
        eps   = q.get("eps","N/A")
        avg50 = q.get("priceAvg50","N/A")
        avg200= q.get("priceAvg200","N/A")
        vol   = q.get("avgVolume","N/A")
        lines.append(f"Current Price: ${price} ({chg}% today)")
        lines.append(f"Market Cap: ${mktcap:,}" if isinstance(mktcap,int) else f"Market Cap: {mktcap}")
        lines.append(f"52-Week Range: ${lo52} – ${hi52}")
        lines.append(f"50-Day MA: ${avg50}  |  200-Day MA: ${avg200}")
        lines.append(f"P/E (TTM): {pe}  |  EPS (TTM): ${eps}")
        lines.append(f"Avg Volume: {vol:,}" if isinstance(vol,int) else f"Avg Volume: {vol}")

    # Profile
    p = (raw.get("profile") or [{}])
    p = p[0] if isinstance(p, list) and p else p if isinstance(p, dict) else {}
    if p:
        lines.append(f"Sector: {p.get('sector','N/A')}  |  Industry: {p.get('industry','N/A')}")
        lines.append(f"Description: {str(p.get('description',''))[:300]}")
        beta = p.get("beta","N/A")
        lines.append(f"Beta: {beta}")

    # Ratios TTM
    r = (raw.get("ratios") or [{}])
    r = r[0] if isinstance(r, list) and r else r if isinstance(r, dict) else {}
    if r:
        lines.append("--- KEY RATIOS (TTM) ---")
        def fmt(v, pct=False, x=False):
            if v is None: return "N/A"
            try:
                f = float(v)
                if pct: return f"{f*100:.1f}%"
                if x:   return f"{f:.1f}x"
                return f"{f:.2f}"
            except: return str(v)
        lines.append(f"P/E: {fmt(r.get('peRatioTTM'),x=True)}  |  Fwd P/E: {fmt(r.get('priceEarningsRatioTTM'),x=True)}")
        lines.append(f"P/S: {fmt(r.get('priceToSalesRatioTTM'),x=True)}  |  P/B: {fmt(r.get('priceToBookRatioTTM'),x=True)}")
        lines.append(f"EV/EBITDA: {fmt(r.get('enterpriseValueMultipleTTM'),x=True)}")
        lines.append(f"Gross Margin: {fmt(r.get('grossProfitMarginTTM'),pct=True)}  |  Net Margin: {fmt(r.get('netProfitMarginTTM'),pct=True)}")
        lines.append(f"Op Margin: {fmt(r.get('operatingProfitMarginTTM'),pct=True)}")
        lines.append(f"ROE: {fmt(r.get('returnOnEquityTTM'),pct=True)}  |  ROIC: {fmt(r.get('returnOnInvestedCapitalTTM'),pct=True)}")
        lines.append(f"Debt/Equity: {fmt(r.get('debtEquityRatioTTM'))}  |  Current Ratio: {fmt(r.get('currentRatioTTM'))}")
        lines.append(f"FCF Yield: {fmt(r.get('freeCashFlowYieldTTM'),pct=True)}")
        lines.append(f"Dividend Yield: {fmt(r.get('dividendYieldTTM'),pct=True)}")

    # Income statement (most recent)
    inc = (raw.get("income") or [{}])
    inc = inc[0] if isinstance(inc, list) and inc else {}
    if inc:
        lines.append("--- INCOME STATEMENT (Most Recent Annual) ---")
        rev  = inc.get("revenue","N/A")
        gp   = inc.get("grossProfit","N/A")
        oi   = inc.get("operatingIncome","N/A")
        ni   = inc.get("netIncome","N/A")
        ebitda=inc.get("ebitda","N/A")
        eps_d= inc.get("eps","N/A")
        period=inc.get("date","N/A")
        def fm(v):
            if v=="N/A" or v is None: return "N/A"
            try:
                n=float(v)
                if abs(n)>=1e9: return f"${n/1e9:.2f}B"
                if abs(n)>=1e6: return f"${n/1e6:.1f}M"
                return f"${n:,.0f}"
            except: return str(v)
        lines.append(f"Period: {period}")
        lines.append(f"Revenue: {fm(rev)}  |  Gross Profit: {fm(gp)}")
        lines.append(f"EBITDA: {fm(ebitda)}  |  Operating Income: {fm(oi)}")
        lines.append(f"Net Income: {fm(ni)}  |  EPS: ${eps_d}")

    # Cash flow (most recent)
    cf = (raw.get("cashflow") or [{}])
    cf = cf[0] if isinstance(cf, list) and cf else {}
    if cf:
        lines.append("--- CASH FLOW (Most Recent Annual) ---")
        ocf = cf.get("operatingCashFlow","N/A")
        fcf = cf.get("freeCashFlow","N/A")
        capex=cf.get("capitalExpenditure","N/A")
        lines.append(f"Operating CF: {fm(ocf)}  |  Free CF: {fm(fcf)}  |  CapEx: {fm(capex)}")

    # Balance sheet
    bs = (raw.get("balance") or [{}])
    bs = bs[0] if isinstance(bs, list) and bs else {}
    if bs:
        lines.append("--- BALANCE SHEET (Most Recent) ---")
        cash  = bs.get("cashAndCashEquivalents","N/A")
        debt  = bs.get("totalDebt","N/A")
        equity= bs.get("totalStockholdersEquity","N/A")
        lines.append(f"Cash: {fm(cash)}  |  Total Debt: {fm(debt)}  |  Equity: {fm(equity)}")

    # DCF intrinsic value (FMP calculated)
    dcf = raw.get("dcf")
    if isinstance(dcf, list) and dcf: dcf = dcf[0]
    if isinstance(dcf, dict) and dcf.get("dcf"):
        lines.append(f"--- FMP DCF INTRINSIC VALUE: ${dcf.get('dcf','N/A')} (model date: {dcf.get('date','N/A')}) ---")
        lines.append("NOTE: Use this as one input but apply sector-appropriate adjustments.")

    # Analyst estimates (forward)
    est = (raw.get("estimates") or [{}])
    est = est[0] if isinstance(est, list) and est else {}
    if est:
        lines.append("--- ANALYST FORWARD ESTIMATES ---")
        lines.append(f"Est. Revenue (next yr): {fm(est.get('estimatedRevenueAvg','N/A'))}")
        lines.append(f"Est. EPS (next yr): ${est.get('estimatedEpsAvg','N/A')}")
        lines.append(f"Est. EBITDA (next yr): {fm(est.get('estimatedEbitdaAvg','N/A'))}")
        lines.append(f"Number of analysts: {est.get('numberAnalystEstimatedRevenue','N/A')}")

    # Analyst price targets
    tgt = raw.get("targets")
    if isinstance(tgt, list) and tgt: tgt = tgt[0]
    if isinstance(tgt, dict):
        lines.append("--- ANALYST PRICE TARGETS (Consensus) ---")
        lines.append(f"Consensus Target: ${tgt.get('targetConsensus','N/A')}")
        lines.append(f"High Target: ${tgt.get('targetHigh','N/A')}  |  Low Target: ${tgt.get('targetLow','N/A')}")
        lines.append(f"Median Target: ${tgt.get('targetMedian','N/A')}")

    # Individual analyst targets (most recent 5)
    tlist = raw.get("target_list") or []
    if isinstance(tlist, list) and tlist:
        lines.append("--- RECENT INDIVIDUAL ANALYST RATINGS ---")
        for a in tlist[:5]:
            lines.append(f"  {a.get('analystCompany','?')} | {a.get('analystName','?')} | "
                        f"Target: ${a.get('priceTarget','?')} | "
                        f"Published: {a.get('publishedDate','?')[:10] if a.get('publishedDate') else '?'}")

    lines.append(f"=== END LIVE DATA FOR {ticker} ===")
    return "\n".join(lines)


# ── Smart Intrinsic Value Calculator ──────────────────────────────────────────
SECTOR_MULTIPLES = {
    "Technology":             {"ev_rev": 8.0,  "kind": "growth"},
    "Communication Services": {"ev_rev": 6.0,  "kind": "growth"},
    "Healthcare":             {"ev_rev": 5.0,  "kind": "growth"},
    "Consumer Discretionary": {"ev_rev": 2.0,  "kind": "mixed"},
    "Utilities":              {"ev_ebitda": 10.0, "kind": "profitable"},
    "Energy":                 {"ev_ebitda": 7.0,  "kind": "profitable"},
    "Financials":             {"pb": 1.5,          "kind": "financial"},
    "Industrials":            {"ev_ebitda": 12.0,  "kind": "profitable"},
    "Materials":              {"ev_ebitda": 10.0,  "kind": "profitable"},
    "Real Estate":            {"ev_ebitda": 20.0,  "kind": "profitable"},
    "Consumer Staples":       {"ev_ebitda": 14.0,  "kind": "profitable"},
}

def calc_intrinsic_value(raw_fmp):
    try:
        q   = (raw_fmp.get("quote") or [{}])
        q   = q[0] if isinstance(q,list) and q else q if isinstance(q,dict) else {}
        inc = (raw_fmp.get("income") or [{}])
        inc = inc[0] if isinstance(inc,list) and inc else {}
        cf  = (raw_fmp.get("cashflow") or [{}])
        cf  = cf[0] if isinstance(cf,list) and cf else {}
        bs  = (raw_fmp.get("balance") or [{}])
        bs  = bs[0] if isinstance(bs,list) and bs else {}
        est = (raw_fmp.get("estimates") or [{}])
        est = est[0] if isinstance(est,list) and est else {}
        pro = (raw_fmp.get("profile") or [{}])
        pro = pro[0] if isinstance(pro,list) and pro else pro if isinstance(pro,dict) else {}
        price      = float(q.get("price") or 0)
        mkt_cap    = float(q.get("marketCap") or 0)
        shares     = float(q.get("sharesOutstanding") or 0)
        if shares == 0 and price > 0 and mkt_cap > 0:
            shares = mkt_cap / price
        fcf        = float(cf.get("freeCashFlow") or 0)
        net_income = float(inc.get("netIncome") or 0)
        revenue    = float(inc.get("revenue") or 0)
        ebitda     = float(inc.get("ebitda") or 0)
        total_debt = float(bs.get("totalDebt") or 0)
        cash_      = float(bs.get("cashAndCashEquivalents") or 0)
        fwd_rev    = float(est.get("estimatedRevenueAvg") or 0)
        book_val   = float(bs.get("totalStockholdersEquity") or 0)
        net_debt   = total_debt - cash_
        sector     = pro.get("sector","Technology")
        dcf_raw = raw_fmp.get("dcf")
        if isinstance(dcf_raw,list) and dcf_raw: dcf_raw = dcf_raw[0]
        fmp_dcf = float(dcf_raw.get("dcf",0)) if isinstance(dcf_raw,dict) else 0
        is_profitable = fcf > 0 and net_income > 0 and ebitda > 0
        is_financial  = "financial" in sector.lower() or "bank" in sector.lower()
        def fv(v): return f"${v:,.2f}"
        if is_financial and book_val > 0 and shares > 0:
            mult = SECTOR_MULTIPLES.get("Financials",{}).get("pb",1.5)
            bvps = book_val / shares
            iv   = bvps * mult
            return (fv(iv), f"P/Book {mult}x (Financials - live)", f"Book/share {fv(bvps)} x {mult}x")
        elif is_profitable and fmp_dcf > 0:
            return (fv(fmp_dcf), "FMP DCF Model (live)", f"Live FCF {fv(fcf/1e9)}B")
        elif is_profitable and ebitda > 0 and shares > 0:
            mult = SECTOR_MULTIPLES.get(sector,{}).get("ev_ebitda",12.0)
            iv   = max(0, (ebitda * mult - net_debt) / shares)
            return (fv(iv), f"EV/EBITDA {mult}x ({sector} - live)", f"EBITDA {fv(ebitda/1e9)}B x {mult}x")
        else:
            rev_use   = fwd_rev if fwd_rev > 0 else revenue
            rev_label = "forward" if fwd_rev > 0 else "TTM"
            if rev_use <= 0 or shares <= 0: return (None, None, None)
            mult = SECTOR_MULTIPLES.get(sector,{}).get("ev_rev", 8.0)
            if revenue > 0 and fwd_rev > revenue:
                growth = (fwd_rev - revenue) / revenue
                if growth > 0.5:   mult = round(mult * 1.3, 1)
                elif growth > 0.3: mult = round(mult * 1.15, 1)
            iv = max(0, (rev_use * mult - net_debt) / shares)
            return (fv(iv), f"EV/Revenue {mult}x {rev_label} (pre-profit - live)",
                    f"{fv(rev_use/1e9)}B {rev_label} rev x {mult}x minus net debt")
    except Exception:
        return (None, None, None)
# ──────────────────────────────────────────────────────────────────────────────

def ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

# ── Restore from query params on first load ──
def load_from_url():
    qp = st.query_params
    tickers = ['','','','','']
    shares  = ['','','','','']
    prices  = ['','','','','']
    holdings = [{'ticker':'','shares':'','cost':''} for _ in range(10)]
    for i in range(5):
        tickers[i] = qp.get(f't{i}','')
        shares[i]  = qp.get(f's{i}','')
        prices[i]  = qp.get(f'p{i}','')
    for i in range(10):
        holdings[i]['ticker'] = qp.get(f'ht{i}','')
        holdings[i]['shares'] = qp.get(f'hs{i}','')
        holdings[i]['cost']   = qp.get(f'hc{i}','')
    return tickers, shares, prices, holdings

def save_to_url():
    qp = {}
    for i in range(5):
        if st.session_state['tickers'][i]: qp[f't{i}'] = st.session_state['tickers'][i]
        if st.session_state['shares'][i]:  qp[f's{i}'] = st.session_state['shares'][i]
        # price field removed from inputs
    for i in range(10):
        h = st.session_state['holdings'][i]
        if h['ticker']: qp[f'ht{i}'] = h['ticker']
        if h['shares']: qp[f'hs{i}'] = h['shares']
        if h['cost']:   qp[f'hc{i}'] = h['cost']
    st.query_params.from_dict(qp)

# On first load restore from URL, then keep in session state
if 'initialized' not in st.session_state:
    t, s, p, h = load_from_url()
    st.session_state['tickers']  = t
    st.session_state['shares']   = s
    st.session_state['prices']   = p
    st.session_state['holdings'] = h
    st.session_state['initialized'] = True

ss('result', None)
ss('running', False)
ss('data_source', None)
ss('fmp_tickers', [])
ss('tickers', ['','','','',''])
ss('shares', ['','','','',''])
ss('prices', ['','','','',''])
ss('holdings', [{'ticker':'','shares':'','cost':''} for _ in range(15)])
# Ensure holdings list always has exactly 15 items (handles old saved state with 10)
while len(st.session_state['holdings']) < 15:
    st.session_state['holdings'].append({'ticker':'','shares':'','cost':''})
st.session_state['holdings'] = st.session_state['holdings'][:15]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:flex-end;gap:12px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #111c2a">
  <div style="width:8px;height:8px;background:#3b82f6;border-radius:50%;margin-bottom:4px;box-shadow:0 0 12px #3b82f6"></div>
  <div>
    <div style="font-size:9px;letter-spacing:4px;color:#3b82f6;text-transform:uppercase;margin-bottom:2px">Equity Research Terminal</div>
    <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#f0f6ff">STOCK ANALYZER — CLAUDE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── API key check ─────────────────────────────────────────────────────────────
# Try multiple ways to get the API key
api_key = ""
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except:
    pass
if not api_key:
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        pass
if not api_key:
    import os
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# ── FMP API key ──
import os as _os
fmp_key = ""
try:
    fmp_key = st.secrets["FMP_API_KEY"]
except:
    pass
if not fmp_key:
    try:
        fmp_key = st.secrets.get("FMP_API_KEY", "")
    except:
        pass
if not fmp_key:
    fmp_key = _os.environ.get("FMP_API_KEY", "")

# ── Finnhub key (real-time prices) ──
finnhub_key = ""
try:    finnhub_key = st.secrets["FINNHUB_API_KEY"]
except: pass
if not finnhub_key:
    try:    finnhub_key = st.secrets.get("FINNHUB_API_KEY","")
    except: pass
if not finnhub_key: finnhub_key = _os.environ.get("FINNHUB_API_KEY","")


if not api_key:
    st.markdown("""
    <div style="background:#150505;border:1px solid #dc2626;padding:20px;color:#f87171;font-size:13px;line-height:2">
      <div style="font-family:'Syne',sans-serif;font-size:11px;letter-spacing:2px;color:#f87171;margin-bottom:12px">⚠ API KEY NOT FOUND</div>
      <b>To fix this:</b><br>
      1. Go to your app on <b>share.streamlit.io</b><br>
      2. Click the <b>⋮ menu → Settings → Secrets</b><br>
      3. Paste this (with your real key):<br>
      <code style="background:#0a0000;padding:8px 12px;display:block;margin:8px 0;color:#fbbf24">ANTHROPIC_API_KEY = "sk-ant-..."</code>
      4. Click <b>Save</b> — the app restarts automatically<br><br>
      Get a key at <b>platform.anthropic.com → API Keys</b>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Stock inputs ──────────────────────────────────────────────────────────────
with st.expander("▸ STOCKS TO ANALYZE — ticker symbols only (up to 5)", expanded=True):
    for i in range(5):
        c1, c2, c3 = st.columns([0.5, 2, 2])
        with c1:
            st.markdown(f'<div style="font-size:9px;color:#93c5fd;font-family:Syne,sans-serif;font-weight:700;padding-top:8px">#{i+1}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="label">Ticker Symbol (e.g. AAPL)</div>', unsafe_allow_html=True)
            raw_tk = st.text_input(
                "Ticker Symbol", value=st.session_state['tickers'][i],
                placeholder="AAPL", max_chars=6, key=f"tk{i}",
                label_visibility="collapsed"
            )
            # Strip spaces and non-ticker chars — prevent "ROCKETLAB" type errors
            import re as _re_tk
            st.session_state['tickers'][i] = _re_tk.sub(r'[^A-Z0-9.-]', '', raw_tk.upper().strip())
        with c3:
            st.markdown('<div class="label">Shares to Buy</div>', unsafe_allow_html=True)
            st.session_state['shares'][i] = st.text_input(
                "Shares", value=st.session_state['shares'][i],
                placeholder="0", key=f"sh{i}", label_visibility="collapsed"
            )
        # Price to Buy field removed — entry price is AI-suggested in output
        st.session_state['prices'][i] = ''

# ── Portfolio ─────────────────────────────────────────────────────────────────
with st.expander("▸ MY PORTFOLIO — UP TO 15 HOLDINGS (optional)"):

    # ── GROUP 1: Import or Manual toggle ──
    st.markdown('<div class="label" style="margin-bottom:8px">How would you like to enter your portfolio?</div>', unsafe_allow_html=True)
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button("📥 Import from Google Sheets", use_container_width=True, key="btn_mode_import"):
            st.session_state['portfolio_mode'] = 'import'
    with mode_col2:
        if st.button("✏️ Enter Manually", use_container_width=True, key="btn_mode_manual"):
            st.session_state['portfolio_mode'] = 'manual'

    port_mode = st.session_state.get('portfolio_mode', 'manual')

    # ── Import mode ──
    if port_mode == 'import':
        st.markdown('''
        <div style="background:#090f1a;border:1px solid #1a2e48;padding:12px 14px;margin:10px 0">
          <div style="font-size:9px;letter-spacing:2px;color:#3b82f6;text-transform:uppercase;margin-bottom:8px">📊 Google Sheets Setup</div>
          <div style="font-size:11px;color:#94a3b8;line-height:2">
            1. Create a Google Sheet with columns: <b style="color:#e2e8f0">Ticker | Shares | Avg Cost</b><br>
            2. Click <b style="color:#e2e8f0">File → Share → Publish to web</b><br>
            3. Select <b style="color:#e2e8f0">Comma-separated values (.csv)</b> → click <b style="color:#e2e8f0">Publish</b><br>
            4. Copy the URL and paste it below
          </div>
        </div>
        ''', unsafe_allow_html=True)

        st.text_input(
            "Google Sheet Published CSV URL",
            value=st.session_state.get('gs_url',''),
            placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv",
            key="gs_url_input"
        )
        do_import = st.button("🚀 Run Import", use_container_width=True, key="btn_do_import")

        if do_import:
            gs_url = st.session_state.get('gs_url_input','').strip()
            if not gs_url:
                st.error("Please paste a Google Sheets URL first.")
            else:
                with st.spinner("Fetching your portfolio..."):
                    try:
                        import urllib.request as _ur
                        import csv as _csv
                        import io as _io
                        import re as _re_gs
                        url = gs_url.strip()
                        # Accept any of these URL formats:
                        # 1. Already a published CSV: .../pub?...output=csv  (use as-is)
                        # 2. /d/e/ export format: already valid, ensure output=csv
                        # 3. Regular edit URL: convert to published CSV
                        if 'output=csv' in url:
                            pass  # already correct format
                        elif '/pub?' in url:
                            url = url + ('&output=csv' if '?' in url else '?output=csv')
                        else:
                            match = _re_gs.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
                            if match:
                                sheet_id = match.group(1)
                                url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/pub?output=csv'
                            else:
                                st.error('Could not parse the Google Sheets URL. Please use the published CSV URL from File > Share > Publish to web.')
                                st.stop()

                        with _ur.urlopen(url, timeout=10) as r:
                            raw_csv = r.read().decode('utf-8-sig')

                        reader = _csv.DictReader(_io.StringIO(raw_csv))
                        rows = list(reader)

                        if not rows:
                            st.error("The sheet appears empty. Make sure it has at least one row of data below the header.")
                        else:
                            # Auto-detect columns
                            headers = {k.lower().strip(): k for k in rows[0].keys()}
                            def find_col(candidates):
                                for cand in candidates:
                                    for h_low, h_orig in headers.items():
                                        if cand in h_low: return h_orig
                                return None

                            ticker_col = find_col(['ticker','symbol','stock'])
                            shares_col = find_col(['shares','quantity','qty','units'])
                            cost_col   = find_col(['avg cost','average cost','cost basis','avg price','average price','cost per','price'])

                            if not ticker_col:
                                st.error(f"Could not find a Ticker/Symbol column. Columns in your sheet: **{', '.join(rows[0].keys())}**")
                            elif not shares_col:
                                st.error(f"Could not find a Shares/Quantity column. Columns in your sheet: **{', '.join(rows[0].keys())}**")
                            else:
                                parsed = []
                                skipped = []
                                for row in rows:
                                    tk  = re.sub(r'[^A-Z0-9.-]', '', str(row.get(ticker_col,'')).upper().strip())
                                    sh  = re.sub(r'[^0-9.]', '', str(row.get(shares_col,'')).strip())
                                    cst = re.sub(r'[^0-9.]', '', str(row.get(cost_col,'') if cost_col else '').strip())
                                    if tk and sh:
                                        parsed.append({'ticker': tk, 'shares': sh, 'cost': cst})
                                    elif tk:
                                        skipped.append(tk)

                                if not parsed:
                                    st.error("No valid holdings found. Make sure Ticker and Shares columns have data.")
                                else:
                                    # Sort by market value desc, take top 15, then alphabetically
                                    def mkt_val(h):
                                        try: return float(h['shares']) * float(h['cost']) if h['cost'] else float(h['shares'])
                                        except: return 0
                                    parsed.sort(key=mkt_val, reverse=True)
                                    parsed = parsed[:15]
                                    parsed.sort(key=lambda h: h['ticker'])

                                    # Clear all 15 slots then fill
                                    st.session_state['holdings'] = [{'ticker':'','shares':'','cost':''} for _ in range(15)]
                                    for i, h in enumerate(parsed):
                                        st.session_state['holdings'][i] = h
                                        st.session_state[f'htk{i}'] = h['ticker']
                                        st.session_state[f'hsh{i}'] = h['shares']
                                        st.session_state[f'hco{i}'] = h['cost']
                                    for i in range(len(parsed), 15):
                                        st.session_state[f'htk{i}'] = ''
                                        st.session_state[f'hsh{i}'] = ''
                                        st.session_state[f'hco{i}'] = ''
                                    st.session_state['gs_url'] = gs_url
                                    st.session_state['portfolio_mode'] = 'manual'  # switch to manual view to show results

                                    msg = f"✓ Imported {len(parsed)} holdings"
                                    if len(parsed) == 15: msg += " (top 15 by market value)"
                                    if skipped: msg += f" · Skipped {len(skipped)} rows with missing shares"
                                    st.success(msg)
                                    st.rerun()

                    except Exception as e:
                        err_msg = str(e)
                        if '404' in err_msg:
                            st.error('Import failed: Sheet not found. Your sheet must be Published to the web as CSV. Go to File > Share > Publish to web > select CSV format > Publish. Then copy that URL here.')
                        elif '403' in err_msg or 'permission' in err_msg.lower():
                            st.error('Import failed: Permission denied. Make sure the sheet is published publicly, not just shared.')
                        elif 'timeout' in err_msg.lower():
                            st.error('Import failed: Connection timed out. Check your internet connection and try again.')
                        else:
                            st.error('Import failed. Please check your URL and make sure the sheet is published as CSV.')


    # ── GROUP 2: Holdings table (shown in both modes) ──
    filled = sum(1 for h in st.session_state['holdings'] if h.get('ticker'))
    st.markdown(
        f'<div style="font-size:10px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin:12px 0 4px">Holdings ({filled}/15 filled) — Ticker · Shares · Avg Cost</div>'
        '<div style="font-size:11px;color:#3b82f6;margin-bottom:8px">ℹ️ These are your existing holdings used for portfolio context. Enter stocks to analyze in the section above.</div>',
        unsafe_allow_html=True)
    # Initialize widget keys from holdings if not already set
    for i in range(15):
        if f'htk{i}' not in st.session_state:
            st.session_state[f'htk{i}'] = st.session_state['holdings'][i].get('ticker','')
        if f'hsh{i}' not in st.session_state:
            st.session_state[f'hsh{i}'] = st.session_state['holdings'][i].get('shares','')
        if f'hco{i}' not in st.session_state:
            st.session_state[f'hco{i}'] = st.session_state['holdings'][i].get('cost','')

    for i in range(15):
        c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
        with c1:
            st.markdown(f'<div style="font-size:9px;color:#fff;padding-top:8px">#{i+1}</div>', unsafe_allow_html=True)
        with c2:
            # Use key only — no value= to avoid session state conflict
            st.text_input(
                f"HTk{i}", placeholder="MSFT", max_chars=6,
                key=f"htk{i}", label_visibility="collapsed"
            )
            st.session_state['holdings'][i]['ticker'] = st.session_state[f'htk{i}'].upper().strip()
        with c3:
            st.text_input(
                f"HSh{i}", placeholder="Shares",
                key=f"hsh{i}", label_visibility="collapsed"
            )
            st.session_state['holdings'][i]['shares'] = st.session_state[f'hsh{i}']
        with c4:
            st.text_input(
                f"HCo{i}", placeholder="Avg $",
                key=f"hco{i}", label_visibility="collapsed"
            )
            st.session_state['holdings'][i]['cost'] = st.session_state[f'hco{i}']

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

# Save current inputs to URL so they survive refresh
save_to_url()

# ── Top-level derived variables (available throughout the page) ──
port_holds = [h for h in st.session_state['holdings'] if h.get('ticker') and h.get('shares') and h.get('cost')]
port_val   = sum(float(h['shares']) * float(h['cost']) for h in port_holds)
valid_tickers = [t for t in st.session_state['tickers'] if t]

# ── Analyze button ────────────────────────────────────────────────────────────
# valid_tickers derived from session_state above
btn_label = f"ANALYZE {len(valid_tickers)} STOCK{'S' if len(valid_tickers)!=1 else ''}" if valid_tickers else "ENTER A TICKER TO ANALYZE"



# ── Button row: Analyze | Stop | Clear ──
is_running = st.session_state['running']


# Analyze via st.button (must be Streamlit widget)
analyze_clicked = st.button(
    btn_label,
    disabled=not valid_tickers or is_running,
    use_container_width=True,
    key="btn_analyze"
)

# Stop + Clear as st.button — no new tab issue
sc1, sc2 = st.columns(2)
with sc1:
    stop_clicked = st.button('■ STOP', disabled=not is_running, use_container_width=True, key='btn_stop')
    if stop_clicked:
        st.session_state['running'] = False
        st.session_state['stop_requested'] = True
        st.rerun()
with sc2:
    clear_clicked = st.button('✕ CLEAR', use_container_width=True, key='btn_clear')
    if clear_clicked:
        for _k in ['result','running','data_source','fmp_tickers','stop_requested','do_analyze',
                   'fmp_raw_data','fmp_locked','finnhub_prices','finnhub_sentiment_data','raw_response']:
            if _k in ('result','data_source','raw_response'): st.session_state[_k] = None
            elif _k in ('running','stop_requested','do_analyze'): st.session_state[_k] = False
            elif _k == 'fmp_tickers': st.session_state[_k] = []
            else: st.session_state[_k] = {}
        st.session_state['tickers']  = ['','','','','']
        st.session_state['shares']   = ['','','','','']
        st.session_state['prices']   = ['','','','','']
        st.session_state['holdings'] = [{'ticker':'','shares':'','cost':''} for _ in range(15)]
        st.session_state['initialized'] = False
        st.query_params.clear()
        st.rerun()

# Inject CSS for stop/clear button colors
st.markdown('<style>'
    'div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(1) button {'
    'background-color:#2d0a0a !important;border:1px solid #f87171 !important;color:#fca5a5 !important;}'
    'div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(1) button:disabled {'
    'background-color:#1a0808 !important;border:1px solid #7f1d1d !important;color:#7f1d1d !important;opacity:1 !important;}'
    'div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) button {'
    'background-color:#2d2500 !important;border:1px solid #fbbf24 !important;color:#fde68a !important;}'
    '</style>', unsafe_allow_html=True)


ss('stop_requested', False)
ss('raw_response', None)
ss('fmp_raw_data', {})
ss('fmp_locked', {})
ss('finnhub_prices', {})
ss('finnhub_sentiment_data', {})
ss('gs_url', '')
ss('portfolio_mode', 'manual')

if analyze_clicked and not st.session_state['running']:
    # Phase 1: set running=True and rerun so Stop button activates BEFORE analysis starts
    st.session_state['running'] = True
    st.session_state['stop_requested'] = False
    st.session_state['result'] = None
    st.session_state['do_analyze'] = True
    st.rerun()

ss('do_analyze', False)

if st.session_state.get('do_analyze') and st.session_state['running']:
    # Phase 2: page has re-rendered with Stop enabled, now run analysis
    st.session_state['do_analyze'] = False

    port_holds = [h for h in st.session_state['holdings'] if h.get('ticker') and h.get('shares') and h.get('cost')]
    port_val = sum(float(h['shares']) * float(h['cost']) for h in port_holds)

    if port_holds:
        port_note = f"Portfolio ({len(port_holds)} holdings ~${port_val:,.0f}): " + \
            ", ".join(f"{h['ticker']} {h['shares']}sh@${h['cost']}" for h in port_holds)
    else:
        port_note = "No portfolio."

    cand_list = []
    for i, tk in enumerate(valid_tickers):
        sh = st.session_state['shares'][i] if i < len(st.session_state['shares']) else ''
        pr = st.session_state['prices'][i] if i < len(st.session_state['prices']) else ''
        part = tk
        if sh: part += f" {sh}sh"
        if pr: part += f" buy@${pr}"
        cand_list.append(part)
    cand_str = ", ".join(cand_list)

    prompt = f"""You are a senior equity analyst. Analyze these stocks: {cand_str}. {port_note}
Live financial data will be appended below. IMPORTANT: Use the EXACT Current Price from the live data for the currentPrice field in your JSON response. Do NOT use your training data prices — they are outdated.

Return ONLY valid JSON (no markdown, no explanation):
{{
  "top2":[{{"ticker":"X","rank":1,"companyName":"...","score":"8.5/10","buyReason":"one sentence","entryNote":"one sentence"}},{{"ticker":"X","rank":2,"companyName":"...","score":"7.5/10","buyReason":"one sentence","entryNote":"one sentence"}}],
  "rankingSummary":"one sentence why these two",
  "comparisonTable":[{{"ticker":"X","companyName":"...","currentPrice":"$X","intrinsicValue":"$X","entryPrice":"$X","analystConsensus":"$X","overallScore":"X/10","verdictStock":"BULLISH","verdictPortfolio":"BULLISH","keyStrength":"...","keyRisk":"..."}}],
  "stocks":{{
    "TICKER":{{
      "ticker":"RESOLVED_SYMBOL","inputAs":"original input string","companyName":"Full Company Name","currentPrice":"$X","summary":"one sentence",
      "verdictStock":"BULLISH","verdictStockReason":"one sentence",
      "verdictPortfolio":"BULLISH","verdictPortfolioReason":"one sentence",
      "sentimentScore":70,
      "portfolioInsights":{{"concentrationRisk":"...","sectorOverlap":"...","correlationNote":"...","diversificationImpact":"...","recommendation":"..."}},
      "pricing":{{"intrinsicValue":"$X (note: if FMP DCF data is provided it will override this)","intrinsicMethod":"Blended","entryPrice":"$X — suggested entry price","entryRationale":"Based on: (1) intrinsic value with 15% margin of safety, (2) key technical support levels from 1-year price chart (50-day MA, 200-day MA, major support zones), and (3) historical price behavior near these levels. Cite the specific support level or MA that anchors this price.","analystConsensus":"$X","targetRange":"$X-$X"}},
      "ivBreakdown":[{{"method":"DCF","value":"$X","desc":"..."}},{{"method":"EV/EBITDA","value":"$X","desc":"..."}},{{"method":"Fwd P/E","value":"$X","desc":"..."}},{{"method":"P/FCF","value":"$X","desc":"..."}}],
      "topAnalysts":[{{"name":"...","firm":"...","accuracyPct":"XX%","rating":"Buy","target":"$X","thesis":"..."}}],
      "fundamentals":{{"revenue":{{"v":"$XB","sig":"good"}},"grossMargin":{{"v":"X%","sig":"good"}},"operatingMargin":{{"v":"X%","sig":"good"}},"netMargin":{{"v":"X%","sig":"good"}},"eps":{{"v":"$X","sig":"good"}},"forwardEPS":{{"v":"$X","sig":"ok"}},"peRatio":{{"v":"Xx","sig":"ok"}},"forwardPE":{{"v":"Xx","sig":"ok"}},"evEbitda":{{"v":"Xx","sig":"ok"}},"debtToEquity":{{"v":"X.X","sig":"ok"}},"freeCashFlow":{{"v":"$XB","sig":"good"}},"roe":{{"v":"X%","sig":"good"}},"divYield":{{"v":"X%","sig":"ok"}}}},
      "sectorAnalysis":{{
        "sector":"Sector name",
        "sectorOutlook":"1 sentence",
        "peerComparison":[
          {{"peer":"Ticker","metric":"P/E","peerVal":"X×","stockVal":"X×","verdict":"Premium/Discount/Inline"}},
          {{"peer":"Ticker","metric":"Rev Growth","peerVal":"X%","stockVal":"X%","verdict":"Above/Below/Inline"}},
          {{"peer":"Ticker","metric":"Net Margin","peerVal":"X%","stockVal":"X%","verdict":"Above/Below/Inline"}}
        ],
        "sectorRank":"Top quartile/Mid-tier/Laggard",
        "sectorCatalysts":"1 sentence",
        "sectorRisks":"1 sentence"
      }},
      "riskAnalysis":{{
        "overallRiskRating":"Low/Medium/High/Very High",
        "riskScore":65,
        "businessRisk":"1 sentence",
        "financialRisk":"1 sentence",
        "macroRisk":"1 sentence",
        "regulatoryRisk":"1 sentence",
        "valuationRisk":"1 sentence",
        "keyRisks":[
          {{"risk":"description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"1 sentence"}},
          {{"risk":"description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"1 sentence"}},
          {{"risk":"description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"1 sentence"}}
        ],
        "bearCasePrice":"$X","bullCasePrice":"$X"
      }},
      "sections":{{"valuation":"1-2 sentences","momentum":"1-2 sentences","sentiment":"1-2 sentences"}}
    }}
  }}
}}
CRITICAL — stocks{{}} MUST contain ALL {len(valid_tickers)} resolved tickers (one per input): inputs were [{', '.join(valid_tickers)}]. comparisonTable[] must have all {len(valid_tickers)}. top2[] picks best 2 but ALL appear in stocks{{}}. Include 5 analysts per stock, thesis max 8 words.
SECTOR-AWARE VALUATION — FIRST check if the company is profitable:

PRE-PROFIT / HIGH-GROWTH COMPANIES (negative earnings, negative FCF, negative EBITDA — e.g. RKLB, IONQ, JOBY, LUNR, ASTR, early-stage biotech/space/EV):
- DO NOT use standard DCF, EV/EBITDA, or P/E — they will produce misleading low values
- USE THESE MODELS INSTEAD:
  1. EV/Revenue: compare to high-growth peers (space: 10-25x revenue; SaaS: 8-20x; EV: 3-8x)
  2. Forward DCF on projected profitability: use analyst consensus FCF estimates for 2026-2028 when company turns profitable, discount back at WACC 12-15%
  3. P/S (Price/Sales): compare to sector peers at similar growth rates
  4. Scenario-weighted value: bull case (full execution) × 40% + base case × 40% + bear case × 20%
- NOTE in ivBreakdown: "Pre-profit company — traditional DCF/P/E not applicable. Using EV/Revenue and forward estimates."
- Analyst consensus targets for these stocks often lag the market significantly — note this explicitly

PROFITABLE COMPANIES:
Utilities (VST,NEE,DUK etc): WACC 7-9%, DCF terminal growth 1.5-2.5%, normalized FCF (3yr avg), EV/EBITDA 8-12x, P/E 14-18x, subtract actual net debt.
Tech/Growth profitable (NVDA,MSFT,AAPL etc): WACC 9-12%, growth 2.5-4%, EV/EBITDA 20-40x, P/E 20-35x.
Financials: use P/B 1-2x and P/E, skip EV/EBITDA.
Industrials/Energy: WACC 8-10%, EV/EBITDA 6-10x, cycle-normalized earnings.
Show actual inputs in desc field e.g. "WACC 8.2%, g 2%, normalized FCF $1.8B" or "EV/Revenue 15x on $601M TTM revenue".
For sectorAnalysis.peerComparison use 3-4 real sector peers. For riskAnalysis list 3 specific key risks.
ENTRY PRICE METHODOLOGY — use ALL three inputs together:
1. VALUATION FLOOR: intrinsic value × 0.85 (15% margin of safety)
2. TECHNICAL SUPPORT: identify the strongest support level from the 1-year chart — 50-day MA, 200-day MA, prior consolidation zones, or recent swing lows. Use whichever is most relevant and actionable.
3. FINAL ENTRY: the higher of (valuation floor) and (nearest technical support below current price). If the stock is already below intrinsic value, the entry may be at or near current price.
Always explain which factor drove the entry price in entryRationale.
Sections text: 2 sentences each, not 10 words — be informative."""

    # ── Step 1: Clean and validate ticker symbols ──
    resolved_tickers = [re.sub(r'[^A-Z0-9.-]', '', vt.upper().strip()) for vt in valid_tickers]
    resolved_tickers = [t for t in resolved_tickers if t]
    st.write(f"Validating tickers: {', '.join(resolved_tickers)}...")

    # Validate each ticker — check Finnhub returns a real price
    invalid_tickers = []
    if finnhub_key:
        for tk in resolved_tickers:
            fh = finnhub_quote(tk, finnhub_key)
            if not fh.get("c") or fh.get("c", 0) == 0:
                invalid_tickers.append(tk)
        if invalid_tickers:
            st.error(
                f"⚠ Invalid ticker symbol{'s' if len(invalid_tickers)>1 else ''}: "
                f"**{', '.join(invalid_tickers)}**\n\n"
                f"Please enter valid stock ticker symbols (e.g. AAPL, NVDA, RKLB). "
                f"Company names are not supported."
            )
            st.session_state['running'] = False
            st.stop()
    st.write(f"✓ Tickers valid: {', '.join(resolved_tickers)}")

    with st.status("Analyzing stocks...", expanded=True) as status:
        st.write(f"Resolving tickers and fetching live data...")
        st.info("💡 Keep this tab open and active during analysis. Streamlit pauses when the tab is hidden on mobile browsers.")
        try:
            if st.session_state.get('stop_requested'):
                st.warning("Analysis stopped by user.")
                st.session_state['running'] = False
                st.stop()
            client = anthropic.Anthropic(api_key=api_key)

            # ── Step 2: Fetch FMP fundamentals + Finnhub real-time prices in parallel ──
            fmp_contexts   = {}
            finnhub_prices = {}
            local_raw_data = {}   # initialize here so Step 3 always has it in scope
            local_sentiment= {}

            if fmp_key:
                st.write(f"Fetching live market data for {', '.join(resolved_tickers)}...")
                # Fetch FMP + Finnhub simultaneously
                def fetch_ticker(tk):
                    import re as _re2
                    clean_tk = _re2.sub(r'[^A-Z0-9.-]', '', tk.upper().strip())
                    fmp_raw  = fmp_fetch_all(clean_tk, fmp_key)
                    fh_quote = finnhub_quote(clean_tk, finnhub_key) if finnhub_key else {}
                    fh_sent  = finnhub_sentiment(clean_tk, finnhub_key) if finnhub_key else {}
                    # Finnhub earnings calendar (more reliable than FMP free tier)
                    fh_earn  = {}
                    if finnhub_key:
                        try:
                            import urllib.parse as _up
                            from datetime import datetime as _dt3, timedelta as _td3
                            today  = _dt3.now().strftime("%Y-%m-%d")
                            future = (_dt3.now() + _td3(days=365)).strftime("%Y-%m-%d")
                            url = f"https://finnhub.io/api/v1/calendar/earnings?symbol={clean_tk}&from={today}&to={future}&token={finnhub_key}"
                            with urllib.request.urlopen(url, timeout=8) as r:
                                fh_earn = json.loads(r.read().decode())
                        except Exception:
                            fh_earn = {}
                    return tk, fmp_raw, fh_quote, fh_sent, fh_earn

                # Collect all results in local dicts first — thread-safe
                local_raw_data  = {}
                local_sentiment = {}
                with ThreadPoolExecutor(max_workers=5) as ex:
                    futures = {ex.submit(fetch_ticker, tk): tk for tk in resolved_tickers}
                    for fut in as_completed(futures):
                        tk, raw, fh, fh_sent, fh_earn = fut.result()
                        if fh.get("c") and fh["c"] > 0:
                            if isinstance(raw.get("quote"), list) and raw["quote"]:
                                raw["quote"][0]["price"] = fh["c"]
                                raw["quote"][0]["changesPercentage"] = fh.get("dp", 0)
                            elif isinstance(raw.get("quote"), dict):
                                raw["quote"]["price"] = fh["c"]
                                raw["quote"]["changesPercentage"] = fh.get("dp", 0)
                            else:
                                raw["quote"] = [{"price": fh["c"], "changesPercentage": fh.get("dp",0)}]
                            finnhub_prices[tk] = fh
                            src = f"Finnhub ${fh['c']:,.2f} (real-time) + FMP (fundamentals)"
                        elif fh.get("_error"):
                            src = f"FMP only — Finnhub error: {fh['_error']}"
                        else:
                            src = "FMP only (Finnhub returned no price)"
                        fmp_contexts[tk] = format_fmp_context(tk, raw)
                        local_raw_data[tk] = raw
                        if fh_sent:
                            local_sentiment[tk] = fh_sent
                        if fh_earn:
                            raw['_fh_earnings'] = fh_earn
                        st.write(f"  ✓ {tk} data fetched ({src})")
                # Assign to session_state AFTER all threads complete
                st.session_state['fmp_raw_data']          = local_raw_data
                st.session_state['finnhub_prices']        = finnhub_prices
                st.session_state['finnhub_sentiment_data']= local_sentiment
                st.write(f"  FMP data stored: {list(local_raw_data.keys())}")
            else:
                st.warning("⚠ FMP_API_KEY not set — using Claude training data only.")

            # ── Step 3: Extract key numbers from FMP and build locked data block ──
            # These numbers are extracted directly and injected as REQUIRED values
            # Claude MUST use them — they are not suggestions
            locked_data = {}  # ticker -> dict of locked fields
            live_data_block = ""

            # Use local_raw_data directly (guaranteed in scope)
            if fmp_contexts and local_raw_data:
                fmp_raw = local_raw_data
                locked_lines = []
                for tk, raw_fmp in fmp_raw.items():
                    locked = {}
                    # Current price
                    q = (raw_fmp.get("quote") or [{}])
                    q = q[0] if isinstance(q, list) and q else q if isinstance(q, dict) else {}
                    if q.get("price"):
                        p = q["price"]
                        locked["currentPrice"] = f"${p:,.2f}" if isinstance(p,(int,float)) else f"${p}"
                        locked["52wkHigh"]  = q.get("yearHigh","N/A")
                        locked["52wkLow"]   = q.get("yearLow","N/A")
                        locked["mktCap"]    = q.get("marketCap","N/A")
                        locked["pe"]        = q.get("pe","N/A")
                        locked["ma50"]      = q.get("priceAvg50","N/A")
                        locked["ma200"]     = q.get("priceAvg200","N/A")
                    # Analyst consensus target
                    tgt = raw_fmp.get("targets")
                    if isinstance(tgt, list) and tgt: tgt = tgt[0]
                    if isinstance(tgt, dict) and tgt.get("targetConsensus"):
                        tc = tgt["targetConsensus"]
                        locked["analystConsensus"] = f"${tc}" if not str(tc).startswith("$") else str(tc)
                        locked["analystTargetHigh"] = tgt.get("targetHigh","N/A")
                        locked["analystTargetLow"]  = tgt.get("targetLow","N/A")
                        locked["analystTargetMedian"] = tgt.get("targetMedian","N/A")
                    # FMP DCF
                    dcf = raw_fmp.get("dcf")
                    if isinstance(dcf, list) and dcf: dcf = dcf[0]
                    if isinstance(dcf, dict) and dcf.get("dcf"):
                        locked["fmpDCF"] = f"${dcf['dcf']}"
                    # Key ratios
                    r = (raw_fmp.get("ratios") or [{}])
                    r = r[0] if isinstance(r, list) and r else r if isinstance(r, dict) else {}
                    if r:
                        def fmt_r(v):
                            if v is None: return "N/A"
                            try: return f"{float(v):.2f}"
                            except: return str(v)
                        locked["peRatio"]   = fmt_r(r.get("peRatioTTM"))
                        locked["evEbitda"]  = fmt_r(r.get("enterpriseValueMultipleTTM"))
                        locked["psRatio"]   = fmt_r(r.get("priceToSalesRatioTTM"))
                        locked["netMargin"] = f"{float(r.get('netProfitMarginTTM',0))*100:.1f}%" if r.get("netProfitMarginTTM") else "N/A"
                        locked["grossMargin"] = f"{float(r.get('grossProfitMarginTTM',0))*100:.1f}%" if r.get("grossProfitMarginTTM") else "N/A"
                        locked["roe"]       = f"{float(r.get('returnOnEquityTTM',0))*100:.1f}%" if r.get("returnOnEquityTTM") else "N/A"
                        locked["debtEq"]    = fmt_r(r.get("debtEquityRatioTTM"))
                        locked["fcfYield"]  = f"{float(r.get('freeCashFlowYieldTTM',0))*100:.1f}%" if r.get("freeCashFlowYieldTTM") else "N/A"
                    # Income
                    inc = (raw_fmp.get("income") or [{}])
                    inc = inc[0] if isinstance(inc, list) and inc else {}
                    if inc:
                        def fm(v):
                            if v is None: return "N/A"
                            try:
                                n=float(v)
                                if abs(n)>=1e9: return f"${n/1e9:.2f}B"
                                if abs(n)>=1e6: return f"${n/1e6:.1f}M"
                                return f"${n:,.0f}"
                            except: return str(v)
                        locked["revenue"]  = fm(inc.get("revenue"))
                        locked["ebitda"]   = fm(inc.get("ebitda"))
                        locked["netIncome"]= fm(inc.get("netIncome"))
                        locked["eps"]      = str(inc.get("eps","N/A"))
                    # Forward estimates
                    est = (raw_fmp.get("estimates") or [{}])
                    est = est[0] if isinstance(est, list) and est else {}
                    if est:
                        locked["fwdEPS"]        = str(est.get("estimatedEpsAvg","N/A"))
                        locked["fwdRevenue"]     = fm(est.get("estimatedRevenueAvg")) if est.get("estimatedRevenueAvg") else "N/A"
                        locked["numAnalysts"]    = str(est.get("numberAnalystEstimatedRevenue","N/A"))

                    # Next earnings — try Finnhub first (more reliable), then FMP
                    from datetime import datetime as _dt
                    today_str = _dt.now().strftime("%Y-%m-%d")
                    earn_found = False
                    # Try Finnhub earnings calendar
                    fh_earn_data = raw_fmp.get('_fh_earnings', {})
                    fh_earn_list = fh_earn_data.get('earningsCalendar', []) if isinstance(fh_earn_data, dict) else []
                    if fh_earn_list:
                        fh_future = [e for e in fh_earn_list if e.get('date','') >= today_str]
                        fh_future.sort(key=lambda x: x.get('date',''))
                        if fh_future:
                            ne = fh_future[0]
                            locked["nextEarningsDate"]   = ne.get("date","N/A")
                            locked["nextEarningsEPS"]    = ne.get("epsEstimated","N/A")
                            locked["nextEarningsTiming"] = ne.get("hour","N/A")
                            earn_found = True
                    # Fallback: FMP earnings calendar
                    if not earn_found:
                        earn_up   = raw_fmp.get("earnings_upcoming") or []
                        earn_hist = raw_fmp.get("earnings_next") or []
                        earn_combined = []
                        for src2 in [earn_up, earn_hist]:
                            if isinstance(src2, list): earn_combined.extend(src2)
                            elif isinstance(src2, dict) and src2.get("earningsCalendar"):
                                earn_combined.extend(src2["earningsCalendar"])
                        future_earns = sorted(
                            [e for e in earn_combined if e.get("date","") >= today_str],
                            key=lambda x: x.get("date","")
                        )
                        if future_earns:
                            ne = future_earns[0]
                            locked["nextEarningsDate"]   = ne.get("date","N/A")
                            locked["nextEarningsEPS"]    = ne.get("epsEstimated","N/A")
                            locked["nextEarningsTiming"] = ne.get("time","N/A")

                    # Calculate IV using correct model for this company type
                    iv_val_c, iv_meth_c, iv_desc_c = calc_intrinsic_value(raw_fmp)
                    if iv_val_c:
                        locked['calcIV']       = iv_val_c
                        locked['calcIVMethod'] = iv_meth_c
                        locked['calcIVDesc']   = iv_desc_c

                    # Add Finnhub news sentiment to locked data
                    fh_sent_data = st.session_state.get('finnhub_sentiment_data', {}).get(tk, {})
                    if fh_sent_data:
                        buzz  = fh_sent_data.get('buzz', {})
                        sent  = fh_sent_data.get('sentiment', {})
                        locked['buzzScore']          = buzz.get('buzz', 'N/A')
                        locked['buzzArticlesWeekly'] = buzz.get('weeklyAverage', 'N/A')
                        locked['sentimentBullish']   = sent.get('bullishPercent', 'N/A')
                        locked['sentimentBearish']   = sent.get('bearishPercent', 'N/A')
                        locked['companyNewsScore']   = fh_sent_data.get('companyNewsScore', 'N/A')
                        locked['sectorAvgBullish']   = fh_sent_data.get('sectorAverageBullishPercent', 'N/A')
                        locked['sectorNewsScore']    = fh_sent_data.get('sectorAverageNewsScore', 'N/A')

                    locked_data[tk] = locked

                    # Build locked data section for prompt
                    locked_lines.append(f"\n--- LOCKED LIVE DATA FOR {tk} (from FMP/Finnhub — use these exact values) ---")
                    for k, v in locked.items():
                        locked_lines.append(f"  {k}: {v}")
                    # Explain sentiment fields
                    if locked.get("buzzScore") not in (None,"N/A"):
                        locked_lines.append(f"  [Finnhub News Sentiment] buzzScore={locked.get('buzzScore')} (higher=more buzz vs historical avg)")
                        locked_lines.append(f"  [Finnhub News Sentiment] bullish%={locked.get('sentimentBullish')} bearish%={locked.get('sentimentBearish')}")
                        locked_lines.append(f"  [Finnhub News Sentiment] companyNewsScore={locked.get('companyNewsScore')} (0-1, higher=more positive)")
                        locked_lines.append(f"  [Finnhub News Sentiment] sectorAvgBullish%={locked.get('sectorAvgBullish')} (benchmark)")
                    locked_lines.append(f"--- END LOCKED DATA FOR {tk} ---")

                live_data_block = (
                    "\n\n=== FINANCIAL MODELING PREP LIVE DATA ==="
                    "\nTHESE ARE MANDATORY VALUES. You MUST use them exactly as provided."
                    "\nDo NOT substitute your own estimates. Do NOT use training data prices."
                    "\nThe currentPrice, analystConsensus, and all ratios below are real-time."
                    "\n" + "\n".join(locked_lines) +
                    "\n\n" + "\n\n".join(fmp_contexts.values()) +
                    "\n=== END FMP DATA ==="
                )

                # Also store locked_data for post-processing override
                st.session_state['fmp_locked'] = locked_data

            enriched_prompt = prompt + live_data_block

            if st.session_state.get('stop_requested'):
                st.warning("Analysis stopped.")
                st.session_state['running'] = False
                st.stop()

            st.write("Running AI analysis and valuations...")
            progress_bar = st.progress(0, text="Claude is thinking...")
            token_counter = [0]
            txt_chunks = []

            # ── Use streaming so UI stays responsive and Stop works ──
            with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=16000,
                messages=[{"role": "user", "content": enriched_prompt}]
            ) as stream:
                for text_chunk in stream.text_stream:
                    # Check stop flag on every chunk
                    if st.session_state.get('stop_requested'):
                        st.warning("Analysis stopped by user.")
                        st.session_state['running'] = False
                        st.stop()
                    txt_chunks.append(text_chunk)
                    token_counter[0] += 1
                    # Update progress bar periodically
                    if token_counter[0] % 50 == 0:
                        pct = min(0.95, token_counter[0] / 800)
                        progress_bar.progress(pct, text=f"Generating analysis... ({token_counter[0] * 4 // 1000}K tokens)")

            progress_bar.progress(1.0, text="Finalizing...")
            st.write("Building report...")
            txt = "".join(txt_chunks)
            parsed = parse_json(txt)
            if not parsed:
                st.error(f"Could not parse response. Raw preview: {txt[:400]}")
                st.session_state['raw_response'] = txt
            else:
                # ── Hard override: inject ALL locked FMP values into parsed JSON ──
                locked = st.session_state.get('fmp_locked', {})
                if locked and parsed.get("stocks"):
                    for tk_key, lk in locked.items():
                        for sk in list(parsed["stocks"].keys()):
                            if sk.upper() == tk_key.upper():
                                s_data = parsed["stocks"][sk]
                                if lk.get("currentPrice"):
                                    s_data["currentPrice"] = lk["currentPrice"]
                                if "pricing" not in s_data or not s_data["pricing"]:
                                    s_data["pricing"] = {}
                                if lk.get("analystConsensus"):
                                    s_data["pricing"]["analystConsensus"] = lk["analystConsensus"]
                                if lk.get("analystTargetHigh") and lk.get("analystTargetLow"):
                                    s_data["pricing"]["targetRange"] = f"${lk['analystTargetLow']} – ${lk['analystTargetHigh']}"
                                # Python-calculated IV — right model per company type
                                if lk.get('calcIV'):
                                    s_data['pricing']['intrinsicValue']  = lk['calcIV']
                                    s_data['pricing']['intrinsicMethod'] = lk.get('calcIVMethod','Live calculation')
                                    primary_iv = {'method': lk.get('calcIVMethod','Live IV'),
                                                  'value':  lk['calcIV'],
                                                  'desc':   lk.get('calcIVDesc','Calculated from live FMP data')}
                                    if not isinstance(s_data.get('ivBreakdown'), list):
                                        s_data['ivBreakdown'] = []
                                    if s_data['ivBreakdown']:
                                        s_data['ivBreakdown'][0] = primary_iv
                                    else:
                                        s_data['ivBreakdown'].insert(0, primary_iv)
                                    if parsed.get('comparisonTable'):
                                        for row in parsed['comparisonTable']:
                                            if row.get('ticker','').upper() == tk_key.upper():
                                                row['intrinsicValue'] = lk['calcIV']
                                elif lk.get('fmpDCF'):
                                    s_data['pricing']['intrinsicValue']  = lk['fmpDCF']
                                    s_data['pricing']['intrinsicMethod'] = 'FMP DCF Model (live)'
                                if "fundamentals" not in s_data or not s_data["fundamentals"]:
                                    s_data["fundamentals"] = {}
                                f = s_data["fundamentals"]
                                def _set(key, val):
                                    if val and val != "N/A":
                                        if key not in f: f[key] = {}
                                        f[key]["v"] = val
                                        f[key].setdefault("sig", "ok")
                                _set("revenue",      lk.get("revenue"))
                                _set("netMargin",    lk.get("netMargin"))
                                _set("grossMargin",  lk.get("grossMargin"))
                                _set("eps",          f"${lk['eps']}" if lk.get("eps") and lk["eps"] != "N/A" else None)
                                _set("forwardEPS",   f"${lk['fwdEPS']}" if lk.get("fwdEPS") and lk["fwdEPS"] != "N/A" else None)
                                _set("peRatio",      f"{lk['peRatio']}×" if lk.get("peRatio") and lk["peRatio"] != "N/A" else None)
                                _set("evEbitda",     f"{lk['evEbitda']}×" if lk.get("evEbitda") and lk["evEbitda"] != "N/A" else None)
                                _set("roe",          lk.get("roe"))
                                _set("debtToEquity", lk.get("debtEq"))
                        # comparisonTable
                        if parsed.get("comparisonTable"):
                            for row in parsed["comparisonTable"]:
                                if row.get("ticker","").upper() == tk_key.upper():
                                    if lk.get("currentPrice"):
                                        row["currentPrice"] = lk["currentPrice"]
                                    if lk.get("analystConsensus"):
                                        row["analystConsensus"] = lk["analystConsensus"]
                # Also override using raw fmp_raw_data as fallback
                elif st.session_state.get('fmp_raw_data') and parsed.get("stocks"):
                    for tk_key, raw_fmp in st.session_state['fmp_raw_data'].items():
                        q = (raw_fmp.get("quote") or [{}])
                        q = q[0] if isinstance(q, list) and q else q if isinstance(q, dict) else {}
                        live_price = q.get("price")
                        if live_price:
                            price_str = f"${live_price:,.2f}" if isinstance(live_price,(int,float)) else f"${live_price}"
                            for sk in list(parsed["stocks"].keys()):
                                if sk.upper() == tk_key.upper():
                                    parsed["stocks"][sk]["currentPrice"] = price_str
                            if parsed.get("comparisonTable"):
                                for row in parsed["comparisonTable"]:
                                    if row.get("ticker","").upper() == tk_key.upper():
                                        row["currentPrice"] = price_str

                # ── Fix duplicate top2 when only 1 stock entered ──
                if parsed.get("top2"):
                    seen = set()
                    deduped = []
                    for t in parsed["top2"]:
                        tk = t.get("ticker","")
                        if tk not in seen:
                            seen.add(tk)
                            deduped.append(t)
                    parsed["top2"] = deduped


                st.session_state['result'] = parsed
                st.session_state['raw_response'] = None
                # Determine data source using local variables (reliable)
                if finnhub_prices and fmp_contexts:
                    ds = "Finnhub + FMP + Claude"
                elif fmp_contexts:
                    ds = "FMP + Claude"
                else:
                    ds = "Claude only"
                st.session_state['data_source'] = ds
                st.session_state['fmp_tickers'] = list(fmp_contexts.keys())
                status.update(label="Analysis complete!", state="complete")
        except Exception as e:
            err = str(e)
            if 'credit' in err.lower() or 'billing' in err.lower():
                st.error('API credit limit reached. Please add credits at platform.anthropic.com → Billing.')
            elif '401' in err or 'api_key' in err.lower() or 'authentication' in err.lower():
                st.error('Invalid API key. Please check your ANTHROPIC_API_KEY in Streamlit secrets.')
            elif '529' in err or 'overloaded' in err.lower():
                st.error('Claude API is temporarily overloaded. Please wait a moment and try again.')
            else:
                st.error('Analysis failed. Please try again. If the problem persists, check your API keys in Streamlit secrets.')
        finally:
            st.session_state['running'] = False
            # Always overwrite data_source based on what was actually fetched
            if fmp_contexts or local_raw_data:
                if finnhub_prices:
                    st.session_state['data_source'] = "Finnhub + FMP + Claude"
                else:
                    st.session_state['data_source'] = "FMP + Claude"
                st.session_state['fmp_tickers'] = list(fmp_contexts.keys()) if fmp_contexts else list(local_raw_data.keys())
            elif not st.session_state.get('data_source'):
                st.session_state['data_source'] = "Claude only" 

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state['result']:
    data = st.session_state['result']
    top2 = data.get('top2', [])
    stocks = data.get('stocks', {})
    ctable = data.get('comparisonTable', [])

    # ── Data source badge ──
    data_source = st.session_state.get('data_source')
    fmp_tickers = st.session_state.get('fmp_tickers', [])
    if data_source:
        tickers_str = ', '.join(fmp_tickers) if fmp_tickers else 'N/A'
        if "FMP" in (data_source or "") or "Finnhub" in (data_source or ""):
            badge_bg    = "#061508"
            badge_border= "#16a34a55"
            badge_icon  = "📡"
            badge_color = "#4ade80"
            badge_label = data_source
            badge_desc  = f"Live market data ({tickers_str}) + AI reasoning by Claude"
        else:
            badge_bg    = "#0f1208"
            badge_border= "#ca8a0455"
            badge_icon  = "🧠"
            badge_color = "#fbbf24"
            badge_label = "Training Data"
            badge_desc  = "FMP not connected — add FMP_API_KEY to Streamlit secrets for live data."
            badge_border= "#ca8a0455"
            badge_icon  = "🧠"
            badge_color = "#fbbf24"
            badge_label = "Training Data"
            badge_desc  = "FMP not connected — analysis based on Claude training knowledge. Add FMP_API_KEY to Streamlit secrets for live data."
        st.markdown(f"""
        <div style="background:{badge_bg};border:1px solid {badge_border};padding:10px 14px;
                    margin-bottom:14px;display:flex;align-items:center;gap:12px">
          <div style="font-size:20px">{badge_icon}</div>
          <div>
            <div style="font-family:Syne,sans-serif;font-size:11px;font-weight:700;
                        letter-spacing:2px;text-transform:uppercase;color:{badge_color}">
              Data Source: {badge_label}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px">{badge_desc}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Deduplicate stocks — keep all that Claude returned, just normalise keys
    # Do NOT filter against valid_tickers because Claude resolves names to symbols
    # e.g. user typed "Apple" but Claude returns key "AAPL" — both are valid
    clean_stocks = {}
    for k, v in stocks.items():
        tk = k.upper().upper().strip()
        if tk and tk not in clean_stocks:
            clean_stocks[tk] = {**v, 'ticker': tk}
    stocks = clean_stocks
    # Also add any top2 tickers that somehow didn't make it into stocks{}
    for t2 in top2:
        tk2 = (t2.get('ticker') or '').upper().upper().strip()
        if tk2 and tk2 not in stocks:
            stocks[tk2] = {
                'ticker': tk2, 'companyName': t2.get('companyName',''),
                'verdictStock': 'NEUTRAL', 'verdictStockReason': 'See top picks above.',
                'verdictPortfolio': 'NEUTRAL', 'verdictPortfolioReason': '',
                'summary': t2.get('buyReason',''), 'sentimentScore': None,
                'pricing': {}, 'ivBreakdown': [], 'topAnalysts': [],
                'fundamentals': None, 'sections': {}, 'sectorAnalysis': {}, 'riskAnalysis': {}
            }

    # Sort: top2 first, then by score
    def sort_key(s):
        tk = s.get('ticker','')
        ri = next((i for i,t in enumerate(top2) if t.get('ticker')==tk), 99)
        row = next((r for r in ctable if r.get('ticker')==tk), {})
        score = float(re.sub(r'[^0-9.]','', str(row.get('overallScore','0') or '0')) or 0)
        return (ri, -score)
    sorted_stocks = sorted(stocks.values(), key=sort_key)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Top 2 picks — filter out N/A placeholders and limit to real stocks ──
    real_top2 = [t for t in top2 if t.get('ticker','').upper() not in ('N/A','','NONE')
                 and t.get('companyName','').lower() not in ('n/a','only one stock analyzed','')]
    # Also deduplicate by ticker
    seen_t2 = set()
    deduped_top2 = []
    for t in real_top2:
        tk = t.get('ticker','')
        if tk not in seen_t2:
            seen_t2.add(tk)
            deduped_top2.append(t)
    # Don't show more picks than stocks analyzed
    deduped_top2 = deduped_top2[:min(len(sorted_stocks), 2)]

    st.markdown("## ★ TOP PICKS TO BUY")
    if not deduped_top2:
        st.markdown('<div style="color:#94a3b8;font-size:12px;padding:10px 0">No top picks generated.</div>', unsafe_allow_html=True)
    t2cols = st.columns(max(len(deduped_top2), 1))
    for i, t in enumerate(deduped_top2):
        with t2cols[i]:
            cls = 'card-gold' if i == 0 else 'card-gray'
            lbl = '#1 Best Pick' if i == 0 else '#2 Runner-Up'
            score_color = '#f59e0b' if i == 0 else '#9ca3af'
            # Get pricing data for this top2 ticker
            t2_stock = stocks.get(t.get('ticker',''), {})
            t2_pp = t2_stock.get('pricing', {})
            t2_iv  = t2_pp.get('intrinsicValue','')
            t2_con = t2_pp.get('analystConsensus','')
            t2_ent = t2_pp.get('entryPrice','')
            badge_bg  = '#f59e0b' if i==0 else '#4b5563'
            badge_clr = '#000'    if i==0 else '#fff'
            entry_note = esc(t.get('entryNote',''))
            buy_reason = esc(t.get('buyReason',''))
            t2_cur = esc(t2_stock.get('currentPrice',''))
            price_pills = ''
            if t2_cur:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #ffffff0a"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Current Price</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#f0f6ff">{t2_cur}</span></div>'
            if t2_iv:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #ffffff0a"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Intrinsic Value</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#a78bfa">{t2_iv}</span></div>'
            if t2_con:
                price_pills += f'<div style="display:flex;flex-direction:column;padding:6px 0;border-bottom:1px solid #ffffff0a"><div style="display:flex;justify-content:space-between;align-items:center"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Consensus Target</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#93c5fd">{t2_con}</span></div><div style=\"font-size:9px;color:#f59e0b;margin-top:2px\">⚠ May be delayed or incorrect</div></div>'
            if t2_ent:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Suggested Entry</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#4ade80">{t2_ent}</span></div>'

            st.markdown(
                f'<div class="card {cls}" style="position:relative">'
                f'<div style="position:absolute;top:0;right:0;font-family:Syne,sans-serif;font-size:8px;font-weight:700;letter-spacing:2px;padding:3px 9px;background:{badge_bg};color:{badge_clr}">{lbl}</div>'
                f'<div style="font-family:Syne,sans-serif;font-size:22px;font-weight:800;color:#f0f6ff;margin-top:2px">{t.get("ticker","—")}</div>'
                f'<div style="font-size:12px;color:#94a3b8;margin:2px 0 6px">{t.get("companyName","")}</div>'
                f'<div style="display:flex;align-items:baseline;gap:4px;margin-bottom:10px">'
                f'<span style="font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:{score_color}">{t.get("score","—")}</span>'
                f'<span style="font-size:11px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase"> / 10</span>'
                f'</div>'
                f'{("<div style=\"background:#090f1a;border:1px solid #111c2a;padding:6px 10px;margin-bottom:10px\">" + price_pills + "</div>") if price_pills else ""}'
                f'<div style="font-size:13px;color:#e2e8f0;line-height:1.8;border-top:1px solid #ffffff11;padding-top:8px">{buy_reason}</div>'
                f'{("<div style=\"font-size:11px;color:#4ade80;margin-top:6px\">▸ " + entry_note + "</div>") if entry_note else ""}'
                f'</div>',
                unsafe_allow_html=True
            )

    top2 = deduped_top2  # use cleaned list for rest of page
    if data.get('rankingSummary'):
        st.markdown(f"""
        <div style="padding:10px 12px;background:#090f1a;border:1px solid #111c2a;font-size:11px;color:#e2e8f0;line-height:1.8;margin-top:4px">
          <div style="color:#3b82f6;font-family:'Syne',sans-serif;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px">Why These</div>
          {data.get('rankingSummary','')}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Per-stock cards ──
    st.markdown(f'### ALL {len(sorted_stocks)} STOCKS — HIGHEST TO LOWEST RANK')

    for s in sorted_stocks:
        tk = s.get('ticker','')
        is_win = any(t.get('ticker')==tk for t in top2)
        ri = next((i for i,t in enumerate(top2) if t.get('ticker')==tk), -1)
        rank_badge = ''
        if ri == 0: rank_badge = '<span class="rank-gold">#1</span>'
        elif ri == 1: rank_badge = '<span class="rank-silver">#2</span>'

        pp = s.get('pricing', {})
        row = next((r for r in ctable if r and r.get('ticker')==tk), {})
        # Match cand_idx: try exact ticker match first, then check if any input
        # resolves to this ticker (for company name inputs)
        cand_idx = -1
        if tk in valid_tickers:
            cand_idx = valid_tickers.index(tk)
        else:
            # Try matching by inputAs field or by position in top2
            input_as_field = s.get('inputAs','').upper().upper().strip()
            for idx2, vt in enumerate(valid_tickers):
                if vt.upper() == tk or vt.upper() == input_as_field:
                    cand_idx = idx2
                    break
            # Last resort: use top2 rank to guess position
            if cand_idx < 0:
                ri2 = next((i for i,t in enumerate(top2) if t.get('ticker')==tk), -1)
                if ri2 >= 0 and ri2 < len(valid_tickers):
                    cand_idx = ri2
        cur_raw_full = st.session_state['prices'][cand_idx] if cand_idx >= 0 and st.session_state['prices'][cand_idx] else s.get('currentPrice','')
        cur_raw = cur_raw_full.lstrip('$') if cur_raw_full else ''  # strip $ for delta_badge math
        cur_shares = st.session_state['shares'][cand_idx] if cand_idx >= 0 else ''
        vs = s.get('verdictStock','NEUTRAL')
        vp = s.get('verdictPortfolio','NEUTRAL')
        sent_num = None
        try: sent_num = int(re.sub(r'\D','', str(s.get('sentimentScore',''))))
        except: pass

        card_border = 'card-win' if is_win else ''
        win_star = ' ★' if is_win else ''

        # Pre-build all variables — keep f-string clean
        company_name   = esc(s.get('companyName',''))
        overall_score  = row.get('overallScore','—')
        input_as       = esc(s.get('inputAs',''))
        v_stock_reason = esc(s.get('verdictStockReason',''))
        v_port_reason  = esc(s.get('verdictPortfolioReason',''))
        port_label     = "Portfolio Synergy" if port_holds else "Portfolio Context"
        vc             = verdict_cls(vs)
        vcp            = verdict_cls(vp)
        v_icon_s       = verdict_icon(vs)
        v_icon_p       = verdict_icon(vp)
        iv_val         = pp.get('intrinsicValue','')
        cons_val       = pp.get('analystConsensus','')
        entry_val      = pp.get('entryPrice','')

        # Build conditional snippets
        price_part   = ("$" + esc(cur_raw)) if cur_raw else ""
        shares_part  = esc(cur_shares) if cur_shares else ""
        inputas_part = ("entered as: " + input_as) if (input_as and input_as.upper() != tk) else ""

        # Sentiment for verdict card
        fh_sent_card = st.session_state.get('finnhub_sentiment_data',{}).get(tk,{})
        sent_data_card = fh_sent_card.get('sentiment',{})
        bull_card = sent_data_card.get('bullishPercent')
        if bull_card is not None:
            bull_f_card = float(bull_card)
            bull_pct_card = f'{bull_f_card*100:.0f}%' if bull_f_card<=1 else f'{bull_f_card:.0f}%'
            sent_label_card = 'Bullish' if bull_f_card>0.55 else ('Bearish' if bull_f_card<0.45 else 'Neutral')
            sent_color_card = '#4ade80' if bull_f_card>0.55 else ('#f87171' if bull_f_card<0.45 else '#fbbf24')
            sent_display = f'<span style="color:{sent_color_card};font-weight:700">{sent_label_card} ({bull_pct_card} bullish)</span>'
        elif sent_num is not None:
            s_col = '#4ade80' if sent_num>=60 else ('#f87171' if sent_num<=35 else '#fbbf24')
            sent_display = f'<span style="color:{s_col};font-weight:700">{sent_num}/100</span>'
        else:
            sent_display = '<span style="color:#94a3b8">N/A</span>'

        # Next earnings date
        lk_card = st.session_state.get('fmp_locked',{}).get(tk,{})
        next_earn = lk_card.get('nextEarningsDate','')
        earn_timing = lk_card.get('nextEarningsTiming','')
        earn_eps = lk_card.get('nextEarningsEPS','')
        timing_map = {'amc':'After Close','bmo':'Before Open','dmh':'During Hours'}
        earn_timing_disp = timing_map.get(str(earn_timing).lower(),'') if earn_timing and str(earn_timing)!='N/A' else ''
        if next_earn and next_earn != 'N/A':
            earn_disp = f'<span style="color:#fbbf24;font-weight:700">{next_earn}</span>'
            if earn_timing_disp: earn_disp += f' <span style="color:#94a3b8;font-size:9px">({earn_timing_disp})</span>'
            if earn_eps and str(earn_eps)!='N/A': earn_disp += f' <span style="color:#94a3b8;font-size:9px">Est EPS: ${earn_eps}</span>'
        else:
            earn_disp = '<span style="color:#94a3b8">Not available</span>'


        # Price strip — intrinsic value, consensus, entry
        # Current price — from FMP quote or Claude response
        cur_price_display = s.get('currentPrice','')
        if not cur_price_display and cur_raw:
            cur_price_display = f'${cur_raw}'
        # Strip leading $ if already present to avoid $$
        if cur_price_display and cur_price_display.startswith('$'):
            cur_price_display = cur_price_display  # already has $, keep as-is
        elif cur_price_display:
            cur_price_display = f'${cur_price_display}'

        price_strip = ''
        if cur_price_display or iv_val or cons_val or entry_val:
            price_strip = '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-bottom:10px">'
            # Row 1: Intrinsic Value | Consensus Target
            _iv_lbl = 'FMP DCF' if 'FMP' in pp.get('intrinsicMethod','') else 'Intrinsic Value'
            price_strip += ('<div style="background:#0c0818;border:1px solid #7c3aed44;padding:8px 10px;">'
                '<div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">' + _iv_lbl + '</div>'
                '<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#a78bfa">' + (iv_val or '—') + '</div></div>')
            price_strip += ('<div style="background:#080f1f;border:1px solid #3b82f644;padding:8px 10px;">'
                '<div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Consensus Target</div>'
                '<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#93c5fd">' + (cons_val or '—') + '</div>'
                '<div style="font-size:9px;color:#f59e0b;margin-top:3px">⚠ May be delayed</div></div>')
            # Row 2: Suggested Entry | Current Price
            price_strip += ('<div style="background:#060f09;border:1px solid #16a34a44;padding:8px 10px;">'
                '<div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Suggested Entry</div>'
                '<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#4ade80">' + (entry_val or '—') + '</div></div>')
            price_strip += ('<div style="background:#0d1825;border:1px solid #3b82f644;padding:8px 10px;">'
                '<div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Current Price</div>'
                '<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#f0f6ff">' + esc(cur_price_display or '—') + '</div></div>')
            price_strip += '</div>'

        # One self-contained HTML block — no split across st.columns
        html = (
            f'<div style="background:#0a1420;border:1px solid {"#f59e0b" if is_win else "#1a2e48"};'
            f'margin-bottom:14px;overflow:hidden">'

            # ── Header row ──
            f'<div style="padding:13px 14px 12px;background:#0d1825">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px">'
            f'<div>'
            f'<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;'
            f'color:#f0f6ff;letter-spacing:2px">{rank_badge}{tk}{win_star}</div>'
            f'<div style="font-size:14px;color:#e2e8f0;margin-top:3px">{company_name}</div>'
        )
        if inputas_part:
            html += f'<div style="font-size:11px;color:#3b82f6;margin-top:2px">{inputas_part}</div>'
        if price_part or shares_part:
            html += '<div style="margin-top:5px">'
            if price_part:
                html += f'<span style="font-size:13px;color:#93c5fd;font-weight:700">{price_part}</span>'
            if shares_part:
                html += f'<span style="font-size:13px;color:#cbd5e1"> &nbsp;&#183;&nbsp; {shares_part} shares</span>'
            html += '</div>'
        # Sentiment row
        html += (
            f'<div style="display:flex;gap:16px;margin-top:6px;padding-top:6px;border-top:1px solid #1a2e48">'
            f'<div><span style="font-size:9px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Sentiment </span>{sent_display}</div>'
            f'<div><span style="font-size:9px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Next Earnings </span>{earn_disp}</div>'
            f'</div>'
        )
        html += (
            f'</div>'  # left side
            f'<div style="text-align:right">'
            f'<div style="font-family:Syne,sans-serif;font-size:17px;font-weight:800;color:#e2e8f0">{overall_score}</div>'
            f'<div style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Score</div>'
            f'</div>'
            f'</div>'  # flex row

            # ── Price strip ──
            + price_strip +

            # ── Verdict pills ──
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">'

            # Standalone verdict
            f'<div class="verdict-{vc}">'
            f'<div class="verdict-tag verdict-tag-{vc}">Standalone Verdict</div>'
            f'<div class="verdict-label-{vc}">{v_icon_s} {vs}</div>'
            f'<div class="verdict-reason">{v_stock_reason}</div>'
            f'</div>'

            # Portfolio verdict
            f'<div class="verdict-{vcp}">'
            f'<div class="verdict-tag verdict-tag-{vcp}">{port_label}</div>'
            f'<div class="verdict-label-{vcp}">{v_icon_p} {vp}</div>'
            f'<div class="verdict-reason">{v_port_reason}</div>'
            f'</div>'

            f'</div>'  # verdict grid
            f'</div>'  # header padding div
            f'</div>'  # outer card
        )
        st.markdown(html, unsafe_allow_html=True)

        # ── Expandable detail ──
        with st.expander(f"▸ View Detailed Performance Diagnostics — {tk}"):

            # Summary
            if s.get('summary'):
                st.markdown(f'<div class="sec-hdr">◈ Asset Analysis Ledger</div><div class="sec-body">{s["summary"]}</div>', unsafe_allow_html=True)

            # Key numbers
            kc0, kc1, kc2, kc3 = st.columns(4)
            with kc0:
                cp_disp = esc(s.get('currentPrice','')) or (f'${cur_raw}' if cur_raw else '—')
                st.markdown(f"""
                <div class="card" style="border-color:#3b82f644">
                  <div class="label">Current Price</div>
                  <div class="big-val" style="color:#f0f6ff">{cp_disp}</div>
                  <div class="sub-text">Live from FMP</div>
                </div>""", unsafe_allow_html=True)
            with kc1:
                iv = pp.get('intrinsicValue','—')
                st.markdown(f"""
                <div class="card card-purple">
                  <div class="label">{'FMP DCF — Live' if 'FMP' in pp.get('intrinsicMethod','') else 'Blended Intrinsic Value'}</div>
                  <div class="big-val big-val-purple">{iv}</div>
                  <div class="sub-text">{pp.get('intrinsicMethod','DCF + EV/EBITDA + P/E')}</div>
                  {delta_badge(iv, cur_raw)}
                </div>""", unsafe_allow_html=True)
            with kc2:
                ac = pp.get('analystConsensus','—')
                st.markdown(f"""
                <div class="card card-blue">
                  <div class="label">Consensus Target</div>
                  <div class="big-val big-val-blue">{ac}</div>
                  <div class="sub-text">Range: {pp.get('targetRange','—')}</div>
                  {delta_badge(ac, cur_raw)}
                  <div style="font-size:9px;color:#f59e0b;margin-top:4px">⚠ May be delayed or incorrect</div>
                </div>""", unsafe_allow_html=True)
            with kc3:

                ep = pp.get('entryPrice','—')
                st.markdown(f"""
                <div class="card card-green">
                  <div class="label">Suggested Entry Price</div>
                  <div class="big-val big-val-green">{ep}</div>
                  <div class="sub-text">{pp.get('entryRationale','15% margin of safety')}</div>
                  {delta_badge(ep, cur_raw)}
                </div>""", unsafe_allow_html=True)

            # IV breakdown
            iv_bd = s.get('ivBreakdown', [])
            if iv_bd:
                st.markdown('<div style="font-size:8px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin:12px 0 7px">Quad Intrinsic Valuation Models Applied</div>', unsafe_allow_html=True)
                ivcols = st.columns(len(iv_bd))
                for j, iv in enumerate(iv_bd):
                    with ivcols[j]:
                        st.markdown(f"""
                        <div class="card" style="padding:9px 10px">
                          <div style="font-size:10px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">{iv.get('method','')}</div>
                          <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#a78bfa">{iv.get('value','—')}</div>
                          <div style="font-size:11px;color:#cbd5e1;margin-top:2px;line-height:1.4">{iv.get('desc','')}</div>
                        </div>""", unsafe_allow_html=True)

            # Analysts
            analysts = s.get('topAnalysts', [])
            if analysts:
                st.markdown('<div style="font-size:8px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin:12px 0 7px">Top Analyst Targets</div>', unsafe_allow_html=True)
                rows = []
                for j, a in enumerate(analysts[:5]):
                    acc = a.get('accuracyPct','—')
                    try: acc_num = float(re.sub(r'[^0-9.]','',str(acc)))
                    except: acc_num = 0
                    acc_cls = 'sig-good' if acc_num >= 70 else 'sig-ok'
                    rat_cls = rating_cls(a.get('rating',''))
                    tgt = a.get('target','—')
                    rows.append(f"""
                    <tr>
                      <td style="color:#94a3b8">#{j+1}</td>
                      <td><div style="color:#e2e8f0;font-weight:700">{a.get('name','')}</div>
                          <div style="color:#94a3b8;font-size:9px">{a.get('firm','')}</div>
                          <div style="color:#cbd5e1;font-size:9px">{a.get('thesis','')}</div></td>
                      <td><span class="{acc_cls}">{acc}</span></td>
                      <td><span class="{rat_cls}">{a.get('rating','—')}</span></td>
                      <td><div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:800;color:#f0f6ff">{tgt}</div>
                          {delta_badge(tgt, cur_raw)}</td>
                    </tr>""")
                st.markdown(f'<table class="data-table"><thead><tr><th>#</th><th>Analyst / Firm</th><th>Accuracy</th><th>Rating</th><th>Target</th></tr></thead><tbody>{"".join(rows)}</tbody></table>', unsafe_allow_html=True)

            # Sentiment + Risk
            sent_label = "Bearish" if sent_num and sent_num <= 35 else ("Neutral" if sent_num and sent_num <= 50 else ("Slightly Bullish" if sent_num and sent_num <= 70 else "Bullish"))
            sent_color = "#f87171" if sent_num and sent_num <= 35 else ("#fbbf24" if sent_num and sent_num <= 50 else "#4ade80")
            # Finnhub news sentiment for this ticker
            fh_sent_tk  = st.session_state.get('finnhub_sentiment_data',{}).get(tk,{})
            buzz_data   = fh_sent_tk.get('buzz',{})
            sent_data_f = fh_sent_tk.get('sentiment',{})
            bull_pct    = sent_data_f.get('bullishPercent')
            bear_pct    = sent_data_f.get('bearishPercent')
            buzz_score  = buzz_data.get('buzz')
            news_score  = fh_sent_tk.get('companyNewsScore')
            sec_avg     = fh_sent_tk.get('sectorAverageBullishPercent')
            has_fh_sent = bull_pct is not None

            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"""
                <div class="card" style="padding:11px">
                  <div class="label">Sentiment Score</div>
                  {'<div style="font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:'+sent_color+'">'+str(sent_num)+'<span style="font-size:13px;color:#5a7a99">/100</span></div><div style="font-size:12px;color:#cbd5e1;margin-top:2px">'+sent_label+'</div>' if sent_num is not None else '<div style="font-size:13px;color:#e2e8f0;line-height:1.8">'+(s.get('sections',{}).get('sentiment','—'))+'</div>'}
                </div>""", unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div class="card" style="padding:11px">
                  <div class="label">Risk Profile</div>
                  <div style="font-size:13px;color:#e2e8f0;line-height:1.8">{s.get('sections',{}).get('risk','—')}</div>
                </div>""", unsafe_allow_html=True)


            # ── Finnhub News Sentiment Card ──
            if has_fh_sent:
                try:
                    bull_f = float(bull_pct) if bull_pct is not None else 0
                    bear_f = float(bear_pct) if bear_pct is not None else 0
                    bull_disp = f'{bull_f*100:.0f}%' if bull_f<=1 else f'{bull_f:.0f}%'
                    bear_disp = f'{bear_f*100:.0f}%' if bear_f<=1 else f'{bear_f:.0f}%'
                    buzz_f = float(buzz_score) if buzz_score else None
                    news_f = float(news_score) if news_score else None
                    sec_f  = float(sec_avg) if sec_avg else None
                    sec_disp = f'{sec_f*100:.0f}%' if sec_f and sec_f<=1 else (f'{sec_f:.0f}%' if sec_f else 'N/A')
                    bull_clr  = '#4ade80' if bull_f > bear_f else '#f87171'
                    buzz_clr  = '#4ade80' if buzz_f and buzz_f>1.0 else ('#f87171' if buzz_f and buzz_f<0.5 else '#fbbf24')
                    buzz_lbl  = 'Above avg' if buzz_f and buzz_f>1.0 else ('Below avg' if buzz_f and buzz_f<0.5 else 'Avg')
                    news_clr  = '#4ade80' if news_f and news_f>0.6 else ('#f87171' if news_f and news_f<0.4 else '#fbbf24')
                    st.markdown(f'''
                    <div class="card" style="padding:12px;margin-bottom:10px;border-color:#3b82f644">
                      <div class="label" style="margin-bottom:8px">📡 FINNHUB NEWS SENTIMENT (LIVE)</div>
                      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
                        <div><div style="font-size:9px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Bullish News</div>
                          <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{bull_clr}">{bull_disp}</div></div>
                        <div><div style="font-size:9px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Bearish News</div>
                          <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:#f87171">{bear_disp}</div></div>
                        <div><div style="font-size:9px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Buzz Score</div>
                          <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{buzz_clr}">{f'{buzz_f:.2f}' if buzz_f else 'N/A'}</div>
                          <div style="font-size:9px;color:#94a3b8">{buzz_lbl} vs hist</div></div>
                        <div><div style="font-size:9px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">News Score</div>
                          <div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{news_clr}">{f'{news_f:.2f}' if news_f else 'N/A'}</div>
                          <div style="font-size:9px;color:#94a3b8">Sector: {sec_disp} bull</div></div>
                      </div>
                    </div>''', unsafe_allow_html=True)
                except Exception:
                    pass

            # Portfolio insights
            pi = s.get('portfolioInsights', {})
            if pi and port_holds:
                st.markdown('<div class="sec-hdr">◎ Portfolio Synergy Analysis</div>', unsafe_allow_html=True)
                rows_pi = ""
                for label, key in [("Concentration Risk","concentrationRisk"),("Sector Overlap","sectorOverlap"),("Correlation","correlationNote"),("Diversification","diversificationImpact"),("Sizing","recommendation")]:
                    if pi.get(key):
                        rows_pi += f'<p><span style="color:#3b82f6;font-family:Syne,sans-serif;font-size:9px;letter-spacing:1px">{label}: </span>{pi[key]}</p>'
                st.markdown(f'<div class="sec-body">{rows_pi}</div>', unsafe_allow_html=True)

            # Fundamentals
            fund = s.get('fundamentals', {})
            if fund:
                st.markdown('<div class="sec-hdr">▣ Fundamental Analysis</div>', unsafe_allow_html=True)
                frows = ""
                for key, lbl in FUND_LABELS:
                    r = fund.get(key, {})
                    if r and r.get('v'):
                        sig = r.get('sig','ok')
                        sig_html = f'<span class="sig-good">● Strong</span>' if sig=='good' else (f'<span class="sig-bad">● Weak</span>' if sig=='bad' else f'<span class="sig-ok">● Fair</span>')
                        note = r.get("note","") or r.get("chg","") or ""
                        frows += f'<tr><td class="mn">{lbl}</td><td style="color:#fff;font-weight:700">{r["v"]}</td><td>{sig_html}</td><td style="font-size:11px;color:#94a3b8">{note}</td></tr>'
                st.markdown(f'<table class="data-table"><thead><tr><th>Metric</th><th>Value</th><th>Signal</th><th>Note</th></tr></thead><tbody>{frows}</tbody></table>', unsafe_allow_html=True)

            # Valuation + Momentum sections
            secs = s.get('sections', {})
            for key, icon, lbl in [("valuation","◎","Valuation Analysis"),("momentum","△","Price Momentum")]:
                if secs.get(key):
                    st.markdown(f'<div class="sec-hdr">{icon} {lbl}</div><div class="sec-body">{secs[key]}</div>', unsafe_allow_html=True)

            # ── SECTOR ANALYSIS ──
            sa = s.get('sectorAnalysis', {})
            if sa:
                st.markdown('<div class="sec-hdr">◈ Sector Analysis & Peer Comparison</div>', unsafe_allow_html=True)
                # Sector header info
                sector_sector  = esc(sa.get('sector','—'))
                sector_rank    = esc(sa.get('sectorRank','—'))
                sector_outlook = esc(sa.get('sectorOutlook',''))
                sector_html  = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px">'
                sector_html += '<div class="card" style="padding:10px 14px;flex:1;min-width:140px">'
                sector_html += '<div class="label">Sector</div>'
                sector_html += f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:#93c5fd">{sector_sector}</div>'
                sector_html += '</div>'
                sector_html += '<div class="card" style="padding:10px 14px;flex:1;min-width:140px">'
                sector_html += '<div class="label">Sector Rank</div>'
                sector_html += f'<div style="font-family:Syne,sans-serif;font-size:14px;font-weight:700;color:#f0f6ff">{sector_rank}</div>'
                sector_html += '</div></div>'
                sector_html += f'<div class="sec-body" style="margin-bottom:10px">{sector_outlook}</div>'
                st.markdown(sector_html, unsafe_allow_html=True)

                # Peer comparison table
                peers = sa.get('peerComparison', [])
                if peers:
                    st.markdown('<div style="font-size:8px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin-bottom:7px">Peer Comparison</div>', unsafe_allow_html=True)
                    peer_rows = ""
                    for p in peers:
                        v = p.get("verdict","")
                        v_color = "#4ade80" if v in ("Above","Premium","Inline") else "#f87171" if v in ("Below","Discount") else "#fbbf24"
                        peer_rows += f"""<tr>
                          <td style="color:#e2e8f0;font-weight:700">{p.get("peer","")}</td>
                          <td style="color:#94a3b8">{p.get("metric","")}</td>
                          <td style="color:#cbd5e1">{p.get("peerVal","—")}</td>
                          <td style="color:#f0f6ff;font-weight:700">{p.get("stockVal","—")}</td>
                          <td><span style="color:{v_color};font-size:10px">{v}</span></td>
                        </tr>"""
                    thead = '<table class="data-table"><thead><tr><th>Peer</th><th>Metric</th><th>Peer</th><th>This Stock</th><th>vs Peer</th></tr></thead><tbody>'
                    st.markdown(thead + peer_rows + '</tbody></table>', unsafe_allow_html=True)

                # Sector catalysts + risks
                cat_catalysts = esc(sa.get('sectorCatalysts','—'))
                cat_risks     = esc(sa.get('sectorRisks','—'))
                cat_risk_html  = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px">'
                cat_risk_html += '<div class="card card-green" style="padding:11px">'
                cat_risk_html += '<div class="label">Sector Catalysts</div>'
                cat_risk_html += f'<div style="font-size:13px;color:#e2e8f0;line-height:1.8;margin-top:4px">{cat_catalysts}</div>'
                cat_risk_html += '</div>'
                cat_risk_html += '<div class="card" style="padding:11px;border-color:#dc262644;background:#150505">'
                cat_risk_html += '<div class="label">Sector Risks</div>'
                cat_risk_html += f'<div style="font-size:13px;color:#e2e8f0;line-height:1.8;margin-top:4px">{cat_risks}</div>'
                cat_risk_html += '</div></div>'
                st.markdown(cat_risk_html, unsafe_allow_html=True)

            # ── DETAILED RISK ANALYSIS ──
            ra = s.get('riskAnalysis', {})
            if ra:
                # Risk rating header
                rating = ra.get("overallRiskRating","Medium")
                risk_score = ra.get("riskScore", 50)
                try: risk_score = int(risk_score)
                except: risk_score = 50
                r_color = "#4ade80" if rating=="Low" else "#fbbf24" if rating=="Medium" else "#f87171" if rating=="High" else "#dc2626"

                st.markdown(f'<div class="sec-hdr">⚠ Detailed Risk Analysis</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:16px;padding:12px;background:#090f1a;border:1px solid #111c2a;margin-bottom:10px">
                  <div>
                    <div class="label">Overall Risk Rating</div>
                    <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:{r_color}">{rating}</div>
                  </div>
                  <div>
                    <div class="label">Risk Score</div>
                    <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:{r_color}">{risk_score}<span style="font-size:12px;color:#5a7a99">/100</span></div>
                  </div>
                  <div style="flex:1">
                    <div class="label" style="margin-bottom:5px">Risk Meter</div>
                    <div style="height:6px;background:#1a2e48;border-radius:3px">
                      <div style="height:6px;width:{risk_score}%;background:{r_color};border-radius:3px;transition:width 0.5s"></div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # Risk categories
                risk_cats = [
                    ("Business Risk", "businessRisk", "🏢"),
                    ("Financial Risk", "financialRisk", "💰"),
                    ("Macro Risk", "macroRisk", "🌐"),
                    ("Regulatory Risk", "regulatoryRisk", "⚖️"),
                    ("Valuation Risk", "valuationRisk", "📊"),
                ]
                for lbl, key, icon in risk_cats:
                    if ra.get(key):
                        st.markdown(f'<div class="sec-body" style="margin-bottom:6px"><span style="color:#3b82f6;font-family:Syne,sans-serif;font-size:9px;letter-spacing:1px">{icon} {lbl}: </span>{ra[key]}</div>', unsafe_allow_html=True)

                # Key risks table
                key_risks = ra.get("keyRisks", [])
                if key_risks:
                    st.markdown('<div style="font-size:8px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin:10px 0 7px">Key Risk Factors</div>', unsafe_allow_html=True)
                    risk_rows = ""
                    for kr in key_risks:
                        sev = kr.get("severity","Medium")
                        lik = kr.get("likelihood","Medium")
                        sev_color = "#f87171" if sev=="High" else "#fbbf24" if sev=="Medium" else "#4ade80"
                        lik_color = "#f87171" if lik=="High" else "#fbbf24" if lik=="Medium" else "#4ade80"
                        risk_rows += f"""<tr>
                          <td style="color:#e2e8f0">{kr.get("risk","")}</td>
                          <td><span style="color:{sev_color};font-size:10px">● {sev}</span></td>
                          <td><span style="color:{lik_color};font-size:10px">● {lik}</span></td>
                          <td style="font-size:12px;color:#cbd5e1">{kr.get("mitigation","")}</td>
                        </tr>"""
                    st.markdown(f'<table class="data-table"><thead><tr><th>Risk</th><th>Severity</th><th>Likelihood</th><th>Mitigation</th></tr></thead><tbody>{risk_rows}</tbody></table>', unsafe_allow_html=True)

                # Bull/Bear case prices
                if ra.get("bearCasePrice") or ra.get("bullCasePrice"):
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        st.markdown(f"""
                        <div class="card" style="padding:11px;border-color:#dc262644;background:#150505">
                          <div class="label">Bear Case Price</div>
                          <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#f87171">{ra.get("bearCasePrice","—")}</div>
                          <div style="font-size:11px;color:#cbd5e1;margin-top:3px">Worst-case scenario</div>
                        </div>""", unsafe_allow_html=True)
                    with bc2:
                        st.markdown(f"""
                        <div class="card card-green" style="padding:11px">
                          <div class="label">Bull Case Price</div>
                          <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#4ade80">{ra.get("bullCasePrice","—")}</div>
                          <div style="font-size:11px;color:#cbd5e1;margin-top:3px">Best-case scenario</div>
                        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="disc">FOR INFORMATIONAL PURPOSES ONLY — NOT FINANCIAL ADVICE</div>', unsafe_allow_html=True)