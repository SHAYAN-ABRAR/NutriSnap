"""
NutriSnap design system.

Exposes design tokens (PALETTE) and a single inject_css() function that paints
the whole Streamlit shell to look like a premium, mobile-first product.
Supports light + dark + reduced-motion. System theme is set via .streamlit/config.toml;
the in-app toggle (Settings) flips this at runtime.
"""

# ----- Brand colour tokens (carried from the original NutriSnap mockup) -----
BRAND = {
    "accent":   "#00e5a0",
    "accent2":  "#00b37a",
    "protein":  "#60a5fa",
    "carbs":    "#fbbf24",
    "fat":      "#f87171",
    "fiber":    "#34d399",
    "water":    "#38bdf8",
    "warn":     "#ff6b6b",
    "gold":     "#fbbf24",
}

DARK = {
    "bg": "#0d0f14", "surface": "#161a22", "surface2": "#1e2330",
    "border": "#2a2f3d", "text": "#e8eaf0", "muted": "#8b93a7",
    "shadow": "0 8px 30px rgba(0,0,0,.45)",
}
LIGHT = {
    "bg": "#f4f6fb", "surface": "#ffffff", "surface2": "#eef1f7",
    "border": "#e2e7f0", "text": "#10131a", "muted": "#5b6477",
    "shadow": "0 8px 30px rgba(20,30,60,.10)",
}


def palette(mode: str = "dark") -> dict:
    base = DARK if mode == "dark" else LIGHT
    return {**BRAND, **base}


def inject_css(mode: str = "dark") -> str:
    """Return a <style> block tuned to the active theme."""
    p = palette(mode)
    grid = "rgba(255,255,255,.03)" if mode == "dark" else "rgba(20,30,60,.025)"
    glass = "rgba(255,255,255,.04)" if mode == "dark" else "rgba(255,255,255,.7)"
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {{
  --bg:{p['bg']}; --surface:{p['surface']}; --surface2:{p['surface2']};
  --border:{p['border']}; --text:{p['text']}; --muted:{p['muted']};
  --accent:{p['accent']}; --accent2:{p['accent2']};
  --protein:{p['protein']}; --carbs:{p['carbs']}; --fat:{p['fat']}; --fiber:{p['fiber']};
  --water:{p['water']}; --warn:{p['warn']}; --gold:{p['gold']};
  --shadow:{p['shadow']};
  --r-lg:22px; --r-md:16px; --r-sm:12px;
}}

/* ---------- App canvas ---------- */
html, body, [data-testid="stAppViewContainer"] {{
  background:
    radial-gradient(1200px 600px at 85% -10%, rgba(0,229,160,.10), transparent 60%),
    radial-gradient(900px 500px at -10% 10%, rgba(96,165,250,.08), transparent 55%),
    var(--bg) !important;
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}
/* root app shell uses the active theme bg (Streamlit's base is hardcoded dark,
   which would otherwise leak through as black in light mode) */
[data-testid="stApp"] {{ background: var(--bg) !important; }}
[data-testid="stHeader"] {{ background: transparent; }}
/* hide Streamlit's top-right chrome (status/deploy/menu) — our top bar owns that space */
[data-testid="stToolbar"], [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"] {{
  display: none !important;
}}
[data-testid="stDecoration"] {{ display:none; }}
#MainMenu, footer {{ visibility: hidden; }}

/* tighter, phone-width main column with safe-area padding.
   Top padding clears the fixed top bar; bottom padding clears the fixed nav. */
[data-testid="stMainBlockContainer"], .block-container {{
  max-width: 540px !important;
  padding: calc(64px + env(safe-area-inset-top)) 1.0rem calc(96px + env(safe-area-inset-bottom)) 1.0rem !important;
}}
h1,h2,h3,h4 {{ font-family:'Space Grotesk', sans-serif; letter-spacing:-.5px; color:var(--text); }}
p, span, label, li {{ color: var(--text); }}

