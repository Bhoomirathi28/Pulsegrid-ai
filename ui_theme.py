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

from ai_engine import SOURCE_WEIGHT, _age_days

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
  --bg:#1B2246; --line:#323C6E; --line2:#3E487C; --inset:rgba(11,16,38,0.35);
  --panel:var(--inset); --panel2:var(--inset); --inner:var(--inset);
  --cream:#F3EBDD; --text2:#C9C6D6; --muted:#A3A9C8; --foot:#9AA0C2; --turm:#E9A93B; --turm2:#F3C77A;
  --green:#5CC489; --green-t:#7FD8A4; --green-bg:rgba(92,196,137,.08); --green-b:rgba(92,196,137,.28); --green-badge:rgba(92,196,137,.18);
  --red:#EE6A5C; --red-t:#FF9B8F; --red-bg:rgba(238,106,92,.08); --red-b:rgba(238,106,92,.28); --red-badge:rgba(238,106,92,.18); --dot:#5C66A0;
  --log-t:#5DCAA5; --log-n:#AFA9EC; --log-p:#E9A93B;
}
header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"],
[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important;}
.stApp{background:var(--bg);color:var(--cream);font-family:'Mukta',sans-serif;}
.block-container{max-width:1080px !important; padding:30px 5% 64px !important;}
[data-testid="stVerticalBlock"]{gap:20px;}
h1,h2,h3,.raj{font-family:'Rajdhani',sans-serif;}
.mono{font-family:'JetBrains Mono',monospace;}
.pg-strip{position:fixed;top:0;left:0;right:0;height:6px;z-index:999990;pointer-events:none;opacity:.55;
  background-image:radial-gradient(#E9A93B 1.3px, transparent 1.6px);background-size:14px 6px;}

/* shared header */
.brand{display:flex;align-items:center;gap:12px;}
.brand .t{font:700 24px 'Rajdhani',sans-serif;color:var(--cream);line-height:1;letter-spacing:.02em;}
.hair{border-bottom:1px solid var(--line);margin-top:-6px;}
.tracker{display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;gap:8px 10px;font:600 13px 'Rajdhani',sans-serif;letter-spacing:.14em;text-transform:uppercase;}
.tracker .done{color:var(--green-t);} .tracker .cur{color:var(--turm);} .tracker .up{color:var(--muted);opacity:.75;}
.tracker .dash{display:inline-block;width:22px;height:1px;background:var(--line2);}
@media (max-width:640px){.tracker{justify-content:flex-start;font-size:12px;letter-spacing:.1em;} .tracker .dash{width:10px;}}

/* buttons */
.stButton button, [data-testid="stDownloadButton"] button, [data-testid="stFormSubmitButton"] button{
  min-height:52px;border-radius:8px;font:700 15px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;transition:background .15s,border-color .15s,color .15s;}
.stButton button p, [data-testid="stDownloadButton"] button p, [data-testid="stFormSubmitButton"] button p{font:inherit !important;letter-spacing:inherit;color:inherit;}
button[data-testid^="stBaseButton-primary"]{background:var(--turm) !important;color:#1A1206 !important;border:1px solid var(--turm) !important;}
button[data-testid^="stBaseButton-primary"]:hover{background:var(--turm2) !important;border-color:var(--turm2) !important;}
button[data-testid^="stBaseButton-primary"]:disabled{opacity:.45;}
button[data-testid^="stBaseButton-secondary"]{background:transparent !important;color:var(--cream) !important;border:1px solid var(--line2) !important;}
button[data-testid^="stBaseButton-secondary"]:hover{border-color:var(--turm) !important;color:var(--turm2) !important;}
button[data-testid="stBaseButton-tertiary"]{background:transparent !important;border:0 !important;color:var(--muted) !important;min-height:40px;padding:4px 2px !important;}
button[data-testid="stBaseButton-tertiary"]:hover{color:var(--turm2) !important;}
.turm-outline button{border-color:var(--turm) !important;color:var(--turm) !important;}
[class*="st-key-nav_"] button{min-height:34px !important;border-radius:0 !important;border-bottom:2px solid transparent !important;font-size:14px !important;}
[class*="st-key-chip_"] button{min-height:34px !important;padding:2px 14px !important;border-radius:999px !important;font:400 13px 'JetBrains Mono',monospace !important;text-transform:none;letter-spacing:0;}
[class*="st-key-chip_"] button p{font:inherit !important;}
[data-testid="stForm"]{border:0 !important;padding:0 !important;}

/* inputs */
[data-testid="stTextInput"] label p{font:600 12px 'Rajdhani',sans-serif !important;letter-spacing:.14em;text-transform:uppercase;color:var(--muted) !important;}
[data-testid="stTextInput"] input{height:52px;background:transparent !important;border:0 !important;color:var(--cream) !important;font-family:'JetBrains Mono',monospace !important;font-size:15px !important;}
[data-testid="stTextInputRootElement"],[data-baseweb="input"],[data-baseweb="base-input"]{background:var(--inset) !important;border:1px solid var(--line2) !important;border-radius:8px !important;}
[data-baseweb="input"]:focus-within{border-color:var(--turm) !important;}
[data-testid="stTextInput"] input::placeholder{color:var(--muted) !important;opacity:.75;}
[data-testid="InputInstructions"]{display:none;}

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

/* thinking */
.mono-sm{font:400 13px 'JetBrains Mono',monospace;color:var(--muted);}
.h1t{font:700 clamp(30px,4.4vw,44px)/1.1 'Rajdhani',sans-serif;color:var(--cream);margin:10px 0 10px;}
.stages2{margin-top:24px;border-top:1px solid var(--line);}
.srow{display:flex;gap:14px;align-items:flex-start;padding:13px 0;border-bottom:1px solid var(--line);}
.sdot{flex:0 0 10px;height:10px;margin-top:6px;border-radius:50%;background:var(--dot);}
.sdot.done{background:var(--green);} .sdot.running{background:var(--turm);animation:pulse 1.4s ease-in-out infinite;} .sdot.failed{background:var(--red);}
.srow .sb{flex:1 1 auto;min-width:0;}
.srow .sn{font:600 15px 'Rajdhani',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--cream);}
.srow .sd{font:400 12px 'JetBrains Mono',monospace;color:var(--muted);margin-top:4px;}
.srow .ss{flex:0 0 auto;font:500 11px 'JetBrains Mono',monospace;letter-spacing:.08em;color:var(--muted);margin-top:4px;}
.ss.done{color:var(--green-t);} .ss.running{color:var(--turm);} .ss.failed{color:var(--red-t);}
.legend{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;font-size:13px;color:var(--muted);margin-top:14px;}
.legend b{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle;}
.st-key-see_results button{min-height:60px !important;font-size:17px !important;}
@media (max-width:640px){.srow .sn .sk{display:block;margin-left:0;}}

/* investigate */
.st-key-inv_col{max-width:860px;margin:24px auto 0;}
.istatus{font:400 13px 'JetBrains Mono',monospace;color:var(--green-t);} .istatus.bad{color:var(--red-t);}
.ih1{font:700 clamp(34px,5.6vw,54px)/1.08 'Rajdhani',sans-serif;color:var(--cream);margin:18px 0 14px;}
.st-key-inv_col [data-testid="stTextInput"] input{height:56px;font-size:16px !important;}
.st-key-inv_col [data-testid="stFormSubmitButton"] button{min-height:58px;}
.try{font:400 13px 'JetBrains Mono',monospace;color:var(--muted);}
.pillars{display:flex;gap:32px;flex-wrap:wrap;} .pillar{flex:1 1 220px;min-width:0;}
.pillar .pt{font-size:14px;line-height:1.55;color:var(--muted);margin-top:8px;}

/* actions */
.rcards{display:flex;gap:20px;flex-wrap:wrap;margin-top:8px;}
.rcard{flex:1 1 260px;min-width:0;border:1px solid var(--line);border-radius:8px;padding:22px;background:var(--inset);}
.rcard .rn{display:inline-flex;width:30px;height:30px;border-radius:50%;border:1px solid var(--turm);color:var(--turm);align-items:center;justify-content:center;font:700 15px 'Rajdhani',sans-serif;}
.rcard .rt{font:600 22px/1.2 'Rajdhani',sans-serif;color:var(--cream);margin-top:14px;}
.rcard .rw{font-size:15px;line-height:1.55;color:var(--text2);margin-top:8px;}
.rcard .rr{font:400 12px 'JetBrains Mono',monospace;color:var(--muted);margin-top:16px;padding-top:12px;border-top:1px solid var(--line);}
.arows{margin-top:10px;border-top:1px solid var(--line);}
.arow{display:flex;gap:14px;padding:13px 0;border-bottom:1px solid var(--line);}
.arow .am{flex:0 0 16px;font:600 15px 'JetBrains Mono',monospace;} .am.ok{color:var(--green-t);} .am.fail{color:var(--red-t);} .am.none{color:var(--muted);}
.arow .al{font:600 14px 'Rajdhani',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:var(--cream);}
.arow .at{font:400 12px 'JetBrains Mono',monospace;color:var(--muted);margin-top:4px;word-break:break-word;}
.st-key-dl_report button{border-color:var(--turm) !important;color:var(--turm) !important;}

/* results */
.lab{font:600 13px 'Rajdhani',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);}
.lab.turm{color:var(--turm);} .lab.green{color:var(--green-t);} .lab.red{color:var(--red-t);}
.rstatus{display:flex;gap:8px 10px;flex-wrap:wrap;font:400 13px 'JetBrains Mono',monospace;color:var(--muted);}
.rstatus .live{color:var(--green-t);} .rstatus .sim{font-size:12px;padding:2px 8px;}
.hero5{display:flex;gap:48px;flex-wrap:wrap;align-items:flex-start;}
.hero5 .l{flex:3 1 440px;min-width:0;} .hero5 .r{flex:2 1 300px;min-width:0;}
.hyp{font:600 clamp(26px,4vw,42px)/1.15 'Rajdhani',sans-serif;color:var(--cream);margin:12px 0 18px;}
.facts5{font:400 13px 'JetBrains Mono',monospace;color:var(--text2);} .facts5 b{color:var(--cream);font-weight:500;}
.bignum{font:600 88px/1 'Rajdhani',sans-serif;color:var(--cream);margin-top:6px;} .bignum small{font-size:36px;color:var(--muted);margin-left:2px;}
.scale5{position:relative;margin-top:16px;} .scale5 .segs{display:flex;gap:3px;}
.scale5 .segs i{display:block;height:4px;border-radius:2px;background:var(--line2);} .scale5 .segs i.on{background:rgba(233,169,59,.45);}
.scale5 .mk{position:absolute;top:-6px;width:3px;height:16px;border-radius:2px;background:var(--turm);}
.names5{display:flex;gap:3px;margin-top:8px;font:600 11px 'Rajdhani',sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);}
.names5 span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;} .names5 .on{color:var(--turm);}
.bandline{font:600 17px 'Rajdhani',sans-serif;letter-spacing:.04em;color:var(--turm);margin-top:14px;}
.cols2{display:flex;gap:48px;flex-wrap:wrap;align-items:flex-start;} .cols2 > .col{flex:1 1 340px;min-width:0;}
.erows{margin-top:10px;border-top:1px solid var(--line);}
.erow{display:flex;gap:14px;align-items:flex-start;padding:14px 0;border-bottom:1px solid var(--line);}
.erow .mark{flex:0 0 6px;height:6px;margin-top:9px;border-radius:50%;background:var(--green);}
.erow.con .mark{border-radius:1px;background:var(--red);transform:rotate(45deg);}
.erow .eb{flex:1 1 auto;min-width:0;} .erow .ec{font-size:15px;line-height:1.5;color:var(--cream);}
.erow .em{font:400 12px 'JetBrains Mono',monospace;color:var(--muted);margin-top:6px;}
.erow .ew{flex:0 0 auto;font:500 12px 'JetBrains Mono',monospace;color:var(--green-t);margin-top:3px;}
.erow.con .ew{color:var(--red-t);}
.pills{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}
.pill5{font:600 12px 'Rajdhani',sans-serif;letter-spacing:.12em;text-transform:uppercase;padding:4px 10px;border-radius:999px;border:1px solid var(--turm);color:var(--turm);}
.pill5.off{border-color:var(--line2);color:var(--muted);opacity:.6;}
.inset{background:var(--inset);border:1px solid var(--line);border-radius:8px;padding:18px 20px;}
.inset p{margin:8px 0 0;color:var(--text2);line-height:1.6;font-size:15px;}
.fac .bar i{background:var(--turm);}
.ul{margin:10px 0 0;padding-left:18px;color:var(--text2);font-size:14px;line-height:1.6;} .ul li{margin-top:6px;}
.qblock{margin-bottom:22px;} .qhead{display:flex;gap:8px 14px;flex-wrap:wrap;align-items:baseline;padding-bottom:8px;border-bottom:1px solid var(--line);}
.qhead .qn{font:600 13px 'Rajdhani',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--turm);}
.qhead .qq{flex:1 1 240px;font:400 13px 'JetBrains Mono',monospace;color:var(--cream);}
.qhead .qc{font:400 12px 'JetBrains Mono',monospace;color:var(--muted);}
.log{background:var(--inset);border:1px solid var(--line);border-radius:8px;padding:14px 16px;font:400 12px/1.7 'JetBrains Mono',monospace;color:var(--text2);max-height:300px;overflow-y:auto;}
.ll{display:flex;gap:10px;} .ll .lt{color:var(--muted);flex:0 0 auto;} .ll .lk{flex:0 0 72px;} .ll .lx{min-width:0;word-break:break-word;}
@media (max-width:640px){.bignum{font-size:68px;} .names5{font-size:9px;letter-spacing:0;} .hero5,.cols2{gap:32px;}}

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


