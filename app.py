import streamlit as st
import anthropic
import json
import re

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

# ── Session state ─────────────────────────────────────────────────────────────
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
ss('tickers', ['','','','',''])
ss('shares', ['','','','',''])
ss('prices', ['','','','',''])
ss('holdings', [{'ticker':'','shares':'','cost':''} for _ in range(10)])

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
with st.expander("▸ STOCKS TO ANALYZE (up to 5)", expanded=True):
    for i in range(5):
        c1, c2, c3 = st.columns([0.5, 2, 2])
        with c1:
            st.markdown(f'<div style="font-size:9px;color:#93c5fd;font-family:Syne,sans-serif;font-weight:700;padding-top:8px">#{i+1}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="label">Ticker or Company Name</div>', unsafe_allow_html=True)
            st.session_state['tickers'][i] = st.text_input(
                "Ticker or Company Name", value=st.session_state['tickers'][i],
                placeholder="AAPL or Apple", key=f"tk{i}",
                label_visibility="collapsed"
            ).strip()
        with c3:
            st.markdown('<div class="label">Shares to Buy</div>', unsafe_allow_html=True)
            st.session_state['shares'][i] = st.text_input(
                "Shares", value=st.session_state['shares'][i],
                placeholder="0", key=f"sh{i}", label_visibility="collapsed"
            )
        # Price to Buy field removed — entry price is AI-suggested in output
        st.session_state['prices'][i] = ''

# ── Portfolio ─────────────────────────────────────────────────────────────────
with st.expander("▸ MY PORTFOLIO — TOP 10 HOLDINGS (optional)"):
    st.markdown('<div class="label">Ticker · Shares · Avg Cost per share</div>', unsafe_allow_html=True)
    for i in range(10):
        c1, c2, c3, c4 = st.columns([0.5, 2, 2, 2])
        with c1:
            st.markdown(f'<div style="font-size:9px;color:#fff;padding-top:8px">#{i+1}</div>', unsafe_allow_html=True)
        with c2:
            st.session_state['holdings'][i]['ticker'] = st.text_input(
                f"HTk{i}", value=st.session_state['holdings'][i]['ticker'],
                placeholder="MSFT", max_chars=6, key=f"htk{i}", label_visibility="collapsed"
            ).upper().strip()
        with c3:
            st.session_state['holdings'][i]['shares'] = st.text_input(
                f"HSh{i}", value=st.session_state['holdings'][i]['shares'],
                placeholder="Shares", key=f"hsh{i}", label_visibility="collapsed"
            )
        with c4:
            st.session_state['holdings'][i]['cost'] = st.text_input(
                f"HCo{i}", value=st.session_state['holdings'][i]['cost'],
                placeholder="Avg $", key=f"hco{i}", label_visibility="collapsed"
            )

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

# Save current inputs to URL so they survive refresh
save_to_url()

# ── Top-level derived variables (available throughout the page) ──
port_holds = [h for h in st.session_state['holdings'] if h['ticker'] and h['shares'] and h['cost']]
port_val   = sum(float(h['shares']) * float(h['cost']) for h in port_holds)
valid_tickers = [t for t in st.session_state['tickers'] if t]

# ── Analyze button ────────────────────────────────────────────────────────────
valid_tickers = [t for t in st.session_state['tickers'] if t]
btn_label = f"ANALYZE {len(valid_tickers)} STOCK{'S' if len(valid_tickers)!=1 else ''}" if valid_tickers else "ENTER A TICKER TO ANALYZE"

