"""
ui_theme.py
===========
"Kolam" UI for PulseGrid AI: one CSS block plus small functions that return HTML strings.
Presentation only. Every web/model string goes through esc(); links are http/https only.
"""

import html
import math
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import streamlit as st

# Switch to st.markdown(..., unsafe_allow_html=True) here if st.html ever drops something.
def render(markup: str, target=None) -> None:
    (target or st).markdown(_flat(markup), unsafe_allow_html=True)


def _flat(s: str) -> str:
    """Collapses newlines/indent so markdown never turns HTML into code blocks."""
    return re.sub(r"\s*\n\s*", "", s)


def esc(x: Any) -> str:
    text = " ".join(str(x if x is not None else "").split())
    return html.escape(text, quote=True).replace("$", "&#36;")


def safe_url(url: str) -> Optional[str]:
    try:
        p = urlparse(str(url))
    except Exception:
        return None
    return str(url) if p.scheme in ("http", "https") and p.netloc else None


def link(url: str, text: str, cls: str = "src") -> str:
    u = safe_url(url)
    if not u:
        return f'<span class="{cls}">{esc(text)}</span>'
    return f'<a class="{cls}" href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(text)}</a>'


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=Mukta:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#0B1026; --panel:#131A3C; --panel2:#10173A; --inner:#0E1430; --line:#252E5C; --line2:#333D72;
  --cream:#F3EBDD; --text2:#C9C6D6; --muted:#A7ACC8; --turm:#E9A93B; --turm2:#F3C77A;
  --green:#5CC489; --green-t:#7FD8A4; --green-bg:#12203A; --green-b:#23415A; --green-badge:#1E3B2C;
  --red:#EE6A5C; --red-t:#FF9B8F; --red-bg:#2A1420; --red-b:#5A2A33; --red-badge:#4A1D24; --dot:#59618F;
}
header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important;}
.stApp{
  background-color:var(--bg);
  background-image:radial-gradient(rgba(243,235,221,0.09) 1.2px, transparent 1.4px);
  background-size:28px 28px; color:var(--cream); font-family:'Mukta',sans-serif;
}
.block-container{max-width:1080px !important; padding:24px 5% 64px !important;}
[data-testid="stVerticalBlock"]{gap:24px;}
h1,h2,h3,.raj{font-family:'Rajdhani',sans-serif;}
.mono{font-family:'JetBrains Mono',monospace;}

/* header */
.pg-head{display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
.pg-head .t{font:700 24px 'Rajdhani',sans-serif;color:var(--cream);line-height:1.1;}
.pg-head .s{font-size:13px;color:var(--muted);}
.pg-rule{border-bottom:1px solid var(--line);margin-top:-8px;}
[data-testid="stTextInput"] label p{font:600 12px 'Rajdhani',sans-serif !important;letter-spacing:.14em;text-transform:uppercase;color:var(--muted) !important;}
[data-testid="stTextInput"] input{height:44px;background:var(--inner) !important;border:1px solid var(--line2) !important;border-radius:6px !important;color:var(--cream) !important;font-family:'JetBrains Mono',monospace !important;font-size:14px !important;}
[data-testid="stTextInput"] input:focus{border-color:var(--turm) !important;box-shadow:none !important;}
.stButton > button, [data-testid="stDownloadButton"] button{
  height:44px;border-radius:6px;font:700 15px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;transition:all .15s;}
.stButton > button[kind="primary"]{background:var(--turm);color:#1A1206;border:1px solid var(--turm);}
.stButton > button[kind="primary"]:hover{background:var(--turm2);border-color:var(--turm2);color:#1A1206;}
.stButton > button[kind="secondary"]{background:transparent;color:var(--turm);border:1px solid var(--turm);}
.stButton > button[kind="secondary"]:hover,[data-testid="stDownloadButton"] button:hover{background:rgba(233,169,59,.12);color:var(--turm2);border-color:var(--turm2);}
[data-testid="stDownloadButton"] button{background:transparent;color:var(--muted);border:1px solid var(--line2);}
[data-testid="stDownloadButton"] button p{color:inherit;}
[data-testid="stTextInputRootElement"],[data-baseweb="input"],[data-baseweb="base-input"]{background:var(--inner) !important;border:1px solid var(--line2) !important;border-radius:6px !important;}
[data-baseweb="input"]:focus-within{border-color:var(--turm) !important;}
[data-testid="stTextInput"] input::placeholder{color:var(--muted) !important;opacity:.7;}

/* common */
.eyebrow{font:600 14px 'Mukta',sans-serif;color:var(--turm);letter-spacing:.04em;}
.label{font:600 13px 'Rajdhani',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);}
.h1{font:600 clamp(26px,3.4vw,40px)/1.15 'Rajdhani',sans-serif;color:var(--cream);margin:8px 0 12px;}
.p2{color:var(--text2);font-size:16px;line-height:1.6;}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:30px;}
.panel.alt{background:var(--panel2);}
.row2{display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start;}
.row2 > .col{flex:1 1 360px;min-width:0;}

/* screen 1 */
.agent{display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:13px;}
.agent .n{color:var(--cream);letter-spacing:.06em;} .agent .n i{color:var(--muted);font-style:normal;}
.st-done{color:var(--green-t);} .st-run{color:var(--turm2);} .st-wait{color:var(--muted);}
.stage{display:flex;gap:16px;align-items:center;flex-wrap:wrap;padding:14px 0;border-bottom:1px solid var(--line);}
.stages{border-top:1px solid var(--line);margin-top:24px;}
.stage .en{flex:1 1 100%;font:600 15px 'Rajdhani',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--cream);}
.stage .ds{flex:1 1 220px;font-size:14px;color:var(--text2);}
.stage .stt{font:500 12px 'JetBrains Mono',monospace;letter-spacing:.08em;}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:14px;}
.legend b{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle;}
.svgbox{overflow-x:auto;}
.pulse{animation:pulse 1.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center;}
@keyframes pulse{0%,100%{opacity:.45;transform:scale(1)}50%{opacity:1;transform:scale(1.5)}}
.draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.6s ease forwards;}
@keyframes draw{to{stroke-dashoffset:0}}