LOGO_SM = """<svg width="30" height="30" viewBox="0 0 40 40" aria-hidden="true">
<polygon points="20,3 37,20 20,37 3,20" fill="none" stroke="#E9A93B" stroke-width="2"/>
<g fill="#F3EBDD"><circle cx="12" cy="12" r="2.2"/><circle cx="28" cy="12" r="2.2"/><circle cx="12" cy="28" r="2.2"/><circle cx="28" cy="28" r="2.2"/></g>
<circle cx="20" cy="20" r="3.4" fill="#E9A93B"/></svg>"""

STEPS = ["Investigate", "Thinking", "Results", "Actions"]


def strip_html() -> str:
    return '<div class="pg-strip"></div>'


def screen_css(dotted: bool, active_nav: str = "") -> str:
    """Per-screen CSS: faint kolam dot grid on some screens, turmeric underline on the active nav item."""
    css = ""
    if dotted:
        css += (".stApp{background-image:radial-gradient(rgba(243,235,221,0.06) 1.2px, transparent 1.4px);"
                "background-size:28px 28px;}")
    if active_nav:
        css += (f".st-key-nav_{active_nav} button{{color:var(--cream) !important;"
                "border-bottom-color:var(--turm) !important;}")
    return f"<style>{css}</style>"


def brand_html() -> str:
    return f'<div class="brand">{LOGO_SM}<span class="t">PulseGrid AI</span></div>'


