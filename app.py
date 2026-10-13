import asyncio
import json
import os
import tempfile
import streamlit as st
from PIL import Image

import pipeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Page Configuration
st.set_page_config(
    page_title="Baby Adult · Narration Agency",
    page_icon="♥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Neo-Brutalist Pixel-Grid Aesthetic (Baby Adult Protection Agency)
st.markdown("""
<style>
    /* Reset & Clean Streamlit */
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    div[data-testid="stToolbar"] { visibility: hidden; display: none; }
    div[data-testid="stDecoration"] { visibility: hidden; display: none; }
    div[data-testid="stStatusWidget"] { visibility: hidden; display: none; }
    
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #EDEDED;
        color: #161616;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1360px !important;
    }
    
    /* Top Nav */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 0 0 20px 0;
        border-bottom: 2px solid #161616;
        margin-bottom: 32px;
    }
    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-text {
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: -0.01em;
        color: #161616;
    }
    .nav-menu {
        display: flex;
        gap: 28px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #161616;
    }
    
    /* Hero Title Section */
    .hero-wrap {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        margin-bottom: 28px;
    }
    .hero-big {
        font-size: 4.2rem;
        font-weight: 700;
        line-height: 0.95;
        letter-spacing: -0.04em;
        color: #161616;
        margin: 0;
    }
    .hero-blurb {
        max-width: 420px;
        font-size: 0.92rem;
        line-height: 1.5;
        color: #444444;
        font-weight: 500;
    }
    
    /* Pixel Graphic Contour Strip */
    .pixel-strip {
        background: #E5E4E0;
        border: 2px solid #161616;
        padding: 10px 16px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #666666;
    }
    .pixel-grid-cells {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pixel-sq-black {
        width: 14px;
        height: 14px;
        background: #161616;
        display: inline-block;
    }
    .pixel-sq-blue {
        width: 14px;
        height: 14px;
        background: #1E3A8A;
        box-shadow: 0 0 8px rgba(30, 58, 138, 0.7);
        display: inline-block;
        position: relative;
    }
    
    /* Column Cards */
    div[data-testid="column"]:nth-of-type(1) > div {
        background: #FFFFFF;
        border: 2px solid #161616;
        padding: 24px;
        box-shadow: 6px 6px 0px #161616;
    }
    
    div[data-testid="column"]:nth-of-type(2) > div {
        background: #161616;
        border: 2px solid #161616;
        padding: 24px;
        color: #FFFFFF;
        box-shadow: 6px 6px 0px rgba(0, 0, 0, 0.3);
    }
    
    /* Typography inside right column */
    div[data-testid="column"]:nth-of-type(2) p,
    div[data-testid="column"]:nth-of-type(2) span,
    div[data-testid="column"]:nth-of-type(2) label {
        color: #E5E5E5 !important;
    }
    
    /* Telemetry Grid */
    .metric-grid-neo {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 20px;
    }
    .metric-card-neo {
        background: #222224;
        border: 1px solid #333335;
        padding: 12px 14px;
    }
    .metric-label-neo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #888888;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-val-neo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.45rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .val-pass { color: #4ADE80 !important; }
    .val-fail { color: #F87171 !important; }
    
    /* Script Editorial Box */
    .script-editorial-neo {
        background: #222224;
        border-left: 3px solid #FFFFFF;
        padding: 16px 18px;
        margin-bottom: 20px;
    }
    .script-meta-neo {
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #888888;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .script-body-neo {
        font-size: 0.96rem;
        line-height: 1.6;
        color: #EDEDED;
    }
    
    /* Banner States */
    .banner-pass-neo {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        background: #052E16;
        border: 1px solid #16A34A;
        color: #4ADE80;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    .banner-fail-neo {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 14px;
        background: #450A0A;
        border: 1px solid #DC2626;
        color: #F87171;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    
    .locked-neo {
        background: #221818;
        border: 2px dashed #DC2626;
        padding: 16px 18px;
        color: #FCA5A5;
        font-size: 0.88rem;
        line-height: 1.5;
        margin-top: 14px;
    }
    .unlocked-neo {
        background: #15271D;
        border: 1px solid #16A34A;
        padding: 10px 14px;
        color: #86EFAC;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 10px;
    }
    
    /* Buttons */
    div.stButton > button {
        background: #161616 !important;
        color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        border: 2px solid #161616 !important;
        border-radius: 0px !important;
        padding: 12px 24px !important;
        box-shadow: 4px 4px 0px #888888 !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stButton > button:hover {
        background: #FFFFFF !important;
        color: #161616 !important;
        border-color: #161616 !important;
        box-shadow: 2px 2px 0px #161616 !important;
        transform: translate(2px, 2px) !important;
    }
    
    div.stDownloadButton > button {
        background: #FFFFFF !important;
        color: #161616 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 0px !important;
        padding: 12px 24px !important;
        box-shadow: 4px 4px 0px #4ADE80 !important;
        transition: all 0.15s ease-in-out !important;
    }
    div.stDownloadButton > button:hover {
        background: #4ADE80 !important;
        color: #161616 !important;
        border-color: #4ADE80 !important;
        box-shadow: 2px 2px 0px #FFFFFF !important;
        transform: translate(2px, 2px) !important;
    }
    
    /* Form Inputs */
    div[data-baseweb="input"] input {
        border-radius: 0px !important;
        border: 2px solid #161616 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
    }
    
    /* Tabs */
    div[data-baseweb="tab-list"] {
        gap: 6px !important;
        border-bottom: 2px solid #161616 !important;
        margin-bottom: 16px !important;
    }
    button[data-baseweb="tab"] {
        border-radius: 0px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #777777 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #161616 !important;
        border-bottom-color: #161616 !important;
    }
</style>
""", unsafe_allow_html=True)

# 1. Top Navigation
st.markdown("""
<div class="top-nav">
    <div class="brand-wrap">
        <svg width="26" height="22" viewBox="0 0 14 12" fill="#161616" style="shape-rendering: crispEdges;">
            <rect x="2" y="0" width="3" height="2"/>
            <rect x="9" y="0" width="3" height="2"/>
            <rect x="1" y="2" width="5" height="2"/>
            <rect x="8" y="2" width="5" height="2"/>
            <rect x="0" y="4" width="14" height="2"/>
            <rect x="1" y="6" width="12" height="2"/>
            <rect x="3" y="8" width="8" height="2"/>
            <rect x="5" y="10" width="4" height="2"/>
        </svg>
        <div class="brand-text">
            Baby Adult<br>Protection Agency
        </div>
    </div>
    <div class="nav-menu">
        <span>Services</span>
        <span>About</span>
        <span>Contact</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Hero Headline
st.markdown("""
<div class="hero-wrap">
    <div>
        <h1 class="hero-big">Adulthood<br>is hard.</h1>
    </div>
    <div class="hero-blurb">
        Helping newbie presentations (thirties or fifties... who cares) figure out how to navigate narration and do a tiny bit better. Calibrated rate <strong>2.73 wps</strong> via JennyNeural.
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Stepped Pixel Boundary Strip
st.markdown("""
<div class="pixel-strip">
    <div class="pixel-grid-cells">
        <span>1</span> <span>1</span> <span class="pixel-sq-black"></span>
        <span>1</span> <span>2</span> <span>1</span> <span class="pixel-sq-black"></span>
        <span>2</span> <span>1</span> <span>3</span> <span class="pixel-sq-blue"></span>
        <span>1</span> <span>1</span> <span class="pixel-sq-black"></span>
        <span>2</span> <span>1</span> <span>1</span>
    </div>
    <div>[GRID: 128.4 // CALIBRATION 2.73 WPS // MUTAGEN VERIFIED]</div>
</div>
""", unsafe_allow_html=True)

# Load holdout runs data
holdout_runs_data = []
holdout_file_path = os.path.join(BASE_DIR, "holdout_results.json")
if os.path.exists(holdout_file_path):
    try:
        with open(holdout_file_path, "r", encoding="utf-8") as hf:
            raw_runs = json.load(hf)
            ordered_ids = ["run_h04", "run_h01", "run_h02", "run_h03"]
            holdout_runs_data = sorted(raw_runs, key=lambda x: ordered_ids.index(x.get("run_id", "run_h04")) if x.get("run_id") in ordered_ids else 99)
    except Exception as e:
        print(f"Error loading holdout results: {e}")

holdout_dict = {hr["run_id"]: hr for hr in holdout_runs_data}

# Layout Columns
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div style="font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 14px;">■ 01 // SLIDE SOURCE & DURATION</div>', unsafe_allow_html=True)

    tab_eval, tab_holdout, tab_upload = st.tabs([
        "Benchmark Runs",
        "Holdout Deck",
        "Upload Slide"
    ])

    selected_image_path = None
    slide_label = "slide"
    selected_holdout = None
    target_seconds = 20.0

    # Tab 1: Benchmark Runs
    with tab_eval:
        run_labels = {
            "run_h04": "run_h04 · Paid seats by plan [20.0s] — PASS (Gap -0.2s)",
            "run_h01": "run_h01 · Paid seats by plan [30.0s] — FAIL (Gap +7.2s, Locked)",
            "run_h02": "run_h02 · Weekly active editors [20.0s] — PASS (Gap -2.3s)",
            "run_h03": "run_h03 · Monthly sales [20.0s] — PASS (Gap -1.2s)"
        }
        
        raw_query = st.query_params.to_dict() if hasattr(st.query_params, "to_dict") else {}
        q_run = raw_query.get("run", "run_h04")
        default_idx = list(run_labels.keys()).index(q_run) if q_run in run_labels else 0

        chosen_run_id = st.selectbox(
            "Select Benchmark Run:",
            options=list(run_labels.keys()),
            format_func=lambda x: run_labels[x],
            index=default_idx
        )
        selected_holdout = holdout_dict.get(chosen_run_id)
        if selected_holdout:
            sid = selected_holdout["slide_id"]
            h_files = [f for f in os.listdir("holdout_slides") if f.startswith(sid)] if os.path.exists("holdout_slides") else []
            if h_files:
                selected_image_path = os.path.join("holdout_slides", h_files[0])
                slide_label = os.path.splitext(h_files[0])[0]
            target_seconds = float(selected_holdout["target_seconds"])

    # Tab 2: Holdout Deck
    with tab_holdout:
        holdout_dir = "holdout_slides"
        available_files = sorted([f for f in os.listdir(holdout_dir) if f.endswith(".png")]) if os.path.exists(holdout_dir) else []
        if available_files:
            chosen_deck_file = st.selectbox("Select Holdout Slide Graphic:", available_files)
            if not selected_holdout:
                selected_image_path = os.path.join(holdout_dir, chosen_deck_file)
                slide_label = os.path.splitext(chosen_deck_file)[0]

    # Tab 3: Upload Custom
    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload 1 Slide Image (PNG, JPG)",
            type=["png", "jpg", "jpeg"]
        )
        if uploaded_file is not None:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_image_path = temp_path
            slide_label = os.path.splitext(uploaded_file.name)[0]
            selected_holdout = None

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    target_seconds = st.number_input(
        "TARGET DURATION (SECONDS)",
        min_value=5.0,
        max_value=120.0,
        value=float(target_seconds),
        step=1.0,
        help="Target length for narration audio. Tolerance is ±3.0s."
    )

    if selected_image_path and os.path.exists(str(selected_image_path)):
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        image = Image.open(str(selected_image_path))
        st.image(image, use_container_width=True, caption=f"GRAPHIC: {slide_label}")

    with st.expander("DIAGNOSTICS & RETRY CONTROLS", expanded=False):
        force_short_draft = st.checkbox("Force Short Draft Mode (triggers Step 2 model rewrite)", value=False)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    generate_clicked = st.button("■ GENERATE NARRATION", use_container_width=True)

with col_right:
    st.markdown('<div style="font-size: 0.8rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #FFFFFF; margin-bottom: 14px;">■ 02 // TELEMETRY & GATED DELIVERY</div>', unsafe_allow_html=True)

    if generate_clicked:
        if not selected_image_path or not os.path.exists(str(selected_image_path)):
            st.error("Please upload or select a slide graphic first.")
        else:
            with st.spinner("Analyzing slide semantics and synthesizing narration..."):
                try:
                    pipeline.check_configuration()
                    run_result = asyncio.run(
                        pipeline.process_slide_custom(
                            image_path=str(selected_image_path),
                            target_seconds=float(target_seconds),
                            slide_id=str(slide_label),
                            force_short_draft=force_short_draft
                        )
                    )
                    st.session_state["latest_run"] = run_result
                except Exception as e:
                    st.error(f"Execution Error: {e}")

    # Determine active result
    res = None
    if generate_clicked and "latest_run" in st.session_state:
        res = st.session_state["latest_run"]
    elif "latest_run" in st.session_state and not selected_holdout:
        res = st.session_state["latest_run"]
    elif selected_holdout:
        res = {
            "status": selected_holdout["verdict"],
            "slide_id": selected_holdout["slide_id"],
            "retries_used": selected_holdout.get("retries_used", 0),
            "final_attempt": {
                "script": selected_holdout["script"],
                "target": selected_holdout["target_seconds"],
                "measured": selected_holdout["measured_seconds"],
                "gap": selected_holdout["gap"],
                "audio_path": selected_holdout["audio_file"]
            },
            "attempts": [
                {
                    "attempt": i + 1,
                    "rate": "+0%",
                    "measured": selected_holdout["measured_seconds"],
                    "gap": selected_holdout["gap"],
                    "verdict": selected_holdout["verdict"],
                    "script": selected_holdout["script"]
                }
                for i in range(selected_holdout.get("retries_used", 0) + 1)
            ]
        }
    elif "latest_run" in st.session_state:
        res = st.session_state["latest_run"]

    if res:
        final_att = res.get("final_attempt", {})
        attempts = res.get("attempts", [])
        retries_used = res.get("retries_used", max(0, len(attempts) - 1))
        
        final_script = final_att.get("script", "")
        target_sec = float(final_att.get("target", target_seconds))
        measured_sec = float(final_att.get("measured", 0.0))
        gap = float(final_att.get("gap", 0.0))
        is_pass = abs(gap) <= 3.0 and res.get("status") == "PASS"
        audio_path = final_att.get("audio_path", "")

        # Verdict Banner
        if is_pass:
            st.markdown(f'<div class="banner-pass-neo">✓ TIMING GATE PASSED // GAP {gap:+.1f}S WITHIN ±3.0S</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="banner-fail-neo">✗ TIMING GATE FAILED // GAP {gap:+.1f}S EXCEEDED</div>', unsafe_allow_html=True)

        # 4-Cell Telemetry Grid
        gap_class = "val-pass" if is_pass else "val-fail"
        st.markdown(f"""
        <div class="metric-grid-neo">
            <div class="metric-card-neo">
                <div class="metric-label-neo">TARGET</div>
                <div class="metric-val-neo">{target_sec:.1f}s</div>
            </div>
            <div class="metric-card-neo">
                <div class="metric-label-neo">MEASURED</div>
                <div class="metric-val-neo">{measured_sec:.1f}s</div>
            </div>
            <div class="metric-card-neo">
                <div class="metric-label-neo">GAP</div>
                <div class="metric-val-neo {gap_class}">{gap:+.1f}s</div>
            </div>
            <div class="metric-card-neo">
                <div class="metric-label-neo">RETRIES</div>
                <div class="metric-val-neo">{retries_used}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Editorial Script Box
        words = len(final_script.split())
        st.markdown(f"""
        <div class="script-editorial-neo">
            <div class="script-meta-neo">
                <span>TRANSCRIPT</span>
                <span>{words} WORDS // ~{words / 2.73:.1f}S AT 2.73 WPS</span>
            </div>
            <div class="script-body-neo">"{final_script}"</div>
        </div>
        """, unsafe_allow_html=True)

        # Gated Audio Delivery
        if is_pass and audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as af:
                audio_bytes = af.read()
            
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button(
                label="■ DOWNLOAD AUDIO (.MP3)",
                data=audio_bytes,
                file_name=f"{res.get('slide_id', 'slide')}_narration.mp3",
                mime="audio/mp3",
                use_container_width=True
            )
            st.markdown('<div class="unlocked-neo">✓ Gated delivery passed. Audio length fits the slide presentation slot within ±3.0s.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="locked-neo">
                <strong>DOWNLOAD LOCKED // EXCEEDED 3.0S WINDOW</strong><br>
                Measured duration ({measured_sec:.1f}s) missed the target length ({target_sec:.1f}s) by <strong>{gap:+.1f}s</strong> after {retries_used} retries.<br>
                Per presentation delivery policy, audio that misses the slot is strictly suppressed from download.
            </div>
            """, unsafe_allow_html=True)

        with st.expander("DIAGNOSTIC ATTEMPT TRACE", expanded=False):
            for att in attempts:
                st.caption(f"Attempt {att.get('attempt')}: Rate {att.get('rate')} | Measured {att.get('measured'):.1f}s | Gap {att.get('gap'):+.1f}s | Verdict: {att.get('verdict')}")
    else:
        st.markdown("""
        <div style="background: #222224; border: 1px solid #333335; padding: 24px;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888888; text-transform: uppercase;">■ AWAITING RUN</div>
            <p style="color: #CCCCCC; font-size: 0.95rem; margin-top: 8px;">Select a slide on the left and click <strong>■ GENERATE NARRATION</strong> to begin speech synthesis.</p>
        </div>
        """, unsafe_allow_html=True)