/* ---------- Buttons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius: var(--r-md); border:1px solid var(--border);
  background: var(--surface2); color: var(--text);
  font-weight:600; padding:.62rem 1rem; min-height:46px;
  transition: transform .12s ease, box-shadow .18s ease, background .18s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
  transform: translateY(-1px); box-shadow: var(--shadow); border-color: var(--accent);
}}
.stButton > button:active {{ transform: scale(.97); }}
.stButton > button[kind="primary"], .stFormSubmitButton > button {{
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  color:#04201a; border:none; box-shadow: 0 6px 22px rgba(0,229,160,.35);
}}
.stButton > button[kind="primary"]:hover {{ filter:brightness(1.05); }}

/* ---------- Inputs ---------- */
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
.stNumberInput input, .stTextInput input, .stDateInput input {{
  background: var(--surface) !important; color: var(--text) !important;
  border-radius: var(--r-sm) !important;
}}
[data-baseweb="select"] > div, [data-baseweb="base-input"] {{
  background: var(--surface) !important; border-radius: var(--r-sm) !important;
}}
.stSlider [data-baseweb="slider"] {{ padding-top: 6px; }}

/* ---------- Custom card / component primitives ---------- */
.ns-card {{
  background: var(--surface); border:1px solid var(--border);
  border-radius: var(--r-lg); padding:18px; box-shadow: var(--shadow);
  margin-bottom:14px;
  background-image: linear-gradient(0deg, {grid}, {grid});
}}
.ns-card.glass {{ background:{glass}; backdrop-filter: blur(12px); }}

/* Native bordered containers (st.container(border=True)) styled as cards.
   This reliably wraps charts/widgets, unlike open/close markdown divs. */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}}
div[data-testid="stVerticalBlockBorderWrapper"] > div {{ padding: 4px 2px; }}
.ns-h {{ font-family:'Space Grotesk'; font-weight:700; font-size:1.02rem; margin-bottom:2px; }}
.ns-sub {{ color:var(--muted); font-size:.8rem; }}
.ns-big {{ font-family:'Space Grotesk'; font-weight:700; font-size:2.1rem; line-height:1; }}
.ns-pill {{
  display:inline-flex; align-items:center; gap:6px; padding:5px 11px; border-radius:999px;
  font-size:.74rem; font-weight:600; background:var(--surface2); border:1px solid var(--border);
}}
.ns-pill.accent {{ background:rgba(0,229,160,.14); color:var(--accent); border-color:rgba(0,229,160,.3); }}
.ns-grad {{ background:linear-gradient(135deg,var(--accent),var(--accent2)); -webkit-background-clip:text; background-clip:text; color:transparent; }}

/* macro chips */
.ns-macro {{ display:flex; flex-direction:column; gap:6px; }}
.ns-macro .bar {{ height:8px; border-radius:999px; background:var(--surface2); overflow:hidden; }}
.ns-macro .bar > span {{ display:block; height:100%; border-radius:999px; transition:width .8s cubic-bezier(.2,.8,.2,1); }}

/* qty stepper number (sits between - and + buttons) */
.ns-qty {{
  text-align:center; font-family:'Space Grotesk'; font-weight:700; font-size:1.1rem;
  line-height:46px; min-height:46px; color:var(--text);
}}

/* diary food rows */
.ns-food {{ display:flex; align-items:center; justify-content:space-between; padding:11px 4px; border-bottom:1px dashed var(--border); }}
.ns-food:last-child {{ border-bottom:none; }}
.ns-food .emoji {{ font-size:1.3rem; margin-right:10px; }}

/* hero ring caption */
.ns-ring-cap {{ text-align:center; margin-top:-8px; }}