def tracker_html(current: int) -> str:
    """Step tracker: 0 Investigate · 1 Thinking · 2 Results · 3 Actions."""
    parts = []
    for i, name in enumerate(STEPS):
        if i < current:
            parts.append(f'<span class="done">✓ {name}</span>')
        elif i == current:
            parts.append(f'<span class="cur">● {name}</span>')
        else:
            parts.append(f'<span class="up">{name}</span>')
    return '<div class="tracker">' + '<span class="dash"></span>'.join(parts) + "</div>"


def hair_html() -> str:
    return '<div class="hair"></div>'


# ------------------------------------------------------------------ screen 2: investigate
def investigate_top_html(tavily_ok: bool, nebius_ok: bool, model: str, simulated: bool) -> str:
    if simulated:
        status = '<div class="istatus bad">● SIMULATED · DEMO_SIMULATION=true — no live calls are made</div>'
    elif tavily_ok and nebius_ok:
        status = f'<div class="istatus">● LIVE · Tavily ready · {esc(model)} on Nebius ready</div>'
    else:
        t = "Tavily ready" if tavily_ok else "Tavily not configured"
        n = f"{esc(model)} on Nebius ready" if nebius_ok else "Nebius not configured"
        status = f'<div class="istatus bad">● NOT CONFIGURED · {t} · {n}</div>'
    return f"""{status}<div class="ih1">Name a company.<br>Watch the agent argue with itself.</div>
<div class="p2">Four agents search the live web, one hypothesis forms, then PulseGrid tries to prove itself wrong before it gives you a verdict.</div>"""


