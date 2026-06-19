"""AI Nutrition Coach: conversational assistant grounded in the user's live data."""
from __future__ import annotations

import streamlit as st

from core import ai
from core import database as db
from core import components as C
from core import state as S
from core import i18n
from core.i18n import t

SUGGESTIONS = [
    "What should I eat for dinner?",
    "How am I doing today?",
    "Give me a high-protein snack",
    "Am I drinking enough water?",
]


def render(p: dict) -> None:
    live = ai.is_live()

    # ---- coach hero: avatar + title + live status ----
    C.html(
        "<div class='coach-hero'>"
        "<div class='coach-ava'>🤖</div>"
        "<div style='flex:1;min-width:0'>"
        f"<div class='ns-h' style='font-size:1.12rem'>{t('AI Coach')}</div>"
        f"<div class='ns-sub'>{t('Personalized advice from your real numbers.')}</div></div>"
        f"<span class='ns-pill {'accent' if live else ''}'>"
        f"<span class='ns-dot {'live' if live else 'idle'}'></span>"
        f"{t('Connected') if live else t('Offline')}</span>"
        "</div>"
    )
    if not live:
        C.html(f"<div class='coach-note'>💡 {i18n.tf('Answers use your live stats. Add an Ollama key in <b>Settings</b> for full conversational AI.', 'উত্তরগুলো আপনার আসল হিসাব থেকে আসে। পুরো কথোপকথনের এআই-এর জন্য <b>সেটিংসে</b> একটি Ollama কী দিন।')}</div>")

    history = db.get_chat()
    # CSS floats this just above the chat input (see .st-key-clear_chat), so it's
    # always reachable even after a long conversation.
    if history and st.button(i18n.tf("🗑 Clear chat", "🗑 চ্যাট মুছুন"), key="clear_chat"):
        db.clear_chat()
        st.rerun()
    if not history:
        C.html(f"<div class='coach-welcome'><span class='wave'>👋</span>"
               f"<div>{i18n.tf('<b>Hi! I am your nutrition coach.</b><br>Ask me what to eat, how your day looks, or tap a suggestion below.', '<b>হাই! আমি আপনার পুষ্টি কোচ।</b><br>কী খাবেন, আজকের দিন কেমন — জিজ্ঞেস করুন বা নিচের একটি প্রশ্নে ট্যাপ করুন।')}</div></div>")

    for msg in history:
        avatar = "🤖" if msg["role"] == "assistant" else "🙂"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # suggestion chips (the .ns-chips marker styles the column row that follows)
    if len(history) < 2:
        C.html(f"<div class='coach-try'>{t('Try asking')}</div><div class='ns-chips'></div>")
        cols = st.columns(2)
        for i, s in enumerate(SUGGESTIONS):
            if cols[i % 2].button(t(s), use_container_width=True, key=f"sug{i}"):
                _send(t(s))   # send the localized text so the chat stays in one language
                st.rerun()

    prompt = st.chat_input(t("Ask your coach…"))
    if prompt:
        _send(prompt)
        st.rerun()


def _send(text: str) -> None:
    db.add_chat("user", text)
    ctx = S.daily_context()
    with st.spinner("Coach is thinking…"):
        reply = ai.coach_reply(text, ctx, db.get_chat())
    db.add_chat("assistant", reply)