/* screen 2 */
.status{font-size:13px;color:var(--muted);display:flex;gap:18px;flex-wrap:wrap;align-items:center;}
.live{color:var(--green-t);font-family:'JetBrains Mono',monospace;}
.sim{background:#B91C1C;color:#fff;font:700 15px 'Rajdhani',sans-serif;letter-spacing:.12em;padding:4px 12px;border-radius:6px;}
.hero{display:flex;gap:32px;flex-wrap:wrap;}
.hero .main{flex:2 1 460px;} .hero .side{flex:1 1 280px;position:relative;overflow:hidden;min-height:260px;}
.hero .side svg{position:absolute;inset:0;width:100%;height:100%;opacity:.28;}
.hero .side .in{position:relative;text-align:center;padding:12px 0;}
.big{font:700 84px/1 'Rajdhani',sans-serif;color:var(--cream);} .big small{font-size:34px;color:var(--turm2);margin-left:2px;}
.pill{display:inline-block;background:#3A2C10;color:var(--turm2);font:600 13px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;padding:5px 14px;border-radius:999px;margin:10px 0;}
.cap{font-size:13px;color:var(--muted);}
.stitle{font:700 18px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--cream);}
.stitle .sub{font:400 13px 'Mukta',sans-serif;letter-spacing:0;text-transform:none;color:var(--muted);margin-left:8px;}
.ev{display:flex;gap:14px;padding:14px 16px;border-radius:10px;margin-top:12px;border:1px solid;}
.ev.sup{background:var(--green-bg);border-color:var(--green-b);} .ev.con{background:var(--red-bg);border-color:var(--red-b);}
.ev .bd{flex:0 0 28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 18px 'Rajdhani',sans-serif;}
.sup .bd{background:var(--green-badge);color:var(--green-t);} .con .bd{background:var(--red-badge);color:var(--red-t);}
.ev .cl{font-size:15px;line-height:1.5;color:var(--cream);}
.ev .mt{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:8px;font:400 12px 'JetBrains Mono',monospace;color:var(--muted);}
.ev .tag{font:600 12px 'Rajdhani',sans-serif;letter-spacing:.08em;padding:2px 8px;border-radius:4px;background:var(--inner);color:var(--text2);}
a.src{color:var(--turm2);text-decoration:none;word-break:break-all;} a.src:hover{text-decoration:underline;}
.qbox{border:1px dashed var(--line2);border-radius:10px;padding:14px 16px;margin-top:14px;font:400 12px 'JetBrains Mono',monospace;color:var(--muted);}
.qbox div{margin-top:6px;color:var(--text2);}
.empty{color:var(--muted);font-size:14px;margin-top:12px;}
.fac{margin-top:16px;} .fac .top{display:flex;justify-content:space-between;gap:12px;font-size:14px;color:var(--text2);}
.fac .top span:last-child{font-family:'JetBrains Mono',monospace;color:var(--cream);}
.bar{height:6px;border-radius:3px;background:var(--inner);margin-top:6px;overflow:hidden;} .bar i{display:block;height:100%;border-radius:3px;}
.why{background:var(--inner);border:1px solid var(--line);border-radius:10px;padding:18px;margin-top:22px;}
.why .k{font:700 14px 'Rajdhani',sans-serif;letter-spacing:.12em;color:var(--turm);text-transform:uppercase;}
.why p{margin:8px 0 0;color:var(--text2);line-height:1.6;font-size:15px;}
.watch{display:flex;gap:14px;margin-top:14px;color:var(--text2);line-height:1.55;font-size:15px;}
.watch b{flex:0 0 28px;height:28px;border-radius:50%;border:1px solid var(--turm);color:var(--turm);display:flex;align-items:center;justify-content:center;font:700 14px 'Rajdhani',sans-serif;}
[data-testid="stExpander"]{background:var(--panel);border:1px solid var(--line);border-radius:10px;}
[data-testid="stExpander"] summary p{font:700 14px 'Rajdhani',sans-serif !important;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}
.sim-banner{background:#DC2626;color:#fff;font:700 clamp(18px,3vw,28px) 'Rajdhani',sans-serif;letter-spacing:.1em;text-align:center;padding:14px;border-radius:10px;}
.tt{width:100%;border-collapse:collapse;font-size:14px;min-width:560px;}
.tt th{font:600 12px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);}
.tt td{padding:10px;border-bottom:1px solid var(--line);color:var(--text2);vertical-align:top;}
.sk{font:400 12px 'Mukta',sans-serif;letter-spacing:0;color:#A3A9C8;margin-left:10px;text-transform:none;}
.sl{font:600 16px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--cream);line-height:1.35;}
.sl.sm{font-size:14px;}
.foot{margin-top:56px;padding-top:16px;border-top:1px solid var(--line);font:400 12px 'Mukta',sans-serif;color:#A3A9C8;line-height:1.6;}
.foot .info{display:inline-block;width:16px;height:16px;line-height:16px;text-align:center;border:1px solid #A3A9C8;border-radius:50%;font-size:11px;margin-right:8px;cursor:help;}
.tag[title]{cursor:help;}
@media (max-width:640px){.sl .sk{display:block;margin-left:0;margin-top:2px;}}
[role="tablist"]{gap:28px;border-bottom:1px solid var(--line);background:transparent !important;}
[data-testid="stTab"]{background:transparent !important;padding:10px 0 !important;height:auto !important;}
[data-testid="stTab"], [data-testid="stTab"] *{font-family:'Rajdhani',sans-serif !important;font-weight:600 !important;font-size:14px !important;letter-spacing:.12em;text-transform:uppercase;color:var(--muted) !important;}
[data-testid="stTab"][aria-selected="true"], [data-testid="stTab"][aria-selected="true"] *{color:var(--cream) !important;}
.react-aria-SelectionIndicator{background:var(--turm) !important;height:2px !important;}
[role="tabpanel"]{padding-top:24px !important;}
.sum{display:flex;gap:48px;flex-wrap:wrap;align-items:flex-start;}
.sum .l{flex:3 1 420px;min-width:0;} .sum .r{flex:2 1 300px;min-width:0;}
.scale{display:flex;height:8px;border-radius:4px;overflow:hidden;position:relative;margin-top:14px;}
.scale i{display:block;height:100%;}
.scale-wrap{position:relative;}
.scale-wrap .mk{position:absolute;top:8px;width:3px;height:16px;background:var(--turm);border-radius:2px;}
.scale-l{display:flex;font:500 11px 'JetBrains Mono',monospace;color:var(--muted);margin-top:6px;}
.facts{font:400 13px 'JetBrains Mono',monospace;color:var(--text2);margin-top:24px;padding-top:16px;border-top:1px solid var(--line);display:flex;gap:10px 22px;flex-wrap:wrap;}
.facts b{color:var(--turm2);font-weight:500;}
.outc{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;}
.qrow{display:flex;gap:14px;flex-wrap:wrap;padding:12px 0;border-bottom:1px solid var(--line);align-items:baseline;}
.qrow .qt{flex:0 0 118px;font:500 12px 'JetBrains Mono',monospace;color:var(--muted);} .qrow .qq{flex:1 1 260px;font:400 13px 'JetBrains Mono',monospace;color:var(--cream);}
.warn{background:#3A2C10;color:var(--turm2);border-radius:8px;padding:10px 14px;font-size:14px;margin-top:12px;}

@media (max-width:640px){.panel{padding:20px;} .big{font-size:64px;}}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important;} .draw{stroke-dashoffset:0;}}
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ header
LOGO = """<svg width="44" height="44" viewBox="0 0 48 48" aria-hidden="true">
<polygon points="24,3 45,24 24,45 3,24" fill="none" stroke="#F3EBDD" stroke-width="1.6" opacity=".7"/>
<rect x="9" y="9" width="30" height="30" rx="9" fill="none" stroke="#E9A93B" stroke-width="2"/>
<g fill="#F3EBDD"><circle cx="14" cy="14" r="1.8"/><circle cx="24" cy="14" r="1.8"/><circle cx="34" cy="14" r="1.8"/>
<circle cx="14" cy="24" r="1.8"/><circle cx="34" cy="24" r="1.8"/><circle cx="14" cy="34" r="1.8"/>
<circle cx="24" cy="34" r="1.8"/><circle cx="34" cy="34" r="1.8"/></g><circle cx="24" cy="24" r="3.4" fill="#E9A93B"/></svg>"""


def section_label(english: str, devanagari: str = "", roman: str = "", small: bool = False) -> str:
    """Heading used everywhere: English first and primary; Sanskrit (if any) after it, smaller and quieter."""
    sk = f'<span class="sk">{esc(devanagari)} {esc(roman)}</span>' if devanagari else ""
    return f'<div class="sl{" sm" if small else ""}">{esc(english)}{sk}</div>'


def sim_banner_html() -> str:
    return '<div class="sim-banner">SIMULATED DATA — NOT LIVE</div>'


def header_html() -> str:
    return f"""<div class="pg-head">{LOGO}<div><div class="t">PulseGrid AI</div>
<div class="s">Competitive intelligence that argues with itself</div></div></div>"""


def divider_html() -> str:
    return '<div class="pg-rule"></div>'


def idle_html(tavily_ok: bool, nebius_ok: bool, model: str) -> str:
    t = '<span class="st-done">Tavily ready</span>' if tavily_ok else '<span style="color:#FF9B8F">Tavily not configured</span>'
    n = f'<span class="st-done">Nebius ready · {esc(model)}</span>' if nebius_ok else '<span style="color:#FF9B8F">Nebius not configured</span>'
    return f"""<div class="panel alt" style="text-align:center;padding:56px 24px">
<div class="eyebrow">Ready</div><div class="h1">Name a company. Watch the agent argue with itself.</div>
<div class="p2">Four agents search the live web, one hypothesis forms, then the agent tries to break it.</div>
<div class="status mono" style="justify-content:center;margin-top:18px">{t}<span>·</span>{n}</div></div>"""


# ------------------------------------------------------------------ screen 1: live
AGENTS = [("TALENT", "careers, roles"), ("PRODUCT", "pricing, docs"),
          ("FRICTION", "forums, reviews"), ("MARKET", "news, funding")]
STAGES = [("Sort evidence", "प्रमाण", "Pramana", "Seen directly, or reported by others"),
          ("Form hypothesis", "अनुमान", "Anumana", "Connect the dots into one hypothesis"),
          ("Challenge hypothesis", "पूर्वपक्ष", "Purva Paksha", "Search for evidence that proves it wrong"),
          ("Verdict", "निर्णय", "Nirnaya", "Confidence, and what to watch")]

_GRID = [(60 + 70 * i, 60 + 70 * j) for j in range(5) for i in range(5) if (i, j) != (2, 2)]


def _ring_order():
    def key(p):
        dx, dy = (p[0] - 200) / 70, (p[1] - 200) / 70
        return (max(abs(dx), abs(dy)), math.atan2(dy, dx))
    return sorted(_GRID, key=key)


def pulli_svg(lit: int, arriving: int, stages_done: int) -> str:
    order = _ring_order()
    lit = max(0, min(lit, len(order)))
    arriving = max(0, min(arriving, len(order) - lit))
    dots = []
    for idx, (x, y) in enumerate(order):
        if idx < lit:
            dots.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#5CC489"/>')
        elif idx < lit + arriving:
            dots.append(f'<circle class="pulse" cx="{x}" cy="{y}" r="6" fill="#E9A93B"/>')
        else:
            dots.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#59618F"/>')
    # decorative kolam loops through the lit dots; count follows real stage progress
    pts = order[:lit]
    n_curves = min(max(len(pts) - 1, 0), 2 + stages_done * 4) if pts else 0
    paths = []
    for k in range(n_curves):
        (x1, y1), (x2, y2) = pts[k], pts[k + 1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        cx, cy = mx + (200 - mx) * 0.55, my + (200 - my) * 0.55
        cls = "draw" if k >= n_curves - 2 else ""
        paths.append(f'<path pathLength="1" class="{cls}" d="M{x1},{y1} Q{cx:.1f},{cy:.1f} {x2},{y2}" fill="none" '
                     f'stroke="#E9A93B" stroke-width="2.2" stroke-linecap="round"/>')
    return f"""<svg viewBox="0 0 400 400" width="100%" style="max-width:440px;display:block;margin:0 auto" role="img" aria-label="Pulli kolam showing signals found so far">
<polygon points="200,30 370,200 200,370 30,200" fill="none" stroke="#F3EBDD" stroke-opacity=".14" stroke-dasharray="4 6"/>
<circle cx="200" cy="200" r="150" fill="none" stroke="#F3EBDD" stroke-opacity=".14" stroke-dasharray="4 6"/>
{''.join(paths)}{''.join(dots)}<circle cx="200" cy="200" r="9" fill="#E9A93B"/></svg>"""


def live_html(stream_counts: Optional[List[int]], stages_done: int) -> str:
    """stream_counts None = still searching. stages_done 0-4 = finished stages."""
    rows = []
    for i, (name, desc) in enumerate(AGENTS):
        if stream_counts is None:
            st_html = '<span class="st-run">● searching…</span>'
        else:
            st_html = f'<span class="st-done">✓ {int(stream_counts[i])} signals</span>'
        rows.append(f'<div class="agent"><span class="n">{name} <i>· {desc}</i></span>{st_html}</div>')
    stage_rows = []
    searching_done = stream_counts is not None
    for i, (en, dv, rm, ds) in enumerate(STAGES):
        if i < stages_done:
            s, cls = "DONE", "st-done"
        elif i == stages_done and searching_done:
            s, cls = "RUNNING", "st-run"
        else:
            s, cls = "WAITING", "st-wait"
        stage_rows.append(f'<div class="stage"><span class="en">{esc(en)}<span class="sk">{esc(dv)} {esc(rm)}</span></span>'
                          f'<span class="ds">{esc(ds)}</span><span class="stt {cls}">{s}</span></div>')
    total = sum(stream_counts) if stream_counts else 0
    svg = pulli_svg(total, 4 if stream_counts is None else 0, stages_done)
    return f"""<div class="row2"><div class="col">
{section_label("Four agents in the field", "गुप्तचर", "Guptachar")}<div class="h1" style="font-size:40px">The pattern is being drawn.</div>
<div class="p2">Each agent searches one corner of the live web. Nothing is concluded until all four report.</div>
<div style="margin-top:22px">{''.join(rows)}</div><div class="stages">{''.join(stage_rows)}</div></div>
<div class="col"><div class="panel alt"><div class="svgbox">{svg}</div>
<div class="legend"><span><b style="background:#5CC489"></b>confirmed signals</span><span><b style="background:#E9A93B"></b>arriving now</span><span><b style="background:#59618F"></b>no signal yet</span></div>
<div class="cap" style="margin-top:14px">When the pattern closes, the hypothesis forms. Then it tries to prove itself wrong.</div></div></div></div>"""


# ------------------------------------------------------------------ screen 2: results
def status_html(diff: Dict[str, Any], simulated: bool, model: str, backend: str) -> str:
    if diff.get("first_scan"):
        cmp_txt = "First scan — baseline saved"
    else:
        n = len(diff.get("new_signals", []))
        cmp_txt = f"Compared with the previous saved baseline · {n} new source{'s' if n != 1 else ''}"
    if simulated:
        tag = '<span class="sim">SIMULATED DATA — NOT LIVE</span>'
    else:
        tag = f'<span class="live">● Live · {esc(model)} on Nebius Token Factory · Tavily</span>'
    return f'<div class="status"><span>{esc(cmp_txt)}</span>{tag}<span class="mono">store: {esc(backend)}</span></div>'


JAALI = """<svg viewBox="0 0 300 260" preserveAspectRatio="xMidYMid slice" aria-hidden="true" fill="none" stroke="#E9A93B" stroke-width="1.2">
<polygon points="150,10 290,130 150,250 10,130"/><rect x="60" y="40" width="180" height="180" rx="28"/><circle cx="150" cy="130" r="82"/>
<path d="M150,48 C220,90 220,170 150,212 C80,170 80,90 150,48Z"/></svg>"""


_ROWS = [("TALENT", "Talent"), ("PRODUCT", "Product"), ("FRICTION", "Customer Friction"), ("MARKET", "Market")]


def pulse_grid_html(d: Dict[str, Any], raw_streams: List[Dict[str, Any]]) -> str:
    sup = {e["url"] for e in d["supporting"]}
    con = {e["url"] for e in d["contradicting"]}
    labels, dots, pos = [], [], {}

    def label(y, txt):
        labels.append(f'<text x="0" y="{y + 4}" fill="#A7ACC8" font-family="Rajdhani" font-weight="600" font-size="13" letter-spacing="1.6">{txt}</text>')

    def gray(x, y):
        dots.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#59618F"/>')

    for i, (lab, key) in enumerate(_ROWS):
        y = 45 + 60 * i
        label(y, lab)
        items = []
        for s in raw_streams:
            if key.lower() in s.get("category", "").lower():
                items = s.get("results", [])
        for j in range(12):
            x = 140 + 60 * j
            if j < len(items) and items[j].get("url") in sup:
                pos.setdefault(items[j]["url"], (x, y))
                dots.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#5CC489"><title>{esc(items[j].get("title"))}</title></circle>')
            else:
                gray(x, y)
    y = 45 + 60 * 4
    label(y, "COUNTER-SEARCH")
    adv = d.get("adversarial_results", [])
    for j in range(12):
        x = 140 + 60 * j
        if j < len(adv) and adv[j]["url"] in con:
            pos.setdefault(adv[j]["url"], (x, y))
            dots.append(f'<rect x="{x - 6}" y="{y - 6}" width="12" height="12" fill="#EE6A5C" transform="rotate(45 {x} {y})"><title>{esc(adv[j]["title"])}</title></rect>')
        else:
            gray(x, y)

    def curve(p1, p2, color, dash=""):
        (x1, y1), (x2, y2) = p1, p2
        bulge = -34 if y1 == y2 else 0
        cx, cy = (x1 + x2) / 2 + (30 if y1 != y2 else 0), (y1 + y2) / 2 + bulge
        return (f'<path d="M{x1},{y1} Q{cx:.0f},{cy:.0f} {x2},{y2}" fill="none" stroke="{color}" stroke-width="1.8" '
                f'stroke-linecap="round" opacity=".85" {dash}/>')

    curves = []
    for l in d.get("links", []):
        if l["from_url"] in pos and l["to_url"] in pos:
            curves.append(curve(pos[l["from_url"]], pos[l["to_url"]], "#E9A93B"))
    for e in d["contradicting"]:
        for t in e.get("target_urls", []):
            if e["url"] in pos and t in pos:
                curves.append(curve(pos[e["url"]], pos[t], "#EE6A5C", 'stroke-dasharray="5 5"'))
    note = "" if curves else '<div class="cap" style="margin-top:8px">The model did not report links between evidence items for this scan.</div>'
    return f"""<div class="panel">{section_label("The Pulse Grid")}<div class="cap" style="margin-top:4px">Dots are signals; lines are connections the model reported.</div>
<div class="legend"><span><b style="background:#5CC489"></b>supports</span><span><b style="background:#EE6A5C;border-radius:2px;transform:rotate(45deg)"></b>contradicts</span><span><b style="background:#59618F"></b>no signal</span><span><b style="background:#E9A93B;height:3px;border-radius:0"></b>reinforces</span><span><b style="background:#EE6A5C;height:3px;border-radius:0"></b>undermines</span></div>{note}
<div class="svgbox" style="margin-top:12px"><svg viewBox="0 0 900 330" width="100%" style="min-width:640px" role="img" aria-label="Evidence grid by stream">{''.join(labels)}{''.join(curves)}{''.join(dots)}</svg></div></div>"""


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def tag_html(source_type: str) -> str:
    """Plain-English evidence tag; the Sanskrit term lives only in the hover tooltip."""
    if source_type == "Primary":
        text, tip = "Official source", "Pratyaksha — direct evidence"
    elif source_type == "Community":
        text, tip = "Community post", "Shabda — reported testimony"
    else:
        text, tip = "News report", "Shabda — reported testimony"
    return f'<span class="tag" title="{esc(tip)}">{text}</span>'


def evidence_card(e: Dict[str, Any], kind: str) -> str:
    badge = "+" if kind == "sup" else "−"
    date = f'<span>{esc(str(e["published_date"])[:10])}</span>' if e.get("published_date") else ""
    return f"""<div class="ev {kind}"><div class="bd">{badge}</div><div><div class="cl">{esc(e['claim'] or e['title'])}</div>
<div class="mt">{tag_html(e['source_type'])}{link(e['url'], _domain(e['url']))}{date}</div></div></div>"""


def calc_html(d: Dict[str, Any]) -> str:
    c = d["confidence"]
    rows = []
    for b in c["breakdown"]:
        color = "#E9A93B" if b["key"] == "support_share" else "#5CC489"
        w = max(0, min(100, b["value"] * 100))
        rows.append(f'<div class="fac"><div class="top"><span>{esc(b["label"])}</span><span>+{b["points"]:.1f}</span></div>'
                    f'<div class="bar"><i style="width:{w:.0f}%;background:{color}"></i></div>'
                    f'<div class="cap" style="margin-top:4px">{esc(b["note"])}</div></div>')
    caps = "".join(f'<div class="warn">{esc(x)}</div>' for x in c["caps"])
    h = c.get("history")
    if h:
        base = f' · evidence score {c["base_score"]:g}%' if h.get("adjustment") else ""
        caps += f'<div class="cap" style="margin-top:14px">Track record · {esc(h["message"])}{esc(base)}</div>'
    return f"""<div class="panel">{section_label("Verdict · how the score was calculated", "निर्णय", "Nirnaya")}{''.join(rows)}{caps}
<div class="why"><div class="k">Why not higher?</div><p>{esc(d['why_not_higher'])}</p></div></div>"""


# ------------------------------------------------------------------ smriti / track record
_STATUS_COLOR = {"pending": "#A7ACC8", "confirmed": "#7FD8A4", "refuted": "#FF9B8F", "expired": "#59618F"}


def suggestion_html(sg: Dict[str, Any]) -> str:
    color = "#7FD8A4" if sg["suggestion"] == "confirmed" else "#FF9B8F"
    return f"""<div class="ev {'sup' if sg['suggestion'] == 'confirmed' else 'con'}"><div>
<div class="label">Model suggestion · needs your review</div>
<div class="cl" style="margin-top:6px">Earlier prediction: {esc(sg['hypothesis'])}</div>
<div class="cl" style="margin-top:6px;color:{color}">Suggested: {esc(sg['suggestion'].upper())} — {esc(sg['reason'])}</div>
<div class="mt">{link(sg['url'], sg['title'] or _domain(sg['url']))}</div></div></div>"""


def smriti_html(rows: List[Dict[str, Any]], stats: List[Dict[str, Any]], backend: str) -> str:
    if rows:
        trs = []
        for r in rows[:25]:
            st_ = r.get("status", "pending")
            out = link(r["resolution_url"], _domain(r["resolution_url"])) if r.get("resolution_url") else ""
            trs.append(f'<tr><td class="mono">{esc(str(r.get("created_at", ""))[:10])}</td><td>{esc(r.get("company_name") or r.get("company_slug"))}</td>'
                       f'<td>{esc(r.get("hypothesis"))}</td><td class="mono">{esc(r.get("confidence"))}%</td>'
                       f'<td class="mono" style="color:{_STATUS_COLOR.get(st_, "#A7ACC8")}">{esc(st_)}</td><td>{out}</td></tr>')
        table = ('<div class="svgbox"><table class="tt"><tr><th>Date</th><th>Company</th><th>Hypothesis</th><th>Conf.</th>'
                 f'<th>Status</th><th>Outcome</th></tr>{"".join(trs)}</table></div>')
    else:
        table = '<div class="empty">No predictions yet. Every live investigation is saved here automatically.</div>'
    if stats:
        parts = []
        for g in stats:
            hit = "—" if g["hit_rate"] is None else f'{g["hit_rate"]:.0%}'
            learn = "learning active" if g["resolved"] >= 5 else f'not enough history ({g["resolved"]}/5)'
            parts.append(f'<tr><td class="mono">{esc(" + ".join(g["pattern"]) or "—")}</td><td>{esc(g["industry"])}</td>'
                         f'<td class="mono">{g["resolved"]}</td><td class="mono">{g["pending"]}</td>'
                         f'<td class="mono">{hit}</td><td class="cap">{esc(learn)}</td></tr>')
        srows = "".join(parts)
        stable = ('<div class="svgbox"><table class="tt"><tr><th>Pattern</th><th>Industry</th><th>Resolved</th><th>Pending</th>'
                  f'<th>Hit rate</th><th>Learning</th></tr>{srows}</table></div>')
    else:
        stable = ""
    note = "" if backend == "supabase" else '<div class="cap" style="margin-top:8px">Stored in a local file (Supabase not configured) — history resets if the server restarts.</div>'
    return f"""<div class="panel">{section_label("Track record", "स्मृति", "Smriti")}<div class="cap" style="margin-top:4px">Past hypotheses and what actually happened.</div>{note}
<div style="margin-top:14px">{table}</div>
<div style="margin-top:28px">{section_label("Pattern stats", small=True)}</div>
<div class="cap" style="margin-top:4px">Confidence for a pattern is adjusted (max ±10) only after 5 resolved predictions with that pattern and industry.</div>
<div style="margin-top:10px">{stable or '<div class="empty">No patterns yet.</div>'}</div></div>"""


# ------------------------------------------------------------------ results layout (summary / tabs / actions)
BANDS = [("Low", 0, 50, "#5A2A33"), ("Moderate", 50, 75, "#6B5320"), ("High", 75, 100, "#1E5A3C")]


def spacer(px: int = 32) -> str:
    return f'<div style="height:{px}px"></div>'


def label(text: str, sanskrit: str = "") -> str:
    sk = f'<span class="sk">{esc(sanskrit)}</span>' if sanskrit else ""
    return f'<div class="label">{esc(text)}{sk}</div>'


def _next_band_line(score: float, name: str) -> str:
    if name == "Low":
        return f"Low — {50 - score:.1f} points from Moderate"
    if name == "Moderate":
        return f"Moderate — {75 - score:.1f} points from High"
    return "High — top band"


def key_facts(d: Dict[str, Any]) -> List[str]:
    sup, con = d["supporting"], d["contradicting"]
    first_party = sum(1 for e in sup if e["source_type"] == "Primary")
    streams = len({e["stream"] for e in sup})
    return [f"<b>{len(sup)}</b> supporting sources", f"<b>{first_party}</b> first-party",
            f"<b>{len(con)}</b> contradictions", f"<b>{streams}/4</b> streams",
            f"<b>{len(d.get('adversarial_queries', []))}</b> counter-searches"]


def summary_html(d: Dict[str, Any]) -> str:
    c = d["confidence"]
    score = c["score"]
    segs = "".join(f'<i style="width:{hi - lo}%;background:{col}"></i>' for _, lo, hi, col in BANDS)
    marks = "".join(f'<span style="width:{hi - lo}%">{n}</span>' for n, lo, hi, _ in BANDS)
    facts = "".join(f"<span>{f}</span>" for f in key_facts(d))
    return f"""<div class="sum"><div class="l">{section_label("Hypothesis — not fact", "अनुमान", "Anumana")}
<div class="h1" style="margin-top:10px">{esc(d['hypothesis'])}</div></div>
<div class="r">{label("Confidence")}<div class="big">{score:g}<small>%</small></div>
<div class="scale-wrap"><div class="scale">{segs}</div><span class="mk" style="left:calc({min(score, 100):g}% - 1px)"></span></div>
<div class="scale-l">{marks}</div>
<div class="p2" style="margin-top:10px;font-size:15px">{esc(_next_band_line(score, c['label']))}</div>
<div class="cap">computed from evidence, not the model’s guess</div></div></div>
<div class="facts">{facts}</div>"""


def evidence_tab_html(d: Dict[str, Any]) -> str:
    sup = "".join(evidence_card(e, "sup") for e in d["supporting"]) or '<div class="empty">No supporting evidence.</div>'
    con = "".join(evidence_card(e, "con") for e in d["contradicting"]) or         '<div class="empty">The counter-search found nothing that contradicts the hypothesis.</div>'
    ctx = f'<div class="p2" style="margin-bottom:24px">{esc(d["executive_summary"])}</div>' if d.get("executive_summary") else ""
    return f"""{ctx}<div class="row2"><div class="col">{section_label("Supporting evidence", "प्रमाण", "Pramana")}<div class="cap" style="margin-top:4px">{len(d['supporting'])} item{'' if len(d['supporting']) == 1 else 's'}</div>{sup}</div>
<div class="col">{section_label("Contradicting evidence")}<div class="cap" style="margin-top:4px">{len(d['contradicting'])} item{'' if len(d['contradicting']) == 1 else 's'}</div>{con}</div></div>"""


def selfchallenge_html(d: Dict[str, Any]) -> str:
    qs = d.get("adversarial_queries", [])
    adv = d.get("adversarial_results", [])
    con_urls = {e["url"] for e in d["contradicting"]}
    flagged = sum(1 for a in adv if a["url"] in con_urls)
    head = (f'<div class="p2"><b style="color:var(--cream)">{len(qs)}</b> counter-searches · '
            f'<b style="color:var(--cream)">{len(adv)}</b> results retrieved · '
            f'<b style="color:var(--cream)">{flagged}</b> judged to contradict the hypothesis</div>')
    qrows = "".join(f'<div class="qrow"><span class="qt">QUERY {i}</span><span class="qq">{esc(q)}</span></div>' for i, q in enumerate(qs, 1))         or '<div class="empty">No counter-search queries were recorded.</div>'
    rrows = "".join(
        f'<div class="qrow"><span class="qt"><i class="outc" style="background:{"#EE6A5C" if a["url"] in con_urls else "#59618F"}"></i>'
        f'{"contradicts" if a["url"] in con_urls else "neutral"}</span><span class="qq">{link(a["url"], a["title"] or _domain(a["url"]))}</span></div>'
        for a in adv) or '<div class="empty">The counter-search returned no results, so the hypothesis was not meaningfully tested.</div>'
    alt = f'<div class="why"><div class="k">Alternative explanation</div><p>{esc(d["alternative_explanation"])}</p></div>' if d.get("alternative_explanation") else ""
    return f"""{section_label("Self-challenge · how it tried to prove itself wrong", "पूर्वपक्ष", "Purva Paksha")}
<div style="margin-top:12px">{head}</div><div class="cap" style="margin-top:6px">Per-query outcomes are not tracked; results below are all counter-search results.</div>
<div class="stitle" style="font-size:15px;margin-top:24px">Queries run</div>{qrows}
<div class="stitle" style="font-size:15px;margin-top:24px">Counter-search results</div>{rrows}{alt}"""


def watch_next_html(d: Dict[str, Any]) -> str:
    items = "".join(f'<div class="watch"><b>{i}</b><span>{esc(r)}</span></div>' for i, r in enumerate(d["recommendations"], 1))
    return f'{section_label("Watch next")}{items}'


def under_hood_html(d: Dict[str, Any], sd: Dict[str, Any]) -> str:
    m = d["meta"]
    rows = [("Model", m["model"]), ("Nebius calls succeeded", m.get("nebius_calls_ok", 0)),
            ("Tavily stream searches", sd.get("tavily_calls_ok", 0)), ("Tavily counter-searches", m.get("tavily_adversarial_ok", 0)),
            ("Sources retrieved", sum(len(s.get("results", [])) for s in sd["raw_streams"])),
            ("Snapshot store", sd.get("storage_backend", "—")), ("Industry label", d.get("industry", "—")),
            ("Pattern", " + ".join(d.get("pattern_signature", [])) or "—")]
    trs = "".join(f'<tr><td>{esc(k)}</td><td class="mono">{esc(v)}</td></tr>' for k, v in rows)
    return f'<table class="tt" style="min-width:0">{trs}</table>'


def footer_html() -> str:
    tip = "Nyaya is a school of classical Indian logic."
    return (f'<div class="foot"><span class="info" title="{esc(tip)}">i</span>'
            'Section names come from Nyaya, classical Indian logic, which required arguing against your own position '
            '(Purva Paksha) before reaching a verdict (Nirnaya).</div>')