PILLARS = [("Four live streams", "Hiring, product and pricing, customer friction and market news, searched in parallel with Tavily."),
           ("Argues against itself", "Nemotron forms one hypothesis, then searches the web for evidence that it is wrong."),
           ("Score you can check", "Confidence is computed in Python from weighted evidence, and every factor is shown.")]


def pillars_html() -> str:
    cols = "".join(f'<div class="pillar"><div class="lab turm">{esc(t)}</div><div class="pt">{esc(x)}</div></div>' for t, x in PILLARS)
    return f'<div class="hair" style="margin:8px 0 28px"></div><div class="pillars">{cols}</div>'


# ------------------------------------------------------------------ screen 3: thinking
# (English name, Devanagari, roman, detail template shown until real numbers arrive)
STAGES = [("Search the live web", "गुप्तचर", "Guptachar", "4 parallel Tavily streams · — sources"),
          ("Sort evidence", "प्रमाण", "Pramana", "Official — · News — · Community — · weighted"),
          ("Form hypothesis", "अनुमान", "Anumana", "Nemotron cited — evidence items"),
          ("Challenge hypothesis", "पूर्वपक्ष", "Purva Paksha", "— counter-searches · — results · — contradict"),
          ("Verdict", "निर्णय", "Nirnaya", "Score computed in Python · — · —"),
          ("Save and alert", "", "", "Prediction — · baseline — · alert check —")]

_GRID = [(60 + 70 * i, 60 + 70 * j) for j in range(5) for i in range(5) if (i, j) != (2, 2)]


def _ring_order():
    def key(p):
        dx, dy = (p[0] - 200) / 70, (p[1] - 200) / 70
        return (max(abs(dx), abs(dy)), math.atan2(dy, dx))
    return sorted(_GRID, key=key)


def _polar(deg: float, r: float):
    t = math.radians(deg)
    return 200 + r * math.cos(t), 200 + r * math.sin(t)


