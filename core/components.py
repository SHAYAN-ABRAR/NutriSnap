"""
Reusable UI building blocks: theme injection, calorie ring, macro bars,
metric cards, charts and the achievement celebration. Keeps views declarative.
"""
from __future__ import annotations

from contextlib import contextmanager

import streamlit as st
import plotly.graph_objects as go

from core import theme as T
from core import database as db


# ------------------------------- theme / chrome ------------------------------
def get_mode() -> str:
    return db.get_meta("theme", "dark") or "dark"


def inject_theme() -> dict:
    mode = get_mode()
    scale = db.get_meta("text_scale", 1.0) or 1.0
    st.markdown(T.inject_css(mode, scale), unsafe_allow_html=True)
    return T.palette(mode)


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def section(title: str, sub: str = "", emoji: str = "") -> None:
    from core.i18n import t
    title, sub = t(title), t(sub)
    head = f"{emoji} {title}" if emoji else title
    html(f"<div class='ns-h' style='font-size:1.15rem;margin-top:4px'>{head}</div>"
         + (f"<div class='ns-sub' style='margin-bottom:8px'>{sub}</div>" if sub else "<div style='height:6px'></div>"))


@contextmanager
def card():
    """A real container styled like .ns-card — use this to wrap charts/widgets."""
    with st.container(border=True):
        yield


def card_title(title: str, sub: str = "") -> None:
    from core.i18n import t
    s = f"<div class='ns-h'>{t(title)}</div>"
    if sub:
        s += f"<div class='ns-sub'>{t(sub)}</div>"
    html(s)


def image_to_datauri(uploaded, max_px: int = 420) -> str:
    """Convert an uploaded image to a small JPEG data URI for local storage."""
    try:
        import io
        import base64
        from PIL import Image
        img = Image.open(uploaded).convert("RGB")
        img.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _enlarge_url(url: str) -> str:
    """Bump a Wikimedia thumbnail to a larger size for the full-view link."""
    if "upload.wikimedia.org" in url:
        import re
        return re.sub(r"/\d+px-", "/800px-", url)
    return url  # data URIs / originals open as-is


def food_icon(item: dict, size: int = 32) -> str:
    """A real food photo (tap to enlarge) if available, else the emoji."""
    img = (item.get("image") or "").strip() if isinstance(item, dict) else ""
    if img:
        big = _enlarge_url(img)
        return (f"<a href='{big}' target='_blank' rel='noopener' title='Tap to view full image' "
                f"style='display:inline-block;line-height:0'>"
                f"<img src='{img}' loading='lazy' alt='' "
                f"style='width:{size}px;height:{size}px;object-fit:cover;border-radius:9px;"
                f"vertical-align:middle;margin-right:9px;cursor:zoom-in'></a>")
    emoji = (item.get("emoji") if isinstance(item, dict) else None) or "🍽️"
    return f"<span style='font-size:{int(size*0.72)}px;margin-right:8px;vertical-align:middle'>{emoji}</span>"


# --------------------------------- charts ------------------------------------
def _style(fig, p, h=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=p["text"], family="Inter"),
        margin=dict(l=6, r=6, t=10, b=6), showlegend=False,
    )
    if h:
        fig.update_layout(height=h)
    return fig


def ring_color(consumed: float, goal: int, p: dict) -> str:
    """Green in range, amber as you near the goal, red once over budget."""
    if goal <= 0:
        return p["accent"]
    pct = consumed / goal * 100
    if pct > 100:
        return p["warn"]
    if pct >= 85:
        return p["gold"]
    return p["accent"]