if st.button(btn_label, disabled=not valid_tickers or st.session_state['running']):
    st.session_state['running'] = True
    st.session_state['result'] = None

    port_holds = [h for h in st.session_state['holdings'] if h['ticker'] and h['shares'] and h['cost']]
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

    prompt = f"""Analyze these stocks as a senior equity analyst: {cand_str}. {port_note}

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
      "pricing":{{"intrinsicValue":"$X","intrinsicMethod":"Blended","entryPrice":"$X — suggested entry price","entryRationale":"Based on: (1) intrinsic value with 15% margin of safety, (2) key technical support levels from 1-year price chart (50-day MA, 200-day MA, major support zones), and (3) historical price behavior near these levels. Cite the specific support level or MA that anchors this price.","analystConsensus":"$X","targetRange":"$X-$X"}},
      "ivBreakdown":[{{"method":"DCF","value":"$X","desc":"..."}},{{"method":"EV/EBITDA","value":"$X","desc":"..."}},{{"method":"Fwd P/E","value":"$X","desc":"..."}},{{"method":"P/FCF","value":"$X","desc":"..."}}],
      "topAnalysts":[{{"name":"...","firm":"...","accuracyPct":"XX%","rating":"Buy","target":"$X","thesis":"..."}}],
      "fundamentals":{{"revenue":{{"v":"$XB","sig":"good"}},"grossMargin":{{"v":"X%","sig":"good"}},"operatingMargin":{{"v":"X%","sig":"good"}},"netMargin":{{"v":"X%","sig":"good"}},"eps":{{"v":"$X","sig":"good"}},"forwardEPS":{{"v":"$X","sig":"ok"}},"peRatio":{{"v":"Xx","sig":"ok"}},"forwardPE":{{"v":"Xx","sig":"ok"}},"evEbitda":{{"v":"Xx","sig":"ok"}},"debtToEquity":{{"v":"X.X","sig":"ok"}},"freeCashFlow":{{"v":"$XB","sig":"good"}},"roe":{{"v":"X%","sig":"good"}},"divYield":{{"v":"X%","sig":"ok"}}}},
      "sectorAnalysis":{{
        "sector":"Sector name e.g. Utilities / Semiconductors / Cloud Software",
        "sectorOutlook":"2-3 sentences on current sector health, tailwinds, headwinds",
        "peerComparison":[
          {{"peer":"Ticker","metric":"P/E or EV/EBITDA","peerVal":"X×","stockVal":"X×","verdict":"Premium/Discount/Inline"}},
          {{"peer":"Ticker","metric":"Revenue Growth","peerVal":"X%","stockVal":"X%","verdict":"Above/Below/Inline"}},
          {{"peer":"Ticker","metric":"Net Margin","peerVal":"X%","stockVal":"X%","verdict":"Above/Below/Inline"}},
          {{"peer":"Ticker","metric":"FCF Yield","peerVal":"X%","stockVal":"X%","verdict":"Above/Below/Inline"}}
        ],
        "sectorRank":"e.g. Top quartile / Mid-tier / Laggard within sector",
        "sectorCatalysts":"Key upcoming sector catalysts e.g. rate cuts, regulation, AI capex",
        "sectorRisks":"Key sector-level risks e.g. margin compression, competition, regulation"
      }},
      "riskAnalysis":{{
        "overallRiskRating":"Low/Medium/High/Very High",
        "riskScore":65,
        "businessRisk":"Competitive threats, market share, business model vulnerabilities — 2 sentences",
        "financialRisk":"Debt levels, liquidity, interest coverage, refinancing risk — 2 sentences",
        "macroRisk":"Interest rate sensitivity, inflation exposure, GDP sensitivity — 2 sentences",
        "regulatoryRisk":"Regulatory threats, antitrust, environmental, policy risk — 2 sentences",
        "valuationRisk":"Downside if multiple compresses, earnings miss scenario — 2 sentences",
        "keyRisks":[
          {{"risk":"Short description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"One sentence"}},
          {{"risk":"Short description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"One sentence"}},
          {{"risk":"Short description","severity":"High/Medium/Low","likelihood":"High/Medium/Low","mitigation":"One sentence"}}
        ],
        "bearCasePrice":"$X — price in worst-case scenario",
        "bullCasePrice":"$X — price in best-case scenario"
      }},
      "sections":{{"valuation":"2 sentences","momentum":"2 sentences","sentiment":"2 sentences"}}
    }}
  }}
}}
CRITICAL STEP 1 — RESOLVE INPUTS TO TICKERS: Each input may be a ticker symbol OR a company name (possibly misspelled). Resolve each to the correct ticker symbol before analysis. Examples: "Apple" → AAPL, "Nvidia" → NVDA, "Vistra" → VST, "Mircosoft" → MSFT (fix typo), "visa inc" → V. Use the resolved ticker as the key in stocks{{}} and as the "ticker" field. If unsure, pick the closest match.
CRITICAL STEP 2 — stocks{{}} MUST contain ALL {len(valid_tickers)} resolved tickers (one per input): inputs were [{', '.join(valid_tickers)}]. comparisonTable[] must have all {len(valid_tickers)}. top2[] picks best 2 but ALL appear in stocks{{}}. Include 5 analysts per stock, thesis max 8 words.
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

    with st.status("Analyzing stocks...", expanded=True) as status:
        st.write(f"Researching {', '.join(valid_tickers)}...")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            st.write("Running valuations and fundamentals...")
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=12000,
                messages=[{"role": "user", "content": prompt}]
            )
            st.write("Building report...")
            txt = "".join(b.text for b in message.content if hasattr(b, 'text'))
            parsed = parse_json(txt)
            if not parsed:
                st.error(f"Could not parse response. Raw: {txt[:300]}")
            else:
                st.session_state['result'] = parsed
                status.update(label="Analysis complete!", state="complete")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            st.session_state['running'] = False

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state['result']:
    data = st.session_state['result']
    top2 = data.get('top2', [])
    stocks = data.get('stocks', {})
    ctable = data.get('comparisonTable', [])

    # Deduplicate stocks — keep all that Claude returned, just normalise keys
    # Do NOT filter against valid_tickers because Claude resolves names to symbols
    # e.g. user typed "Apple" but Claude returns key "AAPL" — both are valid
    clean_stocks = {}
    for k, v in stocks.items():
        tk = k.upper().strip()
        if tk and tk not in clean_stocks:
            clean_stocks[tk] = {**v, 'ticker': tk}
    stocks = clean_stocks
    # Also add any top2 tickers that somehow didn't make it into stocks{}
    for t2 in top2:
        tk2 = (t2.get('ticker') or '').upper().strip()
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

    # ── Top 2 picks ──
    st.markdown("## ★ TOP PICKS TO BUY")
    t2cols = st.columns(min(len(top2), 2))
    for i, t in enumerate(top2[:2]):
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
            entry_note = t.get('entryNote','')
            buy_reason = t.get('buyReason','')

            price_pills = ''
            if t2_iv:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #ffffff0a"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Intrinsic Value</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#a78bfa">{t2_iv}</span></div>'
            if t2_con:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid #ffffff0a"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Consensus Target</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#93c5fd">{t2_con}</span></div>'
            if t2_ent:
                price_pills += f'<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0"><span style="font-size:10px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Entry Price</span><span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:#4ade80">{t2_ent}</span></div>'

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
            input_as_field = s.get('inputAs','').upper().strip()
            for idx2, vt in enumerate(valid_tickers):
                if vt.upper() == tk or vt.upper() == input_as_field:
                    cand_idx = idx2
                    break
            # Last resort: use top2 rank to guess position
            if cand_idx < 0:
                ri2 = next((i for i,t in enumerate(top2) if t.get('ticker')==tk), -1)
                if ri2 >= 0 and ri2 < len(valid_tickers):
                    cand_idx = ri2
        cur_raw = st.session_state['prices'][cand_idx] if cand_idx >= 0 and st.session_state['prices'][cand_idx] else s.get('currentPrice','')
        cur_shares = st.session_state['shares'][cand_idx] if cand_idx >= 0 else ''
        vs = s.get('verdictStock','NEUTRAL')
        vp = s.get('verdictPortfolio','NEUTRAL')
        sent_num = None
        try: sent_num = int(re.sub(r'\D','', str(s.get('sentimentScore',''))))
        except: pass

        card_border = 'card-win' if is_win else ''
        win_star = ' ★' if is_win else ''

        # Pre-build all variables — keep f-string clean
        company_name   = s.get('companyName','')
        overall_score  = row.get('overallScore','—')
        input_as       = s.get('inputAs','')
        v_stock_reason = s.get('verdictStockReason','')
        v_port_reason  = s.get('verdictPortfolioReason','')
        port_label     = "Portfolio Synergy" if port_holds else "Portfolio Context"
        vc             = verdict_cls(vs)
        vcp            = verdict_cls(vp)
        v_icon_s       = verdict_icon(vs)
        v_icon_p       = verdict_icon(vp)
        iv_val         = pp.get('intrinsicValue','')
        cons_val       = pp.get('analystConsensus','')
        entry_val      = pp.get('entryPrice','')

        # Build conditional snippets
        price_part   = ("$" + cur_raw) if cur_raw   else ""
        shares_part  = cur_shares      if cur_shares else ""
        inputas_part = ("entered as: " + input_as) if (input_as and input_as.upper() != tk) else ""

        # Price strip — intrinsic value, consensus, entry
        price_strip = ''
        if iv_val or cons_val or entry_val:
            price_strip = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:10px">'
            if iv_val:
                price_strip += f'<div style="background:#0c0818;border:1px solid #7c3aed44;padding:8px 10px;"><div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Intrinsic Value</div><div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#a78bfa">{iv_val}</div></div>'
            else:
                price_strip += '<div></div>'
            if cons_val:
                price_strip += f'<div style="background:#080f1f;border:1px solid #3b82f644;padding:8px 10px;"><div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Consensus Target</div><div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#93c5fd">{cons_val}</div></div>'
            else:
                price_strip += '<div></div>'
            if entry_val:
                price_strip += f'<div style="background:#060f09;border:1px solid #16a34a44;padding:8px 10px;"><div style="font-size:9px;letter-spacing:1.5px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">Entry Price</div><div style="font-family:Syne,sans-serif;font-size:15px;font-weight:800;color:#4ade80">{entry_val}</div></div>'
            else:
                price_strip += '<div></div>'
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
            kc1, kc2, kc3 = st.columns(3)
            with kc1:
                iv = pp.get('intrinsicValue','—')
                st.markdown(f"""
                <div class="card card-purple">
                  <div class="label">Blended Intrinsic Value</div>
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
                sector_html = f"""
                <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px">
                  <div class="card" style="padding:10px 14px;flex:1;min-width:140px">
                    <div class="label">Sector</div>
                    <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#93c5fd">{sa.get("sector","—")}</div>
                  </div>
                  <div class="card" style="padding:10px 14px;flex:1;min-width:140px">
                    <div class="label">Sector Rank</div>
                    <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#f0f6ff">{sa.get("sectorRank","—")}</div>
                  </div>
                </div>
                <div class="sec-body" style="margin-bottom:10px">{sa.get("sectorOutlook","")}</div>"""
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
                    st.markdown(f'<table class="data-table"><thead><tr><th>Peer</th><th>Metric</th><th>Peer</th><th>This Stock</th><th>vs Peer</th></tr></thead><tbody>{peer_rows}</tbody></table>', unsafe_allow_html=True)

                # Sector catalysts + risks
                cat_risk_html = f"""
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px">
                  <div class="card card-green" style="padding:11px">
                    <div class="label">Sector Catalysts</div>
                    <div style="font-size:13px;color:#e2e8f0;line-height:1.8;margin-top:4px">{sa.get("sectorCatalysts","—")}</div>
                  </div>
                  <div class="card" style="padding:11px;border-color:#dc262644;background:#150505">
                    <div class="label">Sector Risks</div>
                    <div style="font-size:13px;color:#e2e8f0;line-height:1.8;margin-top:4px">{sa.get("sectorRisks","—")}</div>
                  </div>
                </div>"""
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