def kolam_svg(n_sup: int, n_con: int, stages_done: int, running: bool) -> str:
    """Green dots = supporting items, red diamonds = contradicting items, one turmeric loop per finished stage.
    All counts are real; the dot positions and loop shapes are decorative."""
    order = _ring_order()
    n_sup = max(0, min(n_sup, len(order)))
    n_con = max(0, min(n_con, len(order) - n_sup))
    loops = []
    for k in range(min(stages_done, 6)):
        ang = -90 + k * 60
        (x1, y1), (x2, y2) = _polar(ang - 38, 190), _polar(ang + 38, 190)
        cls = ' class="draw"' if k == stages_done - 1 else ""
        loops.append(f'<path pathLength="1"{cls} d="M200,200 C{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} 200,200" fill="none" '
                     f'stroke="#E9A93B" stroke-width="2.2" stroke-linecap="round"/>')
    dots = []
    for idx, (x, y) in enumerate(order):
        if idx < n_sup:
            dots.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="#5CC489"/>')
        elif idx < n_sup + n_con:
            dots.append(f'<rect x="{x - 5.5}" y="{y - 5.5}" width="11" height="11" fill="#EE6A5C" transform="rotate(45 {x} {y})"/>')
        else:
            dots.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#5C66A0"/>')
    pulse = ' class="pulse"' if running else ""
    centre = f'<circle{pulse} cx="200" cy="200" r="9" fill="#E9A93B"/>'
    return f"""<svg viewBox="0 0 400 400" width="100%" style="max-width:400px;display:block;margin:0 auto" role="img" aria-label="Kolam: {n_sup} supporting signals, {n_con} counter-evidence, {stages_done} of 6 stages done">
<polygon points="200,30 370,200 200,370 30,200" fill="none" stroke="#F3EBDD" stroke-opacity=".14" stroke-dasharray="4 6"/>
<circle cx="200" cy="200" r="150" fill="none" stroke="#F3EBDD" stroke-opacity=".14" stroke-dasharray="4 6"/>
{''.join(loops)}{''.join(dots)}{centre}</svg>"""


def kolam_panel_html(run: Dict[str, Any]) -> str:
    done = sum(1 for s in run["stages"] if s["status"] == "DONE")
    running = not run["done"] and not run["error"]
    return f"""{kolam_svg(run.get("sup", 0), run.get("con", 0), done, running)}
<div class="legend"><span><b style="background:#5CC489"></b>supporting signal</span>
<span><b style="background:#EE6A5C;border-radius:1px;transform:rotate(45deg)"></b>counter-evidence</span>
<span><b style="background:#5C66A0"></b>no signal</span></div>"""


def thinking_left_html(run: Dict[str, Any]) -> str:
    if run["error"]:
        title = "The run stopped."
        sub = "A live call failed. Nothing below was faked; the failed step is marked in red."
    elif run["done"]:
        title = "The pattern is complete."
        sub = "Every number below came from a real call. The verdict is ready."
    else:
        title = "The pattern is being drawn."
        sub = "Four agents search the live web, a hypothesis forms, then PulseGrid tries to prove itself wrong."
    rows = []
    for (en, dv, rm, _), stg in zip(STAGES, run["stages"]):
        sk = f'<span class="sk">{esc(dv)} {esc(rm)}</span>' if dv else ""
        cls = stg["status"].lower()
        rows.append(f'<div class="srow"><span class="sdot {cls}"></span><div class="sb"><div class="sn">{esc(en)}{sk}</div>'
                    f'<div class="sd">{esc(stg["detail"])}</div></div><span class="ss {cls}">{esc(stg["status"])}</span></div>')
    log = "".join(_log_line(e) for e in run["events"]) or '<div class="ll"><span class="lx">waiting for the first result…</span></div>'
    return f"""<div class="mono-sm">Investigating · {esc(run["company"])}</div>
<div class="h1t">{title}</div><div class="p2">{sub}</div>
<div class="stages2">{''.join(rows)}</div>
<div class="lab" style="margin-top:28px">Activity log</div><div class="log" style="margin-top:10px">{log}</div>"""


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


# ------------------------------------------------------------------ screen 4: results
# Display bands for the score. The score itself is computed in ai_engine.compute_confidence.
BANDS5 = [("Unsupported", 0, 25), ("Speculative", 25, 45), ("Plausible", 45, 65), ("Likely", 65, 85), ("Confirmed", 85, 100)]
CHECKS = ["Cuts", "Statements", "Alternative", "Absence", "Timing"]
SOURCE_NAME = {"Primary": "Official", "Secondary": "News", "Community": "Community"}


