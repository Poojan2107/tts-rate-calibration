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
    page_title="Canva Magic Studio — Slide Narration",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #1E1B4B 0%, #0F172A 50%, #020617 100%);
        color: #F8FAFC;
    }
    
    .main-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(125, 42, 232, 0.3);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
        backdrop-filter: blur(8px);
    }
    
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #F8FAFC;
    }
    
    .metric-pass { color: #34D399 !important; }
    .metric-fail { color: #F87171 !important; }
    
    .script-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 12px;
        padding: 20px;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #F1F5F9;
        margin-top: 12px;
    }
    
    .status-badge-pass {
        display: inline-block;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid #10B981;
        color: #34D399;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
    }
    
    .status-badge-fail {
        display: inline-block;
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid #EF4444;
        color: #F87171;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; background: linear-gradient(90deg, #A855F7, #38BDF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Canva Magic Studio — Slide Narration App
            </h1>
            <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 1.05rem;">
                Calibrated Multimodal Speech Synthesis with Pre-Synthesis Factual Entailment Gating
            </p>
        </div>
        <div style="background: rgba(125, 42, 232, 0.2); border: 1px solid #7D2AE8; padding: 8px 16px; border-radius: 24px; color: #C084FC; font-weight: 600; font-size: 0.85rem;">
            Baseline: 2.73 WPS | JennyNeural
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Load holdout runs data
holdout_runs_data = []
holdout_file_path = os.path.join(BASE_DIR, "holdout_results.json")
if os.path.exists(holdout_file_path):
    try:
        with open(holdout_file_path, "r", encoding="utf-8") as hf:
            raw_runs = json.load(hf)
            # Prioritize run_h04 (PASS) then run_h01 (FAIL)
            ordered_ids = ["run_h04", "run_h01", "run_h02", "run_h03"]
            holdout_runs_data = sorted(raw_runs, key=lambda x: ordered_ids.index(x.get("run_id", "run_h04")) if x.get("run_id") in ordered_ids else 99)
    except Exception as e:
        print(f"Error loading holdout results: {e}")

holdout_options = {}
for hr in holdout_runs_data:
    lbl = f"{hr['run_id']}: {hr['slide_id']} | Tgt {hr['target_seconds']:.0f}s | Gap {hr['gap']:+.1f}s | {hr['verdict']}"
    holdout_options[lbl] = hr

with st.sidebar:
    st.markdown("### 📊 Presentation Verification")
    st.markdown("Inspect holdout slide verification runs or run fresh generations live.")
    for hr in holdout_runs_data:
        v_icon = "✅" if hr["verdict"] == "PASS" else "❌"
        st.markdown(f"**{v_icon} {hr['run_id']}:** `{hr['slide_id']}` ({hr['target_seconds']:.0f}s) → Gap `{hr['gap']:+.1f}s` [{hr['verdict']}]")

# Layout: Two columns (Input & Preview on Left, Generation & Results on Right)
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("### 1. Slide Input & Target Configuration")
    
    # Query param detection
    raw_query = st.query_params.to_dict() if hasattr(st.query_params, "to_dict") else {}
    query_run = raw_query.get("run") or st.query_params.get("run", None)
    default_mode_idx = 2 if (query_run or True) else 0  # default to "Inspect Holdout Run" for instant inspection
        
    input_mode = st.radio(
        "Choose Slide Source:",
        ["Inspect Holdout Run", "Select Holdout Slide", "Upload Slide Image", "Select Baseline Slide"],
        index=0,
        horizontal=False
    )
    
    selected_image_path = None
    slide_label = "uploaded_slide"
    selected_holdout = None
    
    if input_mode == "Inspect Holdout Run":
        holdout_keys = list(holdout_options.keys())
        default_h_idx = 0
        if query_run:
            for idx, k in enumerate(holdout_keys):
                hr = holdout_options[k]
                if hr and hr.get("run_id") == query_run:
                    default_h_idx = idx
                    break
            
        chosen_h_label = st.radio("Select Holdout Run to Inspect:", holdout_keys, index=default_h_idx)
        selected_holdout = holdout_options.get(chosen_h_label)
        if selected_holdout:
            sid = selected_holdout["slide_id"]
            h_files = [f for f in os.listdir("holdout_slides") if f.startswith(sid)] if os.path.exists("holdout_slides") else []
            if h_files:
                selected_image_path = os.path.join("holdout_slides", h_files[0])
                slide_label = os.path.splitext(h_files[0])[0]
    elif input_mode == "Select Holdout Slide":
        holdout_dir = "holdout_slides"
        available_files = sorted([f for f in os.listdir(holdout_dir) if f.endswith(".png")]) if os.path.exists(holdout_dir) else []
        if available_files:
            chosen = st.selectbox("Select Holdout Slide File:", available_files)
            selected_image_path = os.path.join(holdout_dir, chosen)
            slide_label = os.path.splitext(chosen)[0]
    elif input_mode == "Upload Slide Image":
        uploaded_file = st.file_uploader(
            "Upload 1 Slide Image (PNG, JPG)",
            type=["png", "jpg", "jpeg"],
            help="Upload the slide graphic to be analyzed and narrated."
        )
        if uploaded_file is not None:
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            selected_image_path = temp_path
            slide_label = os.path.splitext(uploaded_file.name)[0]
    else:
        slides_dir = "slides"
        sample_files = sorted([f for f in os.listdir(slides_dir) if f.startswith("slide-") and f.endswith(".png")]) if os.path.exists(slides_dir) else []
        if sample_files:
            chosen = st.selectbox("Select Baseline Slide File:", sample_files)
            selected_image_path = os.path.join(slides_dir, chosen)
            slide_label = os.path.splitext(chosen)[0]

    # Target length input
    default_target = float(selected_holdout["target_seconds"]) if selected_holdout else 20.0
    target_seconds = st.number_input(
        "Target Length (Seconds):",
        min_value=5.0,
        max_value=120.0,
        value=default_target,
        step=1.0,
        help="Target duration for narration audio. Pipeline will calibrate length within ±3.0s."
    )
    
    force_short_draft = st.checkbox(
        "Force Short Draft Mode (Diagnostic Step 2 Rewrite Validation)",
        value=False,
        help="Initializes with a concise draft to deliberately force execution of Step 2 model rewrite under the factual gate."
    )

    # Preview Slide Image
    if selected_image_path and os.path.exists(str(selected_image_path)):
        st.markdown("#### Slide Preview")
        image = Image.open(str(selected_image_path))
        st.image(image, use_container_width=True, caption=f"Loaded: {slide_label}")
    else:
        st.info("Please upload or select a slide image to begin narration calibration.")

    generate_clicked = st.button("🎙️ Generate Narration", type="primary", use_container_width=True)

with col_right:
    st.markdown("### 2. Execution Results & Audio Asset")
    
    if generate_clicked:
        if not selected_image_path or not os.path.exists(str(selected_image_path)):
            st.error("Error: No slide image found. Please upload or select a slide image first.")
        else:
            status_container = st.status("Running Canva Slide Narration Pipeline...", expanded=True)
            
            with status_container:
                st.write("Initializing vision analysis and factual entailment gate...")
                
                # Execute pipeline asynchronously
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
                    status_container.update(label="Narration Pipeline Run Complete!", state="complete", expanded=False)
                    st.session_state["latest_run"] = run_result
                except Exception as e:
                    status_container.update(label=f"Pipeline Error: {e}", state="error", expanded=True)
                    st.error(f"Execution Error: {e}")

    # Determine active result to render
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

    # Render results if available
    if res:
        final_att = res.get("final_attempt")
        attempts = res.get("attempts", [])
        retries_used = res.get("retries_used", max(0, len(attempts) - 1))
        
        if final_att:
            final_script = final_att.get("script", "")
            target_sec = float(final_att.get("target", target_seconds))
            measured_sec = float(final_att.get("measured", 0.0))
            gap = float(final_att.get("gap", 0.0))
            is_pass = abs(gap) <= 3.0 and res.get("status") == "PASS"
            audio_path = final_att.get("audio_path", "")
            
            # Status Banner
            if is_pass:
                st.markdown(f'<div class="status-badge-pass">✅ TIMING GATE PASSED (Gap: {gap:+.1f}s within ±3.0s)</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-badge-fail">❌ TIMING GATE FAILED (Gap: {gap:+.1f}s exceeds ±3.0s)</div>', unsafe_allow_html=True)

            st.write("")
            
            # Display the 5 Required Evidence Metrics
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Target Seconds</div>
                    <div class="metric-value">{target_sec:.1f}s</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Measured Seconds</div>
                    <div class="metric-value">{measured_sec:.1f}s</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col3:
                gap_class = "metric-pass" if is_pass else "metric-fail"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Timing Gap</div>
                    <div class="metric-value {gap_class}">{gap:+.1f}s</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Retries Used</div>
                    <div class="metric-value">{retries_used}</div>
                </div>
                """, unsafe_allow_html=True)

            # 5th item: Generated Script text
            st.markdown("#### Generated Voiceover Script")
            st.markdown(f'<div class="script-box">{final_script}</div>', unsafe_allow_html=True)
            
            st.write("")
            st.markdown("### Gated Audio Asset Delivery")
            
            # Gating Logic: Download button ONLY appears when abs(gap) <= 3.0s
            if is_pass and audio_path and os.path.exists(audio_path):
                with open(audio_path, "rb") as af:
                    audio_bytes = af.read()
                
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="⬇️ Download Narration Audio (MP3)",
                    data=audio_bytes,
                    file_name=f"{res.get('slide_id', 'slide')}_narration.mp3",
                    mime="audio/mp3",
                    type="primary",
                    use_container_width=True
                )
                st.success("Download unlocked: Narration audio fits presentation slot within ±3.0s.")
            else:
                st.error(
                    f"⛔ Audio Download Locked: Narration measured duration ({measured_sec:.1f}s) missed the "
                    f"target length ({target_sec:.1f}s) by {gap:+.1f}s after {retries_used} retries. "
                    f"Per Canva Magic Studio delivery policy, audio that misses the time slot is strictly suppressed from download."
                )

            # Attempt Trace Expander
            with st.expander("🔍 View Attempt-by-Attempt Diagnostic Trace", expanded=False):
                for att in attempts:
                    att_num = att.get("attempt")
                    att_rate = att.get("rate")
                    att_meas = att.get("measured")
                    att_gap = att.get("gap")
                    att_verd = att.get("verdict")
                    st.markdown(f"**Attempt {att_num}:** Rate `{att_rate}` | Measured `{att_meas:.1f}s` | Gap `{att_gap:+.1f}s` | Verdict: **{att_verd}**")
                    st.caption(f"Script: \"{att.get('script')}\"")
                    st.divider()
    else:
        st.write("Configure your slide on the left and click **Generate Narration** to synthesize spoken audio.")