/* metric grid */
.ns-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
.ns-metric {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--r-md); padding:14px; }}
.ns-metric .k {{ color:var(--muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.6px; }}
.ns-metric .v {{ font-family:'Space Grotesk'; font-weight:700; font-size:1.5rem; letter-spacing:.4px; }}

/* achievement badge */
.ns-badge {{ text-align:center; padding:14px 8px; border-radius:var(--r-md); border:1px solid var(--border); background:var(--surface); }}
.ns-badge.locked {{ opacity:.38; filter:grayscale(.6); }}
.ns-badge .ic {{ font-size:1.9rem; }}
.ns-badge .nm {{ font-weight:600; font-size:.78rem; margin-top:4px; }}
.ns-badge .ds {{ color:var(--muted); font-size:.68rem; }}

/* streak flame */
.ns-streak {{ display:flex; align-items:center; gap:10px; }}
.ns-streak .flame {{ font-size:1.8rem; animation: flicker 1.6s ease-in-out infinite; }}

/* AI scan beam overlay */
.ns-scan {{ position:relative; border-radius:var(--r-md); overflow:hidden; }}
.ns-scanline {{
  position:absolute; left:0; right:0; height:3px;
  background:linear-gradient(90deg,transparent,var(--accent),transparent);
  box-shadow:0 0 18px 3px var(--accent); animation: scan 1.6s ease-in-out infinite;
}}

/* toast-ish callout */
.ns-toast {{ border-left:3px solid var(--accent); background:var(--surface); border-radius:10px; padding:10px 14px; }}

/* ---------- Fixed top bar (mirrors the bottom nav) ---------- */
.ns-topmark {{ height:0; }}
[data-testid="stElementContainer"]:has(.ns-topmark) + * {{
  position: fixed !important; top: 0 !important; left: 50% !important;
  transform: translateX(-50%) !important;
  width: 100% !important; max-width: 540px !important; z-index: 1000000 !important;
  padding: calc(9px + env(safe-area-inset-top)) 16px 9px 16px;
  background: {("rgba(13,15,20,.82)" if mode=="dark" else "rgba(255,255,255,.88)")};
  backdrop-filter: blur(16px) saturate(1.2);
  border-bottom: 1px solid var(--border);
  border-radius: 0 0 22px 22px !important;
}}
/* keep brand + toggles on one centered row */
[data-testid="stElementContainer"]:has(.ns-topmark) + * [data-testid="stHorizontalBlock"] {{
  flex-wrap: nowrap !important; align-items: center !important; gap: 8px !important;
}}
/* let the columns shrink instead of overflowing the bar (mirrors the nav rule) */
[data-testid="stElementContainer"]:has(.ns-topmark) + * [data-testid="stColumn"] {{
  min-width: 0 !important;
}}
/* push both toggles to the right edge of the bar */
.st-key-lang_toggle, .st-key-theme_toggle {{ display: flex !important; justify-content: flex-end !important; }}
/* shared pill look for the top-bar toggles: compact accent chips */
.st-key-lang_toggle button, .st-key-theme_toggle button {{
  min-height: 36px !important; height: 36px !important; line-height: 1 !important;
  font-weight: 700 !important; border-radius: 999px !important;
  transform: none !important; box-shadow: none !important; white-space: nowrap !important;
  background: rgba(0,229,160,.12) !important; color: var(--accent) !important;
  border: 1px solid rgba(0,229,160,.32) !important;
}}
.st-key-lang_toggle button:hover, .st-key-theme_toggle button:hover {{
  background: rgba(0,229,160,.20) !important; border-color: var(--accent) !important;
  transform: none !important; box-shadow: none !important;
}}
.st-key-lang_toggle button {{ padding: 4px 14px !important; font-size: .85rem !important; }}
/* theme toggle is icon-only — make it a round chip */
.st-key-theme_toggle button {{ padding: 0 !important; width: 38px !important; min-width: 38px !important; font-size: 1rem !important; }}

/* ---------- Fixed bottom (thumb-zone) navigation ---------- */
.ns-navmark {{ height:0; }}
[data-testid="stElementContainer"]:has(.ns-navmark) + * {{
  position: fixed !important; bottom: 0 !important; left: 50% !important;
  transform: translateX(-50%) !important;
  width: 100% !important; max-width: 540px !important; z-index: 1000 !important;
  padding: 10px 10px calc(8px + env(safe-area-inset-bottom)) 10px;
  background: {("rgba(13,15,20,.82)" if mode=="dark" else "rgba(255,255,255,.88)")};
  backdrop-filter: blur(16px) saturate(1.2);
  border-top: 1px solid var(--border);
  border-radius: 22px 22px 0 0 !important; overflow: visible !important;
}}
/* keep the 5 nav items in one row inside the wrapper */
[data-testid="stElementContainer"]:has(.ns-navmark) + * [data-testid="stHorizontalBlock"] {{
  flex-wrap: nowrap !important; gap: 4px !important; align-items: end !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * [data-testid="stColumn"] {{
  width: auto !important; flex: 1 1 0 !important; min-width: 0 !important;
}}
/* nav items: monochrome line icon over a small label */
[data-testid="stElementContainer"]:has(.ns-navmark) + * button {{
  flex-direction: column !important; gap: 3px !important; align-items: center !important;
  min-height: 50px !important; padding: 4px 2px !important;
  border: none !important; background: transparent !important; box-shadow: none !important;
  font-size: .66rem !important; font-weight: 600 !important; line-height: 1.2 !important;
  color: var(--muted) !important; transform: none !important;
}}
/* stack the Material icon OVER the label (Streamlit nests them in an inner row) */
[data-testid="stElementContainer"]:has(.ns-navmark) + * button > div,
[data-testid="stElementContainer"]:has(.ns-navmark) + * button > div > span {{
  display: flex !important; flex-direction: column !important;
  align-items: center !important; justify-content: center !important; gap: 2px !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * button [data-testid="stIconMaterial"] {{
  font-size: 24px !important; width: 24px !important; height: 24px !important; color: inherit !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * button:hover,
[data-testid="stElementContainer"]:has(.ns-navmark) + * button:hover [data-testid="stIconMaterial"] {{
  color: var(--text) !important; background: transparent !important;
}}
/* active item: accent icon + label + a small top indicator bar */
[data-testid="stElementContainer"]:has(.ns-navmark) + * button[kind="primary"],
[data-testid="stElementContainer"]:has(.ns-navmark) + * button[kind="primary"] [data-testid="stIconMaterial"] {{
  background: transparent !important; color: var(--accent) !important; box-shadow: none !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * button[kind="primary"]::before {{
  content: ""; position:absolute; top:-2px; width:26px; height:3px; border-radius:3px;
  background: linear-gradient(90deg,var(--accent),var(--accent2));
}}

/* ----- center FAB (Scan): raised gradient circle, Venmo-style ----- */
[data-testid="stElementContainer"]:has(.ns-navmark) + * .st-key-nav_scan button {{
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  width: 58px !important; height: 58px !important; min-height: 58px !important;
  max-width: 58px !important; padding: 0 !important;
  margin: -28px auto 0 !important; border-radius: 50% !important;
  box-shadow: 0 8px 22px rgba(0,229,160,.55), 0 0 0 5px var(--bg) !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * .st-key-nav_scan button [data-testid="stMarkdownContainer"] {{
  display: none !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * .st-key-nav_scan button [data-testid="stIconMaterial"] {{
  font-size: 28px !important; width: 28px !important; height: 28px !important; color: #04201a !important;
}}
[data-testid="stElementContainer"]:has(.ns-navmark) + * .st-key-nav_scan button::before {{ display: none !important; }}
[data-testid="stElementContainer"]:has(.ns-navmark) + * .st-key-nav_scan button:hover {{
  filter: brightness(1.07) !important; transform: none !important;
}}

/* chat bubbles */
[data-testid="stChatMessage"] {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--r-md); }}

/* ---------- AI Coach screen ---------- */
.coach-hero {{
  display:flex; align-items:center; gap:14px;
  background:var(--surface); border:1px solid var(--border);
  border-radius:var(--r-lg); padding:15px 17px; box-shadow:var(--shadow);
  margin-bottom:14px;
}}
.coach-ava {{
  width:46px; height:46px; flex:none; border-radius:14px; font-size:1.45rem;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg, rgba(0,229,160,.22), rgba(96,165,250,.18));
  border:1px solid var(--border);
}}
.ns-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; }}
.ns-dot.live {{ background:var(--accent); box-shadow:0 0 8px var(--accent); animation:pulse 1.8s ease-in-out infinite; }}
.ns-dot.idle {{ background:var(--gold); }}
.coach-note {{
  font-size:.82rem; color:var(--muted); line-height:1.45;
  background:var(--surface2); border:1px solid var(--border);
  border-radius:12px; padding:10px 14px; margin-bottom:14px;
}}
.coach-welcome {{
  display:flex; gap:12px; align-items:flex-start; line-height:1.5;
  background:linear-gradient(135deg, rgba(0,229,160,.10), rgba(96,165,250,.05));
  border:1px solid var(--border); border-left:3px solid var(--accent);
  border-radius:14px; padding:14px 16px; margin-bottom:16px;
}}
.coach-welcome .wave {{ font-size:1.3rem; line-height:1; animation:wave 2.6s ease-in-out infinite; transform-origin:70% 80%; }}
.coach-try {{ text-transform:uppercase; letter-spacing:.9px; font-size:.7rem; color:var(--muted); font-weight:600; margin:2px 2px 9px; }}

/* suggestion chips: the column row right after the .ns-chips marker */
[data-testid="stElementContainer"]:has(.ns-chips) + * button {{
  border-radius:999px !important; background:var(--surface2) !important;
  border:1px solid var(--border) !important; box-shadow:none !important;
  font-weight:500; font-size:.84rem; min-height:44px; color:var(--text) !important;
}}
[data-testid="stElementContainer"]:has(.ns-chips) + * button:hover {{
  border-color:var(--accent) !important; color:var(--accent) !important; transform:translateY(-1px);
}}

/* ---------- Chat input: float it ABOVE the fixed bottom nav ---------- */
[data-testid="stBottom"] {{
  background:transparent !important;
  bottom: calc(86px + env(safe-area-inset-bottom));
  pointer-events:none;
}}
/* Streamlit hardcodes this inner wrapper to the base (dark) backgroundColor, which
   shows as a black band in light mode — force it transparent in both themes. */
[data-testid="stBottom"] > div {{ background: transparent !important; }}
[data-testid="stBottom"] [data-testid="stBottomBlockContainer"] {{
  max-width:540px; margin:0 auto; padding:0 14px 8px;
  background:transparent !important; pointer-events:auto;
}}
/* one clean pill: style the OUTER container, make everything inside transparent */
[data-testid="stChatInput"] {{
  border-radius:28px !important; background:var(--surface) !important;
  border:1px solid var(--border) !important; box-shadow:var(--shadow);
  padding:2px 6px 2px 4px !important;
}}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="input"] {{
  background:transparent !important; border:none !important; box-shadow:none !important;
}}
[data-testid="stChatInput"] textarea {{ background:transparent !important; color:var(--text) !important; }}
[data-testid="stChatInputSubmitButton"] {{
  background:linear-gradient(135deg,var(--accent),var(--accent2)) !important;
  color:#04201a !important; border:none !important; border-radius:50% !important;
  box-shadow:none !important;
}}
[data-testid="stChatInputSubmitButton"]:hover {{ filter:brightness(1.06); transform:none !important; }}
/* reserve room so messages clear the floating input + nav (Coach page only) */
[data-testid="stAppViewContainer"]:has([data-testid="stChatInput"]) [data-testid="stMainBlockContainer"] {{
  padding-bottom: calc(188px + env(safe-area-inset-bottom)) !important;
}}

/* progress bar colour */
.stProgress > div > div > div > div {{ background: linear-gradient(90deg,var(--accent),var(--accent2)); }}

/* dataframe */
[data-testid="stDataFrame"] {{ border-radius:var(--r-md); overflow:hidden; }}

/* fade-in for screens */
[data-testid="stMainBlockContainer"] {{ animation: fadeUp .45s cubic-bezier(.2,.8,.2,1); }}

@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(8px);}} to {{ opacity:1; transform:none;}} }}
@keyframes scan {{ 0%{{top:2%}} 50%{{top:96%}} 100%{{top:2%}} }}
@keyframes flicker {{ 0%,100%{{transform:scale(1) rotate(-3deg); opacity:1}} 50%{{transform:scale(1.12) rotate(3deg); opacity:.85}} }}
@keyframes pop {{ 0%{{transform:scale(.6); opacity:0}} 70%{{transform:scale(1.08)}} 100%{{transform:scale(1); opacity:1}} }}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}
@keyframes wave {{ 0%,60%,100%{{transform:rotate(0)}} 10%,30%{{transform:rotate(14deg)}} 20%{{transform:rotate(-8deg)}} 40%{{transform:rotate(10deg)}} }}
.ns-pop {{ animation: pop .5s cubic-bezier(.2,.9,.3,1.4); }}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; transition: none !important; }}
}}
</style>
"""