def band5(score: float):
    """(band, next band or None, points to next band or None)."""
    for i, (name, _, hi) in enumerate(BANDS5):
        if score < hi or i == len(BANDS5) - 1:
            if i + 1 < len(BANDS5):
                nxt = BANDS5[i + 1]
                return name, nxt[0], round(nxt[1] - score, 1)
            return name, None, None


def band_line(score: float) -> str:
    name, nxt, pts = band5(score)
    return f"{name} — {pts:g} points from {nxt}" if nxt else f"{name} — top band"


def checks_run(d: Dict[str, Any]) -> List[str]:
    """Only checks the pipeline really performed. It asks for an alternative explanation;
    the other four check types are not part of the pipeline, so they show as not checked."""
    return ["Alternative"] if d.get("alternative_explanation") else []


def age_text(published: Any) -> str:
    days = _age_days(published)
    if days is None or days < 0:
        return "—"
    if days < 1:
        return "today"
    return f"{int(days)}d ago" if days < 60 else f"{int(days // 30)}mo ago"


def results_status_html(d: Dict[str, Any], sd: Dict[str, Any], scan_n: Optional[int]) -> str:
    if sd["diff"].get("first_scan"):
        cmp_txt = "first scan — baseline saved"
    else:
        cmp_txt = f"scan #{scan_n} vs baseline" if scan_n else "scan #— vs baseline"
    live = ('<span class="sim">SIMULATED</span>' if d.get("simulated")
            else f'<span class="live">● live {esc(d["meta"]["model"])}</span>')
    return f'<div class="rstatus"><span>{esc(d.get("company"))}</span><span>·</span><span>{esc(cmp_txt)}</span><span>·</span>{live}</div>'


def hero_html(d: Dict[str, Any]) -> str:
    c = d["confidence"]
    score = c["score"]
    sup, con = d["supporting"], d["contradicting"]
    official = sum(1 for e in sup if e["source_type"] == "Primary")
    streams = len({e["stream"] for e in sup})
    facts = [f"<b>{len(sup)}</b> supporting", f"<b>{official}</b> official", f"<b>{len(con)}</b> against",
             f"<b>{streams}/4</b> streams", f"<b>{len(checks_run(d))}/5</b> checks run"]
    name = band5(score)[0]
    segs = "".join(f'<i class="{"on" if n == name else ""}" style="width:{hi - lo}%"></i>' for n, lo, hi in BANDS5)
    names = "".join(f'<span class="{"on" if n == name else ""}" style="width:{hi - lo}%">{n}</span>' for n, lo, hi in BANDS5)
    return f"""<div class="hero5"><div class="l">
<div class="lab turm">Hypothesis — not fact<span class="sk">अनुमान Anumana</span></div>
<div class="hyp">{esc(d['hypothesis'])}</div>
<div class="facts5">{' · '.join(facts)}</div></div>
<div class="r"><div class="lab">Confidence</div><div class="bignum">{score:g}<small>%</small></div>
<div class="scale5"><div class="segs">{segs}</div><span class="mk" style="left:calc({min(score, 100):g}% - 1.5px)"></span></div>
<div class="names5">{names}</div>
<div class="bandline">{esc(band_line(score))}</div>
<div class="cap">computed from weighted evidence, not the model’s guess</div></div></div>"""


def _ev_row(e: Dict[str, Any], kind: str) -> str:
    w = SOURCE_WEIGHT.get(e["source_type"], 0.7)
    meta = f'{SOURCE_NAME.get(e["source_type"], "News")} · {esc(age_text(e.get("published_date")))} · {link(e["url"], _domain(e["url"]))}'
    return (f'<div class="erow {kind}"><span class="mark"></span><div class="eb"><div class="ec">{esc(e["claim"] or e["title"])}</div>'
            f'<div class="em">{meta}</div></div><span class="ew">w {w:.2f}</span></div>')


def evidence_columns_html(d: Dict[str, Any]) -> str:
    sup, con = d["supporting"], d["contradicting"]
    s_rows = "".join(_ev_row(e, "sup") for e in sup) or '<div class="empty">No supporting evidence.</div>'
    c_rows = "".join(_ev_row(e, "con") for e in con) or \
        '<div class="empty">The counter-search found nothing that contradicts the hypothesis.</div>'
    done = checks_run(d)
    pills = "".join(f'<span class="pill5{"" if c in done else " off"}">{c}{"" if c in done else " · not checked"}</span>' for c in CHECKS)
    n_q = len(d.get("adversarial_queries", []))
    return f"""<div class="cols2"><div class="col">
<div class="lab green">Supporting evidence · {len(sup)}<span class="sk">प्रमाण Pramana</span></div><div class="erows">{s_rows}</div></div>
<div class="col"><div class="lab red">Opposing evidence · {len(con)}<span class="sk">पूर्वपक्ष Purva Paksha</span></div><div class="erows">{c_rows}</div>
<div class="lab" style="margin-top:28px">Checks run · {len(done)} of 5</div><div class="pills">{pills}</div>
<div class="cap" style="margin-top:8px">Plus {n_q} counter-search{"" if n_q == 1 else "es"} on the live web — see the self-challenge log.</div></div></div>"""


