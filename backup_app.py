"""
ui/app.py — Agentic AI Travel Planner
Day 3: Chat re-planning, skeleton loader, edge case handling, polish
"""

import sys, os, re, html as html_lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --ink: #0f0e0c; --paper: #faf8f4;
    --accent: #d4622a; --muted: #6b6560;
    --card: #ffffff; --border: #e8e3db;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; background: var(--paper); color: var(--ink); }
h1,h2,h3 { font-family: 'Playfair Display', serif; }

/* Sidebar */
section[data-testid="stSidebar"] { background: var(--ink) !important; }
section[data-testid="stSidebar"] * { color: var(--paper) !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stDateInput label,
section[data-testid="stSidebar"] .stTextInput label {
    color: #b0a898 !important; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 0.08em;
}

/* Button */
.stButton > button {
    background: var(--accent) !important; color: white !important;
    border: none !important; border-radius: 4px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    font-size: 1rem !important; padding: 0.65rem 2.5rem !important;
    letter-spacing: 0.04em !important; transition: opacity 0.2s !important;
    width: 100% !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; }
.metric-box { flex: 1; background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.2rem; text-align: center; }
.metric-box .val { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: var(--accent); }
.metric-box .lbl { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }

/* Step chip */
.step-chip { display: inline-block; background: #f0ece4; border-radius: 20px; padding: 0.25rem 0.85rem; font-size: 0.78rem; color: var(--muted); margin: 0.2rem; }
.step-chip.active { background: var(--accent); color: white; }

/* Skeleton loader */
@keyframes shimmer { 0%{background-position:-1000px 0} 100%{background-position:1000px 0} }
.skeleton { background: linear-gradient(90deg,#f0ece4 25%,#e8e3db 50%,#f0ece4 75%); background-size: 1000px 100%; animation: shimmer 2s infinite; border-radius: 6px; margin: 0.5rem 0; }
.sk-title { height: 28px; width: 60%; }
.sk-line { height: 14px; width: 100%; }
.sk-line-short { height: 14px; width: 70%; }
.sk-line-med { height: 14px; width: 85%; }
.sk-block { height: 80px; width: 100%; }

/* Itinerary card */
.itin-wrap { background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 12px; padding: 2rem 2.5rem; margin-bottom: 1.5rem; font-family: 'DM Sans', sans-serif; }
.itin-section-header { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #e8894a; margin: 1.5rem 0 0.5rem; padding-bottom: 0.35rem; border-bottom: 1px solid #2d2d44; }
.itin-day-header { font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 700; color: #f0c080; margin: 1.2rem 0 0.5rem; padding: 0.4rem 0.8rem; background: rgba(212,98,42,0.12); border-left: 3px solid #d4622a; border-radius: 0 6px 6px 0; }
.itin-subheader { font-size: 0.8rem; font-weight: 600; color: #a0b4cc; text-transform: uppercase; letter-spacing: 0.1em; margin: 1rem 0 0.3rem; }
.itin-kv { display: flex; gap: 0.75rem; align-items: baseline; padding: 0.22rem 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.itin-key { font-size: 0.75rem; color: #7a8fa6; text-transform: uppercase; letter-spacing: 0.06em; min-width: 130px; flex-shrink: 0; }
.itin-val { font-size: 0.9rem; color: #e8e4dc; }
.itin-bullet { font-size: 0.88rem; color: #c8c0b4; padding: 0.18rem 0 0.18rem 1rem; line-height: 1.6; }
.itin-line { font-size: 0.88rem; color: #c8c0b4; padding: 0.15rem 0; line-height: 1.65; }
.itin-divider { height: 1px; background: linear-gradient(to right,transparent,#3a3a5c,transparent); margin: 0.8rem 0; }
.itin-gap { height: 0.35rem; }

/* Chat */
.chat-wrap { background: #1a1a2e; border: 1px solid #2d2d44; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
.chat-msg-user { background: rgba(212,98,42,0.15); border: 1px solid rgba(212,98,42,0.3); border-radius: 8px 8px 2px 8px; padding: 0.6rem 1rem; margin: 0.5rem 0 0.5rem 3rem; font-size: 0.88rem; color: #f0c080; }
.chat-msg-ai { background: rgba(42,125,212,0.1); border: 1px solid rgba(42,125,212,0.25); border-radius: 8px 8px 8px 2px; padding: 0.6rem 1rem; margin: 0.5rem 3rem 0.5rem 0; font-size: 0.88rem; color: #c8dff0; }
.chat-label { font-size: 0.68rem; color: #6b7a8d; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.15rem; }

/* Trip history */
.hist-item { background: #f7f4ef; border: 1px solid var(--border); border-radius: 6px; padding: 0.5rem 0.75rem; margin: 0.3rem 0; font-size: 0.78rem; color: var(--muted); cursor: pointer; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────
ALL_CITIES = ["Bangalore", "Chennai", "Delhi", "Goa", "Hyderabad", "Jaipur", "Kolkata", "Mumbai"]

VALID_ROUTES = {
    "Bangalore": ["Delhi", "Goa", "Kolkata", "Mumbai"],
    "Chennai":   ["Bangalore", "Hyderabad", "Mumbai"],
    "Delhi":     ["Kolkata"],
    "Goa":       ["Bangalore", "Hyderabad", "Jaipur", "Kolkata", "Mumbai"],
    "Hyderabad": ["Delhi", "Goa", "Kolkata", "Mumbai"],
    "Jaipur":    ["Bangalore", "Chennai", "Delhi", "Kolkata", "Mumbai"],
    "Kolkata":   ["Jaipur"],
    "Mumbai":    ["Goa", "Hyderabad"],
}

TRIP_PURPOSES = ["Leisure", "Honeymoon", "Family", "Business", "Solo Adventure", "Friends Getaway"]
TRAVEL_STYLES = ["Budget 💰", "Comfort 🛋️", "Luxury ✨"]

# ─── Helper Functions ────────────────────────────────────────────────────────

def style_key(s: str) -> str:
    return s.split()[0].lower()


def build_query(source, dest, start_dt, num_days, budget, style, purpose, extra) -> str:
    end_dt = start_dt + timedelta(days=num_days - 1)
    return (
        f"Plan a {num_days}-day {purpose.lower()} trip from {source} to {dest}. "
        f"Travel dates: {start_dt.strftime('%B %d, %Y')} to {end_dt.strftime('%B %d, %Y')}. "
        f"Total budget: Rs.{budget:,}. Travel style: {style_key(style)}. "
        f"Start date for weather: {start_dt.strftime('%Y-%m-%d')}. "
        + (f"Additional notes: {extra}." if extra.strip() else "")
    )


def save_trip(query: str, output: str):
    if "trip_history" not in st.session_state:
        st.session_state.trip_history = []
    st.session_state.trip_history.insert(0, {
        "query": query[:55] + "...",
        "output": output,
        "date": date.today().strftime("%d %b %Y"),
    })
    st.session_state.trip_history = st.session_state.trip_history[:5]


def extract_total_budget(text: str) -> str:
    patterns = [
        r'(?i)TOTAL.*?(?:Rs\.|₹)([\d,]+)',
        r'(?i)Total Estimated.*?(?:Rs\.|₹)([\d,]+)',
        r'(?i)\*\*Total.*?(?:Rs\.|₹)([\d,]+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return "Rs." + m.group(1)
    return "—"


# ─── Render Functions ────────────────────────────────────────────────────────

def render_skeleton():
    """Show animated skeleton loader while agent is thinking."""
    st.markdown("""
    <div style='background:#1a1a2e;border:1px solid #2d2d44;border-radius:12px;padding:2rem 2.5rem;margin-bottom:1.5rem'>
        <div class='skeleton sk-title' style='margin-bottom:1.5rem'></div>
        <div class='skeleton sk-line'></div>
        <div class='skeleton sk-line-med'></div>
        <div class='skeleton sk-line-short'></div>
        <div style='margin-top:1.2rem'></div>
        <div class='skeleton sk-block'></div>
        <div style='margin-top:1.2rem'></div>
        <div class='skeleton sk-line'></div>
        <div class='skeleton sk-line-med'></div>
        <div class='skeleton sk-line'></div>
        <div class='skeleton sk-line-short'></div>
        <div style='margin-top:1.2rem'></div>
        <div class='skeleton sk-block'></div>
        <div style='margin-top:1.2rem'></div>
        <div class='skeleton sk-line-med'></div>
        <div class='skeleton sk-line-short'></div>
    </div>
    """, unsafe_allow_html=True)


def render_itinerary(text: str):
    """Parse agent output and render as styled HTML sections."""
    lines = text.strip().split("\n")
    parts = ["<div class='itin-wrap'>"]

    for line in lines:
        raw = line.rstrip()
        safe = html_lib.escape(raw)

        if set(raw.strip()) <= set("─—-=═") and len(raw.strip()) > 4:
            parts.append("<div class='itin-divider'></div>")
            continue

        if not raw.strip():
            parts.append("<div class='itin-gap'></div>")
            continue

        if raw.strip().startswith("---") or raw.strip().startswith("##"):
            label = html_lib.escape(raw.strip().strip("-#").strip())
            if label:
                parts.append(f"<div class='itin-section-header'>{label}</div>")
            continue

        day_match = re.match(r"\*{0,2}(Day \d+[^\n*]*)\*{0,2}", raw.strip(), re.IGNORECASE)
        if day_match and re.match(r"\s*\*{0,2}day\s+\d+", raw, re.IGNORECASE):
            parts.append(f"<div class='itin-day-header'>{html_lib.escape(day_match.group(1).strip())}</div>")
            continue

        kv = re.match(r"^(\s*)(\*{0,2})([^:*\n]{2,30})(\*{0,2})\s*:\s*(.+)$", raw)
        if kv:
            key = html_lib.escape(kv.group(3).strip().strip("*"))
            val = html_lib.escape(kv.group(5).strip().strip("*"))
            parts.append(f"<div class='itin-kv'><span class='itin-key'>{key}</span><span class='itin-val'>{val}</span></div>")
            continue

        if raw.strip().startswith(("- ", "* ", "• ")):
            val = html_lib.escape(raw.strip()[2:])
            parts.append(f"<div class='itin-bullet'>· {val}</div>")
            continue

        bold_only = re.match(r"^\*{2}([^*]+)\*{2}\s*$", raw.strip())
        if bold_only:
            parts.append(f"<div class='itin-subheader'>{html_lib.escape(bold_only.group(1))}</div>")
            continue

        cleaned = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", raw)
        parts.append(f"<div class='itin-line'>{html_lib.escape(cleaned)}</div>")

    parts.append("</div>")
    st.markdown("\n".join(parts), unsafe_allow_html=True)


def render_budget_chart(output_text: str, budget: int):
    try:
        import plotly.graph_objects as go
        cur = r'(?:Rs\.|₹)'
        patterns = {
            "Flight":    rf'(?i)flight.*?{cur}([\d,]+)',
            "Hotel":     rf'(?i)hotel.*?{cur}([\d,]+)',
            "Food":      rf'(?i)(?:food|meal|dining).*?{cur}([\d,]+)',
            "Transport": rf'(?i)(?:transport|travel|local).*?{cur}([\d,]+)',
            "Activities":rf'(?i)activit.*?{cur}([\d,]+)',
            "Misc":      rf'(?i)misc.*?{cur}([\d,]+)',
        }
        labels, values = [], []
        for label, pattern in patterns.items():
            m = re.search(pattern, output_text)
            if m:
                val = int(m.group(1).replace(",", ""))
                if val > 0:
                    labels.append(label)
                    values.append(val)

        if not values:
            st.info("Budget breakdown will appear here after planning a trip.")
            return

        colors = ["#d4622a","#2a7dd4","#f0a500","#2ab87d","#9b59b6","#e74c3c"]
        fig = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.45,
            marker=dict(colors=colors[:len(labels)], line=dict(color="#1a1a2e", width=2)),
            textfont=dict(family="DM Sans", size=12),
            hovertemplate="<b>%{label}</b><br>Rs.%{value:,}<br>%{percent}<extra></extra>",
        ))
        total = sum(values)
        fig.add_annotation(text=f"Rs.{total:,}", x=0.5, y=0.5,
            font=dict(size=15, family="Playfair Display"), showarrow=False)
        fig.update_layout(margin=dict(t=20,b=20,l=20,r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(family="DM Sans", size=11)), height=320)
        st.plotly_chart(fig, use_container_width=True)

        # Under/over budget
        try:
            m2 = re.search(r'(?i)(?:total|estimated).*?(?:Rs\.|₹)([\d,]+)', output_text)
            if m2:
                total_val = int(m2.group(1).replace(",", ""))
                remaining = budget - total_val
                color = "#2ab87d" if remaining >= 0 else "#e74c3c"
                label_txt = "Under budget ✓" if remaining >= 0 else "Over budget ✗"
                sign = "+" if remaining >= 0 else ""
                st.markdown(f"""
                <div style='margin-top:1rem;padding:1rem;background:#1a1a2e;border:1px solid #2d2d44;border-radius:8px;text-align:center'>
                    <div style='font-size:0.72rem;color:#7a8fa6;text-transform:uppercase;letter-spacing:0.08em'>{label_txt}</div>
                    <div style='font-size:1.8rem;font-family:Playfair Display,serif;color:{color}'>{sign}Rs.{abs(remaining):,}</div>
                    <div style='font-size:0.8rem;color:#a0b4cc'>vs your Rs.{budget:,} budget</div>
                </div>""", unsafe_allow_html=True)
        except Exception:
            pass
    except ImportError:
        st.info("Install `plotly` to enable budget charts.")
    except Exception as e:
        st.info(f"Chart unavailable: {str(e)}")


def render_map(destination: str):
    try:
        import folium
        from streamlit_folium import st_folium
        from tools.weather_tool import CITY_COORDS
        coords = CITY_COORDS.get(destination.lower())
        if not coords:
            st.info(f"Map coordinates not available for {destination}.")
            return
        lat, lon = coords
        m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
        folium.Marker([lat, lon], popup=f"<b>{destination}</b>",
            icon=folium.Icon(color="red", icon="plane", prefix="fa")).add_to(m)
        st_folium(m, width="100%", height=380)
    except ImportError:
        st.info("Install `folium` and `streamlit-folium` to enable the map view.")
    except Exception as e:
        st.info(f"Map unavailable: {str(e)}")


def render_packing_checklist(destination: str):
    beach = ["goa","andaman","kochi","kerala","chennai","mumbai"]
    hill  = ["manali","shimla","darjeeling","leh","ooty","munnar"]
    dest  = destination.lower()
    if dest in beach:
        items = ["👙 Swimwear","🕶️ Sunglasses","🧴 Sunscreen SPF50+","🩴 Flip flops","👒 Sun hat","📱 Waterproof pouch","💊 Motion sickness tabs","🎒 Light backpack"]
    elif dest in hill:
        items = ["🧥 Heavy jacket / fleece","🧤 Gloves & woolen cap","👢 Trekking shoes","💊 Altitude sickness meds","🔦 Torch / headlamp","☕ Thermos","🧴 Moisturizer","🎒 Rain-cover day pack"]
    else:
        items = ["👕 Casual outfits","👟 Comfortable walking shoes","🧴 Toiletries","💊 Basic first aid","🔌 Chargers & power bank","📄 ID / Aadhaar copy","💳 Cards + cash","🎒 Day backpack"]
    cols = st.columns(2)
    for i, item in enumerate(items):
        cols[i % 2].markdown(f"- {item}")


def generate_pdf(output_text: str, query: str) -> bytes:
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(20, 20, 20)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(212, 98, 42)
        pdf.cell(0, 12, "AI Travel Planner", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(107, 101, 96)
        pdf.cell(0, 6, query[:100], new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(15, 14, 12)
        for line in output_text.split("\n"):
            clean = line.encode("latin-1", errors="replace").decode("latin-1")
            if set(clean.strip()) <= set("─—-=═") and len(clean.strip()) > 4:
                pdf.set_draw_color(232, 227, 219)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(3)
            elif re.match(r".*Day \d+.*", clean):
                pdf.set_font("Helvetica", "B", 11)
                pdf.set_text_color(212, 98, 42)
                pdf.multi_cell(0, 7, clean)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(15, 14, 12)
            elif clean.strip():
                pdf.multi_cell(0, 6, clean)
        return bytes(pdf.output())
    except Exception:
        return b""


def render_thinking_steps(steps: list):
    """Show agent tool usage trace — no nested expanders."""
    if not steps:
        return
    with st.expander("🔍 Agent Reasoning Trace", expanded=False):
        for i, (action, observation) in enumerate(steps, 1):
            st.markdown(
                f'<div class="step-chip active">Step {i}</div> '
                f'<span style="font-size:0.85rem;color:#6b6560"><b>{action.tool}</b> ← {str(action.tool_input)[:80]}</span>',
                unsafe_allow_html=True,
            )
            st.code(str(observation)[:400], language=None)


def render_chat_interface(current_output: str):
    """Chat interface for re-planning the current itinerary."""
    st.markdown("### 💬 Modify Your Trip")
    st.markdown('<div style="font-size:0.82rem;color:#6b6560;margin-bottom:0.8rem">Ask the AI to change any part of your itinerary</div>', unsafe_allow_html=True)

    # Examples
    with st.expander("💡 Example requests", expanded=False):
        examples = [
            "Change the hotel to a luxury option",
            "Add one more day to the trip",
            "Replace Day 2 morning activity with something adventurous",
            "Reduce the budget by 20%",
            "Add vegetarian food suggestions",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex[:20]}"):
                st.session_state.chat_input_prefill = ex
                st.rerun()

    # Chat history display
    if "chat_history" in st.session_state and st.session_state.chat_history:
        st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
        for msg in st.session_state.chat_history[-6:]:  # show last 6 messages
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-label'>You</div><div class='chat-msg-user'>{html_lib.escape(msg['content'])}</div>", unsafe_allow_html=True)
            else:
                preview = msg["content"][:300] + ("..." if len(msg["content"]) > 300 else "")
                st.markdown(f"<div class='chat-label'>AI</div><div class='chat-msg-ai'>{html_lib.escape(preview)}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Input
    prefill = st.session_state.pop("chat_input_prefill", "")
    user_msg = st.text_input(
        "Your request",
        value=prefill,
        placeholder="e.g. Change hotel to budget option, add beach day...",
        label_visibility="collapsed",
        key="chat_input_box",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        send = st.button("Send ✈", key="chat_send")
    with col2:
        if st.button("Clear chat", key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()

    if send and user_msg.strip():
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        st.session_state.chat_history.append({"role": "user", "content": user_msg})

        with st.spinner("Re-planning..."):
            try:
                from agent.travel_agent import run_replan_for_ui
                new_output, steps, err = run_replan_for_ui(current_output, user_msg)

                if err:
                    st.error(f"Re-planning failed: {err}")
                elif new_output.strip():
                    st.session_state.last_output = new_output
                    st.session_state.last_steps = steps
                    st.session_state.chat_history.append({
                        "role": "ai",
                        "content": f"Updated! Changes applied: {user_msg}"
                    })
                    save_trip(user_msg, new_output)
                    st.rerun()
                else:
                    st.warning("Agent couldn't apply the change. Try rephrasing.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.5rem 0 1rem'>
        <div style='font-family:Playfair Display,serif;font-size:1.6rem;font-weight:900;color:#faf8f4;line-height:1.1'>
            ✈ Travel<br>Planner
        </div>
        <div style='font-size:0.72rem;color:#6b6560;text-transform:uppercase;letter-spacing:0.1em;margin-top:0.4rem'>
            Powered by LangChain + GPT-4o-mini
        </div>
    </div>
    <hr style='border-color:#2a2825;margin:0.5rem 0 1.5rem'>
    """, unsafe_allow_html=True)

    source = st.selectbox("FROM", ALL_CITIES, index=ALL_CITIES.index("Bangalore"))

    valid_destinations = VALID_ROUTES.get(source, [])
    if not valid_destinations:
        st.warning(f"No outbound flights from {source} in dataset.")
        destination = source
    else:
        destination = st.selectbox("TO", valid_destinations, index=0)

    start_date = st.date_input("DEPARTURE DATE", value=date.today() + timedelta(days=7),
                               min_value=date.today())
    num_days = st.slider("TRIP DURATION (DAYS)", 2, 7, 3)
    budget = st.slider("TOTAL BUDGET (Rs.)", 5000, 100000, 20000, step=1000, format="Rs.%d")
    travel_style = st.selectbox("TRAVEL STYLE", TRAVEL_STYLES, index=1)
    trip_purpose = st.selectbox("TRIP PURPOSE", TRIP_PURPOSES)
    extra_notes = st.text_input("SPECIAL REQUESTS", placeholder="vegetarian food, beach access...")

    st.markdown(
        f"<div style='font-size:0.72rem;color:#6b6560;margin-top:0.4rem'>"
        f"✈ {len(valid_destinations)} route(s) available from {source}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#2a2825;margin:1.5rem 0'>", unsafe_allow_html=True)
    plan_btn = st.button("PLAN MY TRIP →")

    # Trip history
    if "trip_history" in st.session_state and st.session_state.trip_history:
        st.markdown("<div style='font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;color:#6b6560;margin-top:1rem'>PAST TRIPS</div>", unsafe_allow_html=True)
        for i, trip in enumerate(st.session_state.trip_history):
            if st.button(f"📋 {trip['date']}: {trip['query'][:28]}...", key=f"hist_{i}"):
                st.session_state.last_output = trip["output"]
                st.session_state.last_query = trip["query"]
                st.session_state.chat_history = []
                st.rerun()

# ─── Main ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='margin-bottom:2rem'>
    <div style='font-size:0.72rem;text-transform:uppercase;letter-spacing:0.12em;color:#6b6560'>Agentic AI</div>
    <h1 style='font-size:2.6rem;margin:0;line-height:1.1;color:#0f0e0c'>Plan Your Perfect<br>Indian Journey</h1>
    <p style='color:#6b6560;margin-top:0.5rem;font-size:0.95rem'>
        AI searches flights, hotels, weather & attractions — builds your full itinerary in seconds.
    </p>
</div>
""", unsafe_allow_html=True)

# ─── Validation ──────────────────────────────────────────────────────────────
if source == destination:
    st.warning("⚠ Source and destination can't be the same city.")
    st.stop()

if destination not in VALID_ROUTES.get(source, []):
    st.error(f"⚠ No flight data for {source} → {destination}. Available from {source}: {', '.join(VALID_ROUTES.get(source, ['none']))}")
    st.stop()

# ─── Plan Button ─────────────────────────────────────────────────────────────
output_text = st.session_state.get("last_output", "")
last_query  = st.session_state.get("last_query", "")

if plan_btn:
    st.session_state.pop("last_output", None)
    st.session_state.pop("chat_history", None)

    query = build_query(source, destination, start_date, num_days, budget, travel_style, trip_purpose, extra_notes)
    st.session_state.last_query = query

    # Metric strip
    st.markdown(f"""
    <div class='metric-row'>
        <div class='metric-box'><div class='val'>{num_days}</div><div class='lbl'>Days</div></div>
        <div class='metric-box'><div class='val'>Rs.{budget//1000}K</div><div class='lbl'>Budget</div></div>
        <div class='metric-box'><div class='val'>{style_key(travel_style).title()}</div><div class='lbl'>Style</div></div>
        <div class='metric-box'><div class='val'>{destination}</div><div class='lbl'>Destination</div></div>
    </div>""", unsafe_allow_html=True)

    # Skeleton + step chips while running
    skel_slot  = st.empty()
    steps_slot = st.empty()

    with skel_slot.container():
        render_skeleton()

    with st.spinner(""):
        try:
            from agent.travel_agent import run_agent_for_ui
            output_text, steps, err = run_agent_for_ui(query)

            skel_slot.empty()

            if err:
                st.error(f"Agent error: {err}")
                st.info("Check OPENROUTER_API_KEY in your .env and datasets in /data/")
                st.stop()

            if not output_text.strip():
                st.warning("Agent returned no output. Try a shorter trip duration or different route.")
                st.stop()

            if steps:
                steps_slot.markdown(
                    "".join([f'<span class="step-chip active">Step {i+1}: {a.tool}</span>'
                             for i, (a, _) in enumerate(steps)]),
                    unsafe_allow_html=True,
                )

            st.session_state.last_output = output_text
            st.session_state.last_steps  = steps
            save_trip(query, output_text)
            st.rerun()

        except Exception as e:
            skel_slot.empty()
            st.error(f"Failed to run agent: {e}")
            st.info("Make sure OPENROUTER_API_KEY is set in .env and datasets are in /data/")
            st.stop()

# ─── Output ──────────────────────────────────────────────────────────────────
if output_text:
    total_cost = extract_total_budget(output_text)

    st.markdown(f"""
    <div class='metric-row'>
        <div class='metric-box'><div class='val'>{num_days}</div><div class='lbl'>Days</div></div>
        <div class='metric-box'><div class='val'>{total_cost}</div><div class='lbl'>Est. Cost</div></div>
        <div class='metric-box'><div class='val'>{style_key(travel_style).title()}</div><div class='lbl'>Style</div></div>
        <div class='metric-box'><div class='val'>{destination}</div><div class='lbl'>Destination</div></div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Itinerary", "💬 Modify Trip", "🗺 Map", "💰 Budget", "🎒 Packing"])

    with tab1:
        render_itinerary(output_text)
        render_thinking_steps(st.session_state.get("last_steps", []))
        col_dl, _ = st.columns([1, 3])
        with col_dl:
            pdf_bytes = generate_pdf(output_text, last_query)
            if pdf_bytes:
                st.download_button(
                    label="⬇ Download PDF",
                    data=pdf_bytes,
                    file_name=f"trip_{destination.lower()}_{start_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with tab2:
        render_chat_interface(output_text)

    with tab3:
        st.markdown(f"### {destination} — Interactive Map")
        render_map(destination)

    with tab4:
        st.markdown("### Budget Breakdown")
        render_budget_chart(output_text, budget)

    with tab5:
        st.markdown(f"### Packing List for {destination}")
        st.markdown("*Based on destination type & weather profile*")
        render_packing_checklist(destination)

else:
    # Empty state
    st.markdown("""
    <div style='text-align:center;padding:4rem 2rem;color:#6b6560'>
        <div style='font-size:3rem;margin-bottom:1rem'>✈️</div>
        <div style='font-family:Playfair Display,serif;font-size:1.4rem;color:#0f0e0c;margin-bottom:0.5rem'>Ready to plan your trip?</div>
        <div style='font-size:0.9rem'>Set your preferences in the sidebar and click <b>PLAN MY TRIP →</b></div>
    </div>""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    features = [
        ("✈", "Smart Flights", "Cheapest + fastest with backup options"),
        ("🏨", "Best Hotels",  "Matched to your style: budget to luxury"),
        ("🌤", "Live Weather", "Day-wise forecast for your travel dates"),
        ("💬", "Chat & Modify","Change anything via natural language chat"),
    ]
    for col, (icon, title, desc) in zip([col1,col2,col3,col4], features):
        col.markdown(f"""
        <div style='background:#fff;border:1px solid #e8e3db;border-radius:8px;padding:1.5rem;text-align:center'>
            <div style='font-size:1.8rem'>{icon}</div>
            <div style='font-family:Playfair Display,serif;font-weight:700;margin:0.4rem 0'>{title}</div>
            <div style='font-size:0.8rem;color:#6b6560'>{desc}</div>
        </div>""", unsafe_allow_html=True)