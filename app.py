import streamlit as st
import anthropic
import json
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analyzer",
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
.verdict-reason { font-size:10px; color:#e2e8f0; margin-top:3px; line-height:1.5; }

.sec-hdr { font-family:'Syne',sans-serif; font-size:9px; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:#3b82f6; padding:8px 12px; background:#0d1825; border-bottom:1px solid #111c2a; margin-bottom:0; }
.sec-body { padding:12px; font-size:11px; line-height:1.85; color:#e2e8f0; background:#090f1a; border:1px solid #111c2a; margin-bottom:8px; }

.divider { height:1px; background:#111c2a; margin:16px 0; }
.disc { font-size:9px; color:#4a6a88; text-align:center; letter-spacing:1.5px; padding:20px 0; }

/* Rank badge */
.rank-gold { font-family:'Syne',sans-serif; font-size:11px; font-weight:700; color:#f59e0b; margin-right:4px; }
.rank-silver { font-family:'Syne',sans-serif; font-size:11px; font-weight:700; color:#9ca3af; margin-right:4px; }

/* Table */
.data-table { width:100%; border-collapse:collapse; font-size:11px; }
.data-table th { text-align:left; padding:7px 10px; font-size:8px; letter-spacing:2px; color:#94a3b8; text-transform:uppercase; border-bottom:1px solid #111c2a; background:#0d1825; font-family:'Syne',sans-serif; }
.data-table td { padding:8px 10px; border-bottom:1px solid #090f1a; vertical-align:top; color:#e2e8f0; }
.data-table tr:last-child td { border-bottom:none; }
.sig-good { color:#4ade80; } .sig-bad { color:#f87171; } .sig-ok { color:#fbbf24; }

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

ss('result', None)
ss('running', False)
ss('tickers', ['','',''])
ss('shares', ['','',''])
ss('prices', ['','',''])
ss('holdings', [{'ticker':'','shares':'','cost':''} for _ in range(10)])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:flex-end;gap:12px;margin-bottom:20px;padding-bottom:14px;border-bottom:1px solid #111c2a">
  <div style="width:8px;height:8px;background:#3b82f6;border-radius:50%;margin-bottom:4px;box-shadow:0 0 12px #3b82f6"></div>
  <div>
    <div style="font-size:9px;letter-spacing:4px;color:#3b82f6;text-transform:uppercase;margin-bottom:2px">Equity Research Terminal</div>
    <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#f0f6ff">STOCK ANALYZER</div>
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
with st.expander("▸ STOCKS TO ANALYZE (up to 3)", expanded=True):
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f'<div class="label">Stock {i+1}</div>', unsafe_allow_html=True)
            st.session_state['tickers'][i] = st.text_input(
                "Ticker", value=st.session_state['tickers'][i],
                placeholder="AAPL", max_chars=6, key=f"tk{i}",
                label_visibility="collapsed"
            ).upper().strip()
            st.markdown('<div class="label" style="margin-top:6px">Shares to Buy</div>', unsafe_allow_html=True)
            st.session_state['shares'][i] = st.text_input(
                "Shares", value=st.session_state['shares'][i],
                placeholder="0", key=f"sh{i}", label_visibility="collapsed"
            )
            st.markdown('<div class="label" style="margin-top:6px">Price to Buy $</div>', unsafe_allow_html=True)
            st.session_state['prices'][i] = st.text_input(
                "Price", value=st.session_state['prices'][i],
                placeholder="0.00", key=f"pr{i}", label_visibility="collapsed"
            )

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
      "ticker":"X","companyName":"...","currentPrice":"$X","summary":"one sentence",
      "verdictStock":"BULLISH","verdictStockReason":"one sentence",
      "verdictPortfolio":"BULLISH","verdictPortfolioReason":"one sentence",
      "sentimentScore":70,
      "portfolioInsights":{{"concentrationRisk":"...","sectorOverlap":"...","correlationNote":"...","diversificationImpact":"...","recommendation":"..."}},
      "pricing":{{"intrinsicValue":"$X","intrinsicMethod":"Blended","entryPrice":"$X","entryRationale":"...","analystConsensus":"$X","targetRange":"$X-$X"}},
      "ivBreakdown":[{{"method":"DCF","value":"$X","desc":"..."}},{{"method":"EV/EBITDA","value":"$X","desc":"..."}},{{"method":"Fwd P/E","value":"$X","desc":"..."}},{{"method":"P/FCF","value":"$X","desc":"..."}}],
      "topAnalysts":[{{"name":"...","firm":"...","accuracyPct":"XX%","rating":"Buy","target":"$X","thesis":"..."}}],
      "fundamentals":{{"revenue":{{"v":"$XB","sig":"good"}},"grossMargin":{{"v":"X%","sig":"good"}},"operatingMargin":{{"v":"X%","sig":"good"}},"netMargin":{{"v":"X%","sig":"good"}},"eps":{{"v":"$X","sig":"good"}},"forwardEPS":{{"v":"$X","sig":"ok"}},"peRatio":{{"v":"Xx","sig":"ok"}},"forwardPE":{{"v":"Xx","sig":"ok"}},"evEbitda":{{"v":"Xx","sig":"ok"}},"debtToEquity":{{"v":"X.X","sig":"ok"}},"freeCashFlow":{{"v":"$XB","sig":"good"}},"roe":{{"v":"X%","sig":"good"}},"divYield":{{"v":"X%","sig":"ok"}}}},
      "sections":{{"valuation":"one sentence","momentum":"one sentence","sentiment":"one sentence","risk":"one sentence"}}
    }}
  }}
}}
CRITICAL: stocks{{}} MUST contain ALL {len(valid_tickers)} tickers: {', '.join(valid_tickers)}. comparisonTable[] must have all {len(valid_tickers)}. top2[] picks best 2 but ALL appear in stocks{{}}. Include 5 analysts per stock, thesis max 8 words.
SECTOR-AWARE VALUATION — identify each stock's sector and apply correct assumptions:
Utilities (VST,NEE,DUK etc): WACC 7-9%, DCF terminal growth 1.5-2.5%, normalized FCF (3yr avg), EV/EBITDA 8-12x, P/E 14-18x, subtract actual net debt.
Tech/Growth (NVDA,MSFT,AAPL etc): WACC 9-12%, growth 2.5-4%, EV/EBITDA 20-40x, P/E 20-35x.
Show actual inputs in desc field e.g. "WACC 8.2%, g 2%, normalized FCF $1.8B".
All text fields max 10 words. Be extremely concise."""

    with st.status("Analyzing stocks...", expanded=True) as status:
        st.write(f"Researching {', '.join(valid_tickers)}...")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            st.write("Running valuations and fundamentals...")
            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=8000,
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

    # Deduplicate and filter to entered tickers only
    allowed = set(t.upper() for t in valid_tickers)
    clean_stocks = {}
    for k, v in stocks.items():
        tk = k.upper().strip()
        if tk in allowed and tk not in clean_stocks:
            clean_stocks[tk] = {**v, 'ticker': tk}
    stocks = clean_stocks

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
            st.markdown(f"""
            <div class="card {cls}" style="position:relative">
              <div style="position:absolute;top:0;right:0;font-family:'Syne',sans-serif;font-size:8px;font-weight:700;letter-spacing:2px;padding:3px 9px;background:{'#f59e0b' if i==0 else '#4b5563'};color:{'#000' if i==0 else '#fff'}">{lbl}</div>
              <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:#f0f6ff;margin-top:2px">{t.get('ticker','—')}</div>
              <div style="font-size:9px;color:#94a3b8;margin:2px 0 8px">{t.get('companyName','')}</div>
              <div style="display:flex;align-items:baseline;gap:4px;margin-bottom:8px">
                <span style="font-family:'Syne',sans-serif;font-size:18px;font-weight:800;color:{score_color}">{t.get('score','—')}</span>
                <span style="font-size:9px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">/ 10</span>
              </div>
              <div style="font-size:11px;color:#e2e8f0;line-height:1.7;border-top:1px solid #ffffff11;padding-top:8px">{t.get('buyReason','')}</div>
              <div style="font-size:10px;color:#4ade80;margin-top:6px">{('▸ ' + t.get('entryNote','')) if t.get('entryNote') else ''}</div>
            </div>
            """, unsafe_allow_html=True)

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
        cand_idx = valid_tickers.index(tk) if tk in valid_tickers else -1
        cur_raw = st.session_state['prices'][cand_idx] if cand_idx >= 0 and st.session_state['prices'][cand_idx] else s.get('currentPrice','')
        cur_shares = st.session_state['shares'][cand_idx] if cand_idx >= 0 else ''
        vs = s.get('verdictStock','NEUTRAL')
        vp = s.get('verdictPortfolio','NEUTRAL')
        sent_num = None
        try: sent_num = int(re.sub(r'\D','', str(s.get('sentimentScore',''))))
        except: pass

        card_border = 'card-win' if is_win else ''
        win_star = ' ★' if is_win else ''

        st.markdown(f"""
        <div class="card {card_border}" style="padding:0;overflow:hidden;margin-bottom:12px">
          <div style="padding:13px 14px 11px;background:#0d1825">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px">
              <div>
                <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;color:#f0f6ff;letter-spacing:2px">
                  {rank_badge}{tk}{win_star}
                </div>
                <div style="font-size:10px;color:#94a3b8;margin-top:2px">{s.get('companyName','')}</div>
                <div style="display:flex;align-items:center;gap:8px;margin-top:4px">
                  {'<span style="font-size:12px;color:#93c5fd;font-weight:700">$'+cur_raw+'</span>' if cur_raw else ''}
                  {'<span style="font-size:10px;color:#cbd5e1">· '+cur_shares+' shares</span>' if cur_shares else ''}
                </div>
              </div>
              <div style="text-align:right">
                <div style="font-family:'Syne',sans-serif;font-size:17px;font-weight:800;color:#e2e8f0">{row.get('overallScore','—')}</div>
                <div style="font-size:8px;color:#94a3b8;letter-spacing:1px;text-transform:uppercase">Score</div>
              </div>
            </div>
        """, unsafe_allow_html=True)

        # Verdict pills
        vc = verdict_cls(vs)
        vcp = verdict_cls(vp)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="verdict-{vc}">
              <div class="verdict-tag verdict-tag-{vc}">Standalone Verdict</div>
              <div class="verdict-label-{vc}">{verdict_icon(vs)} {vs}</div>
              <div class="verdict-reason">{s.get('verdictStockReason','')}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            port_label = "Portfolio Synergy" if port_holds else "Portfolio Context"
            st.markdown(f"""
            <div class="verdict-{vcp}">
              <div class="verdict-tag verdict-tag-{vcp}">{port_label}</div>
              <div class="verdict-label-{vcp}">{verdict_icon(vp)} {vp}</div>
              <div class="verdict-reason">{s.get('verdictPortfolioReason','')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

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
                  <div class="label">Entry Price</div>
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
                          <div style="font-size:7px;letter-spacing:2px;color:#94a3b8;text-transform:uppercase;margin-bottom:3px">{iv.get('method','')}</div>
                          <div style="font-family:'Syne',sans-serif;font-size:14px;font-weight:700;color:#a78bfa">{iv.get('value','—')}</div>
                          <div style="font-size:9px;color:#cbd5e1;margin-top:2px;line-height:1.4">{iv.get('desc','')}</div>
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
                  {'<div style="font-family:Syne,sans-serif;font-size:26px;font-weight:800;color:'+sent_color+'">'+str(sent_num)+'<span style="font-size:13px;color:#5a7a99">/100</span></div><div style="font-size:10px;color:#cbd5e1;margin-top:2px">'+sent_label+'</div>' if sent_num is not None else '<div style="font-size:11px;color:#e2e8f0;line-height:1.7">'+(s.get('sections',{}).get('sentiment','—'))+'</div>'}
                </div>""", unsafe_allow_html=True)
            with sc2:
                st.markdown(f"""
                <div class="card" style="padding:11px">
                  <div class="label">Risk Profile</div>
                  <div style="font-size:11px;color:#e2e8f0;line-height:1.7">{s.get('sections',{}).get('risk','—')}</div>
                </div>""", unsafe_allow_html=True)

            # Portfolio insights
            pi = s.get('portfolioInsights', {})
            port_holds_check = [h for h in st.session_state['holdings'] if h['ticker'] and h['shares'] and h['cost']]
            if pi and port_holds_check:
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
                        frows += f'<tr><td class="mn">{lbl}</td><td style="color:#fff;font-weight:700">{r["v"]}</td><td>{sig_html}</td><td style="font-size:9px;color:#94a3b8">{note}</td></tr>'
                st.markdown(f'<table class="data-table"><thead><tr><th>Metric</th><th>Value</th><th>Signal</th><th>Note</th></tr></thead><tbody>{frows}</tbody></table>', unsafe_allow_html=True)

            # Valuation + Momentum sections
            secs = s.get('sections', {})
            for key, icon, lbl in [("valuation","◎","Valuation Analysis"),("momentum","△","Price Momentum")]:
                if secs.get(key):
                    st.markdown(f'<div class="sec-hdr">{icon} {lbl}</div><div class="sec-body">{secs[key]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="disc">FOR INFORMATIONAL PURPOSES ONLY — NOT FINANCIAL ADVICE</div>', unsafe_allow_html=True)