def why_html(d: Dict[str, Any]) -> str:
    text = d.get("why_not_higher") or "—"
    return f'<div class="inset"><div class="lab turm">Why not higher?</div><p>{esc(text)}</p></div>'


def score_tab_html(d: Dict[str, Any]) -> str:
    c = d["confidence"]
    rows = []
    for b in c["breakdown"]:
        w = max(0, min(100, b["value"] * 100))
        rows.append(f'<div class="fac"><div class="top"><span>{esc(b["label"])} <i class="cap">· weight {b["weight"] * 100:.0f}%</i></span>'
                    f'<span>+{b["points"]:.1f}</span></div><div class="bar"><i style="width:{w:.0f}%"></i></div>'
                    f'<div class="cap" style="margin-top:4px">{esc(b["note"])}</div></div>')
    caps = "".join(f'<div class="warn">{esc(x)}</div>' for x in c["caps"])
    h = c.get("history")
    if h:
        base = f' · evidence score before adjustment {c["base_score"]:g}%' if h.get("adjustment") else ""
        caps += f'<div class="cap" style="margin-top:14px">Track record · {esc(h["message"])}{esc(base)}</div>'
    # "raise" = factors with the most unclaimed points; "lower" = how the formula penalises
    head = sorted(c["breakdown"], key=lambda b: -(b["weight"] * 100 - b["points"]))
    raise_ = [f'{esc(b["label"])}: up to +{b["weight"] * 100 - b["points"]:.1f} points available ({esc(b["note"])})'
              for b in head if b["weight"] * 100 - b["points"] >= 0.5][:3]
    if any("Capped at 60" in x for x in c["caps"]):
        raise_.append("A counter-search that returns results would remove the cap at 60.")
    lower = ["Contradicting evidence lowers the weighted support share (35% of the score); official sources count most (1.0).",
             "Older or undated supporting sources lower recency (15%).",
             "If the counter-search returns nothing, the score is capped at 60.",
             "After 5 resolved predictions with the same pattern, the track record can move it by up to ±10."]
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs) or "<li>—</li>"
    return f"""{''.join(rows)}{caps}<div class="cols2" style="margin-top:28px">
<div class="col"><div class="lab green">What would raise this</div><ul class="ul">{li(raise_)}</ul></div>
<div class="col"><div class="lab red">What would lower this</div><ul class="ul">{li(lower)}</ul></div></div>"""


def selfchallenge_log_html(d: Dict[str, Any]) -> str:
    con_ids = {e["id"] for e in d["contradicting"]}
    by_id = {a["id"]: a for a in d.get("adversarial_results", [])}
    blocks = []
    for i, q in enumerate(d.get("adversarial_log", []), 1):
        n_con = sum(1 for x in q["ids"] if x in con_ids)
        items = "".join(
            f'<div class="qrow"><span class="qt" style="color:{"#FF9B8F" if x in con_ids else "#A3A9C8"}">'
            f'{"contradicts" if x in con_ids else "neutral"}</span><span class="qq">{link(by_id[x]["url"], by_id[x]["title"] or _domain(by_id[x]["url"]))}</span></div>'
            for x in q["ids"] if x in by_id) or '<div class="empty">No results for this query.</div>'
        blocks.append(f'<div class="qblock"><div class="qhead"><span class="qn">Counter-search {i}</span>'
                      f'<span class="qq">{esc(q["query"])}</span><span class="qc">{q["results"]} results · {n_con} contradict</span></div>{items}</div>')
    if not blocks:
        blocks = ['<div class="empty">No counter-search was run (simulation mode, or no queries recorded).</div>']
    alt = d.get("alternative_explanation")
    alt_html = f'<div class="inset" style="margin-top:24px"><div class="lab turm">Alternative explanation</div><p>{esc(alt)}</p></div>' if alt else ""
    return "".join(blocks) + alt_html


def changes_html(sd: Dict[str, Any]) -> str:
    diff = sd["diff"]
    if diff["first_scan"]:
        return '<div class="p2">First scan — baseline saved. Rescan later to see what changed. No changes are claimed.</div>'
    new = diff["new_signals"]
    body = "".join(f'<div class="qrow"><span class="qt">{esc(n["category"])}</span><span class="qq">{link(n["url"], n["title"])}</span></div>'
                   for n in new) or '<div class="empty">No new sources since the previous scan.</div>'
    return (f'<div class="cap">Matched by source URL: {len(new)} new source(s); '
            f'{diff["gone_count"]} previously seen source(s) did not appear.</div>{body}')