def calorie_ring(consumed: float, goal: int, p: dict, height: int = 230) -> None:
    consumed = max(0, consumed)
    remaining = max(0, goal - consumed)
    over = max(0, consumed - goal)
    pct = round(consumed / goal * 100) if goal else 0
    color = ring_color(consumed, goal, p)

    values = [min(consumed, goal), remaining] if not over else [goal, 0]
    fig = go.Figure(go.Pie(
        values=values if not over else [1],
        hole=0.74, sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[color, p["surface2"]] if not over else [p["warn"]]),
        textinfo="none", hoverinfo="skip",
    ))
    from core import i18n
    fig.add_annotation(text=f"<b>{i18n.num(int(consumed))}</b>", font=dict(size=34, color=p["text"]),
                       showarrow=False, y=0.56)
    fig.add_annotation(text=i18n.tf(f"of {goal} kcal", f"{goal} ক্যালরির মধ্যে"),
                       font=dict(size=13, color=p["muted"]), showarrow=False, y=0.40)
    sub = (i18n.tf(f"{int(remaining)} left", f"{int(remaining)} বাকি") if not over
           else i18n.tf(f"{int(over)} over", f"{int(over)} বেশি"))
    fig.add_annotation(text=sub, font=dict(size=12, color=color), showarrow=False, y=0.27)
    _style(fig, p, height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def mini_ring(value: float, goal: float, p: dict, color: str, label: str, unit: str,
              height: int = 150) -> None:
    value = max(0, value)
    frac = min(value, goal)
    rest = max(0, goal - value)
    fig = go.Figure(go.Pie(
        values=[frac, rest] if goal else [0, 1], hole=0.72, sort=False,
        direction="clockwise", marker=dict(colors=[color, p["surface2"]]),
        textinfo="none", hoverinfo="skip",
    ))
    from core import i18n
    fig.add_annotation(text=f"<b>{i18n.num(int(value))}</b>", font=dict(size=20, color=p["text"]),
                       showarrow=False, y=0.54)
    fig.add_annotation(text=i18n.loc(label), font=dict(size=11, color=p["muted"]), showarrow=False, y=0.34)
    _style(fig, p, height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def weight_ring(current: float, start: float, target, p: dict, height: int = 140) -> None:
    """Progress ring from start → target weight. Center marks the current weight and
    the goal; the arc fills with how far along the journey you are (works for lose or gain)."""
    has_goal = target is not None
    span = (start - target) if (has_goal and start is not None) else 0.0
    if abs(span) > 0.05:
        frac = max(0.0, min(1.0, (start - current) / span))
    else:
        frac = 1.0 if (has_goal and abs(current - target) < 0.5) else 0.0
    reached = has_goal and abs(current - target) < 0.3
    color = p["accent"] if (frac > 0 or reached) else p["water"]

    fig = go.Figure(go.Pie(
        values=[frac, 1 - frac], hole=0.72, sort=False,
        direction="clockwise", rotation=0,
        marker=dict(colors=[color, p["surface2"]]),
        textinfo="none", hoverinfo="skip",
    ))
    from core import i18n
    fig.add_annotation(text=f"<b>{i18n.num(f'{current:g}')}</b>", font=dict(size=20, color=p["text"]),
                       showarrow=False, y=0.54)
    sub = i18n.tf(f"of {target:g} kg", f"লক্ষ্য {target:g} kg") if has_goal else i18n.tf("kg", "কেজি")
    fig.add_annotation(text=sub, font=dict(size=11, color=p["muted"]), showarrow=False, y=0.33)
    _style(fig, p, height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def macro_bars(totals: dict, goals: dict, p: dict) -> None:
    from core.i18n import t, loc as loc_fn
    rows = [
        (t("Protein"), totals.get("protein", 0), goals.get("protein_g", 1), p["protein"], "g"),
        (t("Carbs"),   totals.get("carbs", 0),   goals.get("carbs_g", 1),   p["carbs"], "g"),
        (t("Fat"),     totals.get("fat", 0),      goals.get("fat_g", 1),     p["fat"], "g"),
        (t("Fiber"),   totals.get("fiber", 0),    max(25, goals.get("fiber_g", 25)), p["fiber"], "g"),
    ]
    out = f"<div class='ns-card'><div class='ns-h'>{t('Macros')}</div>"
    out += "<div style='display:flex;flex-direction:column;gap:14px;margin-top:10px'>"
    for name, val, goal, col, unit in rows:
        pct = min(100, round(val / goal * 100)) if goal else 0
        out += (
            f"<div class='ns-macro'>"
            f"<div style='display:flex;justify-content:space-between;font-size:.85rem'>"
            f"<span style='font-weight:600'>{name}</span>"
            f"<span style='color:var(--muted)'>{loc_fn(f'{int(val)} / {int(goal)} {unit}')}</span></div>"
            f"<div class='bar'><span style='width:{pct}%;background:{col}'></span></div>"
            f"</div>"
        )
    out += "</div></div>"
    html(out)


def metric_grid(items: list[tuple]) -> None:
    """items: [(label, value, color)]"""
    from core.i18n import loc
    cells = "".join(
        f"<div class='ns-metric'><div class='k'>{k}</div>"
        f"<div class='v' style='color:{c}'>{loc(str(v))}</div></div>"
        for k, v, c in items
    )
    html(f"<div class='ns-grid'>{cells}</div>")


def weekly_bar(data: list[dict], goal: int, p: dict, height: int = 230) -> None:
    import datetime as dt
    labels = [dt.date.fromisoformat(d["log_date"]).strftime("%a") for d in data]
    vals = [d["calories"] for d in data]
    colors = [p["accent"] if v <= goal else p["warn"] for v in vals]
    fig = go.Figure(go.Bar(x=labels, y=vals, marker_color=colors,
                           marker_line_width=0, width=0.6,
                           hovertemplate="%{y:.0f} kcal<extra></extra>"))
    fig.add_hline(y=goal, line_dash="dot", line_color=p["muted"],
                  annotation_text="goal", annotation_font_color=p["muted"])
    fig.update_yaxes(showgrid=False, zeroline=False)
    fig.update_xaxes(showgrid=False)
    _style(fig, p, height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def trend_line(dates, values, p: dict, color=None, fill=True, height=230,
               target=None, unit="") -> None:
    color = color or p["accent"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=values, mode="lines+markers",
        line=dict(color=color, width=3, shape="spline"),
        marker=dict(size=7, color=color),
        fill="tozeroy" if fill else None,
        fillcolor=_rgba(color, 0.12),
        hovertemplate="%{y:.1f}" + unit + "<extra></extra>",
    ))
    if target is not None:
        fig.add_hline(y=target, line_dash="dot", line_color=p["muted"],
                      annotation_text="target", annotation_font_color=p["muted"])
    fig.update_yaxes(showgrid=True, gridcolor=_rgba(p["muted"], 0.12), zeroline=False)
    fig.update_xaxes(showgrid=False)
    _style(fig, p, height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def weight_progress_chart(dates, values, target, p: dict, height=250) -> None:
    """Weight over time, done right: the y-axis zooms to the real range (so a few
    kg of change is actually visible), the goal zone is shaded, the target line is
    marked, and start + latest weigh-ins are labelled."""
    vals = [float(v) for v in values]
    anchors = vals + ([float(target)] if target is not None else [])
    span = max(anchors) - min(anchors)
    pad_bot = max(1.2, span * 0.18)
    pad_top = max(2.8, span * 0.42)   # extra headroom so the value labels clear the top
    lo, hi = min(anchors) - pad_bot, max(anchors) + pad_top

    fig = go.Figure()
    # goal zone + target reference line
    if target is not None:
        fig.add_hrect(y0=target - 0.4, y1=target + 0.4,
                      fillcolor=_rgba(p["accent"], 0.14), line_width=0)
        fig.add_hline(y=target, line_dash="dash", line_color=p["accent"],
                      annotation_text=f"target {target:g} kg",
                      annotation_position="bottom right",
                      annotation_font=dict(color=p["accent"], size=11))
    # the weigh-in line
    fig.add_trace(go.Scatter(
        x=dates, y=vals, mode="lines+markers",
        line=dict(color=p["accent"], width=3, shape="spline"),
        marker=dict(size=8, color=p["accent"], line=dict(color=p["bg"], width=1.6)),
        fill="tozeroy", fillcolor=_rgba(p["accent"], 0.10),
        hovertemplate="%{x}: %{y:.1f} kg<extra></extra>",
    ))
    # label the latest weigh-in (and the start, when there's room)
    fig.add_annotation(x=dates[-1], y=vals[-1], text=f"<b>{vals[-1]:g} kg</b>",
                       showarrow=False, yshift=15, font=dict(color=p["text"], size=12))
    if len(vals) > 1:
        fig.add_annotation(x=dates[0], y=vals[0], text=f"{vals[0]:g}",
                           showarrow=False, yshift=15, font=dict(color=p["muted"], size=11))
    fig.update_yaxes(range=[lo, hi], showgrid=True, gridcolor=_rgba(p["muted"], 0.12),
                     ticksuffix=" kg", zeroline=False)
    fig.update_xaxes(showgrid=False)
    _style(fig, p, height)
    fig.update_layout(margin=dict(l=6, r=6, t=22, b=6))  # extra top room for labels
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def donut(labels, values, colors, p: dict, center="", height=230) -> None:
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False,
                           marker=dict(colors=colors), textinfo="percent",
                           textfont=dict(color=p["text"], size=12)))
    if center:
        fig.add_annotation(text=center, showarrow=False, font=dict(size=14, color=p["muted"]))
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1,
                      font=dict(color=p["text"], size=11)))
    _style(fig, p, height)
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _rgba(hex_color: str, a: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


# ------------------------------- celebration ---------------------------------
def celebrate(new_achievements: list[dict]) -> None:
    from core.i18n import t, tf
    if not new_achievements:
        return
    st.balloons()
    for a in new_achievements:
        st.toast(tf(f"{a['icon']}  Achievement unlocked — {a['name']}!",
                    f"{a['icon']}  অর্জন আনলক — {t(a['name'])}!"), icon="🏆")


# ---------------------------- shareable recap (#4) ---------------------------
def daily_recap_image(ctx: dict) -> bytes:
    """Render today's summary as a shareable PNG (no emojis — PIL's font lacks them)."""
    import io
    import datetime as dt
    from PIL import Image, ImageDraw, ImageFont

    W, H = 900, 560
    img = Image.new("RGB", (W, H), "#0d0f14")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill="#00e5a0")          # accent top bar

    def font(sz):
        try:
            return ImageFont.load_default(size=sz)       # Pillow >= 10
        except TypeError:
            return ImageFont.load_default()

    accent, white, muted = (0, 229, 160), (232, 234, 240), (139, 147, 167)
    d.text((44, 44), "NutriSnap", font=font(46), fill=accent)
    d.text((46, 104), dt.date.today().strftime("%A, %d %B %Y"), font=font(26), fill=muted)

    cal, goal = int(ctx.get("consumed", 0)), int(ctx.get("calorie_goal", 0) or 0)
    left = max(0, int(ctx.get("remaining", 0)))
    d.text((44, 170), str(cal), font=font(130), fill=white)
    d.text((50, 320), f"of {goal} kcal   |   {left} left", font=font(28), fill=muted)

    y, x = 380, 46
    for name, val, g, col in (
        ("Protein", ctx.get("protein", 0), ctx.get("protein_goal", 0), (96, 165, 250)),
        ("Carbs",   ctx.get("carbs", 0),   ctx.get("carbs_goal", 0),   (251, 191, 36)),
        ("Fat",     ctx.get("fat", 0),     ctx.get("fat_goal", 0),     (248, 113, 113)),
    ):
        d.text((x, y), name, font=font(24), fill=muted)
        d.text((x, y + 32), f"{int(val)}/{int(g)}g", font=font(34), fill=col)
        x += 230

    d.text((46, 488), f"Water  {int(ctx.get('water', 0))}/{int(ctx.get('water_goal', 0))} ml",
           font=font(26), fill=(56, 189, 248))
    d.text((520, 488), f"Streak  {int(ctx.get('streak', 0))} days", font=font(26), fill=accent)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