def sources_html(sd: Dict[str, Any]) -> str:
    out = []
    for s in sd["raw_streams"]:
        rows = "".join(
            f'<div class="qrow"><span class="qt">{SOURCE_NAME.get(it.get("provenance"), "News")}</span>'
            f'<span class="qq">{link(it.get("url", ""), it.get("title") or it.get("url", ""))}'
            f'<span class="cap"> · {esc(_domain(it.get("url", "")))}</span></span></div>' for it in s.get("results", [])) \
            or '<div class="empty">No results.</div>'
        out.append(f'<div class="lab" style="margin-top:20px">{esc(s.get("category", ""))} · {len(s.get("results", []))}</div>'
                   f'<div class="cap">query: {esc(s.get("query", ""))}</div>{rows}')
    return "".join(out)


def how_it_ran_html(d: Dict[str, Any], sd: Dict[str, Any], events: Optional[List[Dict[str, Any]]] = None) -> str:
    timeline = ""
    if events:
        timeline = '<div class="log" style="margin-bottom:24px">' + "".join(_log_line(e) for e in events) + "</div>"
    return timeline + under_hood_html(d, sd)


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
def spacer(px: int = 32) -> str:
    return f'<div style="height:{px}px"></div>'


def label(text: str, sanskrit: str = "") -> str:
    sk = f'<span class="sk">{esc(sanskrit)}</span>' if sanskrit else ""
    return f'<div class="label">{esc(text)}{sk}</div>'


# ------------------------------------------------------------------ screen 5: actions
def _stream_short(category: str) -> str:
    return str(category or "").split(" & ")[0]


def responds_to(rec: Dict[str, Any], supporting: List[Dict[str, Any]]) -> str:
    by_id = {e["id"]: e for e in supporting}
    items = [by_id[i] for i in rec.get("evidence_ids", []) if i in by_id]
    if not items:
        return "Responds to: —"
    streams = list(dict.fromkeys(_stream_short(e["stream"]) for e in items))
    return (f"Responds to: {len(items)} signal{'' if len(items) == 1 else 's'} · {', '.join(streams)} "
            f"({', '.join(e['id'] for e in items)})")


def actions_head_html(d: Dict[str, Any]) -> str:
    score = d["confidence"]["score"]
    return f"""<div class="lab turm">Recommended actions</div>
<div class="h1t">What a competitor of {esc(d.get("company"))} could do next</div>
<div class="p2" style="color:var(--muted)">Suggestions based on the evidence for a hypothesis at {score:g}% ({esc(band5(score)[0])}).
Each one shows which signals it responds to. Not certainties.</div>"""


def rec_cards_html(d: Dict[str, Any]) -> str:
    recs = d.get("recommendation_details") or [{"action": r, "why": "", "evidence_ids": [], "structured": False}
                                                for r in d.get("recommendations", [])]
    cards = []
    for i, r in enumerate(recs[:3], 1):
        why = f'<div class="rw">{esc(r["why"])}</div>' if r.get("why") else ""
        resp = f'<div class="rr">{esc(responds_to(r, d["supporting"]))}</div>' if r.get("structured") else ""
        cards.append(f'<div class="rcard"><span class="rn">{i}</span><div class="rt">{esc(r["action"])}</div>{why}{resp}</div>')
    return '<div class="rcards">' + ("".join(cards) or '<div class="empty">The model returned no recommendations.</div>') + "</div>"


def after_analysis_html(run_log: List[Dict[str, Any]]) -> str:
    marks = {"ok": ("✓", "ok"), "fail": ("✕", "fail"), "none": ("–", "none")}
    rows = "".join(
        f'<div class="arow"><span class="am {marks[r["mark"]][1]}">{marks[r["mark"]][0]}</span>'
        f'<div><div class="al">{esc(r["label"])}</div><div class="at">{esc(r["text"])}</div></div></div>' for r in run_log) \
        or '<div class="empty">—</div>'
    return f'<div class="lab">After the analysis</div><div class="arows">{rows}</div>'


def kolam_footer_html() -> str:
    return '<div class="foot">Every kolam begins with dots. Every conclusion here begins with evidence.</div>'


LOG_COLOR = {"TAVILY": "var(--log-t)", "NEMOTRON": "var(--log-n)", "PYTHON": "var(--log-p)"}


def _log_line(e: Dict[str, Any]) -> str:
    color = LOG_COLOR.get(e["kind"], "var(--muted)")
    return (f'<div class="ll"><span class="lt">{int(e["t"]) // 60:02d}:{int(e["t"]) % 60:02d}</span>'
            f'<span class="lk" style="color:{color}">{esc(e["kind"])}</span><span class="lx">{esc(e["text"])}</span></div>')


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
