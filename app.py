import io
import os
import time

import httpx
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from streamlit_drawable_canvas import st_canvas

load_dotenv()

MAX_PIXELS = 9_000_000  # Stability AI limit is 9,437,184


def resize_for_api(img: Image.Image) -> Image.Image:
    """Resize image if it exceeds the Stability AI pixel limit."""
    w, h = img.size
    if w * h <= MAX_PIXELS:
        return img
    scale = (MAX_PIXELS / (w * h)) ** 0.5
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


def get_api_key():
    """Get API key from Streamlit secrets (cloud) or .env (local)."""
    try:
        return st.secrets["STABILITY_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("STABILITY_API_KEY", "")


st.set_page_config(
    page_title="i'mnotadesigner",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Minimal, warm, classy CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Söhne,ui-monospace,Menlo,Monaco,monospace&family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #fafaf8;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton {display: none !important; visibility: hidden !important;}

/* === HEADER === */
.app-header {
    padding: 3rem 0 2rem;
    text-align: center;
}
.app-header h1 {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0;
    letter-spacing: -0.02em;
}
.app-header .tagline {
    font-family: 'IBM Plex Mono', monospace;
    color: #888;
    font-size: 0.82rem;
    margin-top: 0.5rem;
    letter-spacing: 0.01em;
}
.divider {
    width: 40px;
    height: 2px;
    background: #e0ddd5;
    margin: 1.5rem auto 0;
    border-radius: 1px;
}

/* === SECTION LABELS === */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #999;
    margin-bottom: 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #eee;
}

/* === RENDER BUTTON === */
.stButton > button[kind="primary"] {
    background: #1a1a1a !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #333 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}

/* === SECONDARY / DOWNLOAD BUTTONS === */
.stButton > button:not([kind="primary"]),
.stDownloadButton > button {
    background: #fff !important;
    border: 1px solid #e0ddd5 !important;
    border-radius: 8px !important;
    color: #444 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
}
.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:hover {
    border-color: #bbb !important;
    background: #f5f5f2 !important;
}

/* === TEXT INPUTS === */
.stTextArea textarea, .stTextInput input {
    background: #fff !important;
    border: 1px solid #e0ddd5 !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    line-height: 1.5 !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #999 !important;
    box-shadow: none !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
    color: #bbb !important;
}

/* === CHECKBOX === */
.stCheckbox label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    color: #555 !important;
}
.stCheckbox label span[data-testid="stCheckboxLabel"] {
    font-weight: 400;
}

/* === SLIDER === */
.stSlider label { font-size: 0.8rem !important; color: #777 !important; }

/* === RADIO === */
.stRadio label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
}

/* === SIDEBAR === */
section[data-testid="stSidebar"] {
    background: #f5f4f0;
    border-right: 1px solid #e8e6e0;
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'IBM Plex Mono', monospace;
    color: #555;
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 1rem;
}

/* === IMAGES === */
.stImage > img {
    border-radius: 8px;
    border: 1px solid #e8e6e0;
}

/* === STATUS === */
.stStatus {
    border: 1px solid #e8e6e0 !important;
    border-radius: 10px !important;
    background: #fff !important;
}

/* === CANVAS === */
.canvas-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e0ddd5;
    background: #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* === FILE UPLOADER === */
section[data-testid="stFileUploader"] {
    border-radius: 10px !important;
}

/* === NUMBER INPUT === */
.stNumberInput input {
    background: #fff !important;
    border: 1px solid #e0ddd5 !important;
    border-radius: 6px !important;
    color: #1a1a1a !important;
}

/* === EMPTY STATE === */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 420px;
    border: 1px dashed #ddd;
    border-radius: 12px;
    background: #fff;
}
.empty-state .pencil {
    font-size: 2rem;
    margin-bottom: 1rem;
    opacity: 0.4;
}
.empty-state p {
    color: #aaa;
    font-size: 0.85rem;
    margin: 0.15rem 0;
}
.empty-state .steps {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #ccc;
    margin-top: 1rem;
    letter-spacing: 0.03em;
}

/* === CAPTION === */
.stCaption { font-size: 0.75rem !important; color: #999 !important; }

/* === COLUMN GAP FIX === */
[data-testid="stHorizontalBlock"] { gap: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="app-header">
    <h1>i'mnotadesigner</h1>
    <p class="tagline">sketch it rough — we'll handle the rest</p>
    <div class="divider"></div>
</div>
""", unsafe_allow_html=True)

# --- Session State ---
if "history" not in st.session_state:
    st.session_state.history = []
if "rendered_image" not in st.session_state:
    st.session_state.rendered_image = None
if "sketch_image" not in st.session_state:
    st.session_state.sketch_image = None

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Settings")

    st.markdown('<p class="section-label">Sketch Fidelity</p>', unsafe_allow_html=True)
    control_strength = st.slider(
        "fidelity", min_value=0.0, max_value=1.0, value=0.7, step=0.05,
        help="Higher = output follows your sketch lines more closely",
        label_visibility="collapsed",
    )

    st.markdown('<p class="section-label">Format</p>', unsafe_allow_html=True)
    output_format = st.radio(
        "format", ["webp", "png", "jpeg"],
        horizontal=True, label_visibility="collapsed",
    )

    st.markdown('<p class="section-label">Seed</p>', unsafe_allow_html=True)
    seed = st.number_input(
        "seed", min_value=0, max_value=4294967294, value=0,
        help="0 = random. Use a fixed number to reproduce results.",
        label_visibility="collapsed",
    )

    st.markdown('<p class="section-label">Exclude</p>', unsafe_allow_html=True)
    negative_prompt = st.text_input(
        "neg", placeholder="blurry, distorted, low quality...",
        label_visibility="collapsed",
    )

    if st.session_state.history:
        st.markdown("---")
        st.markdown("### History")
        for i, item in enumerate(st.session_state.history[:5]):
            truncated = item['prompt'][:45] + ("..." if len(item['prompt']) > 45 else "")
            if st.button(f"{truncated}", key=f"hist_{i}"):
                st.session_state.rendered_image = item["image"]
                st.session_state.sketch_image = item["sketch"]

# --- Style Presets ---
STYLE_PRESETS = {
    "Studio Light": ", professional studio lighting, soft shadows",
    "Matte": ", matte material finish, no reflections",
    "Chrome": ", glossy chrome finish, reflective surface",
    "Wood": ", natural wood material, warm tones",
    "Glass": ", transparent glass material, refractive",
    "Concrete": ", raw concrete, brutalist aesthetic",
    "Neon": ", neon edge lighting, vibrant glow",
    "Product Shot": ", product photography, white background, commercial",
}

# --- Main Layout ---
left_col, right_col = st.columns([1.15, 1], gap="large")

with left_col:
    # --- Sketch Input ---
    st.markdown('<p class="section-label">Sketch</p>', unsafe_allow_html=True)

    input_mode = st.radio(
        "mode", ["Draw", "Upload"],
        horizontal=True, label_visibility="collapsed",
    )

    if input_mode == "Draw":
        tool_cols = st.columns([1.5, 0.7, 1.3])
        with tool_cols[0]:
            stroke_width = st.slider("Brush", 1, 20, 3, label_visibility="collapsed")
        with tool_cols[1]:
            stroke_color = st.color_picker("", "#1a1a1a", label_visibility="collapsed")
        with tool_cols[2]:
            drawing_mode = st.selectbox(
                "tool", ["freedraw", "line", "rect", "circle"],
                label_visibility="collapsed",
            )

        st.markdown('<div class="canvas-wrap">', unsafe_allow_html=True)
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color="#FFFFFF",
            height=460,
            width=460,
            drawing_mode=drawing_mode,
            key="sketch_canvas",
            display_toolbar=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        if canvas_result.image_data is not None:
            sketch_img = Image.fromarray(canvas_result.image_data.astype("uint8"), "RGBA")
            sketch_img = sketch_img.convert("RGB")
            st.session_state.sketch_image = resize_for_api(sketch_img)
    else:
        uploaded_file = st.file_uploader(
            "Drop a sketch here — PNG, JPG, WEBP",
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed",
        )
        if uploaded_file:
            sketch_img = Image.open(uploaded_file).convert("RGB")
            st.session_state.sketch_image = resize_for_api(sketch_img)
            st.image(sketch_img, use_container_width=True)

    # --- Prompt ---
    st.markdown("")
    st.markdown('<p class="section-label">Prompt</p>', unsafe_allow_html=True)
    prompt = st.text_area(
        "prompt",
        placeholder="What should this become?\ne.g. 'matte black wireless headphones, brushed aluminum accents, studio lighting'",
        label_visibility="collapsed",
        height=80,
    )

    # --- Style Presets ---
    st.markdown('<p class="section-label">Style</p>', unsafe_allow_html=True)
    preset_cols = st.columns(4)
    selected_presets = []
    for i, (name, suffix) in enumerate(STYLE_PRESETS.items()):
        with preset_cols[i % 4]:
            if st.checkbox(name, key=f"p_{name}"):
                selected_presets.append(suffix)

    # --- Render Button ---
    st.markdown("")
    render_clicked = st.button("Generate", type="primary", use_container_width=True)


with right_col:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)

    if render_clicked:
        if not prompt.strip():
            st.info("Add a prompt describing what you'd like the sketch to become.")
        elif st.session_state.sketch_image is None:
            st.info("Draw or upload a sketch first.")
        else:
            full_prompt = prompt.strip() + "".join(selected_presets)

            buf = io.BytesIO()
            st.session_state.sketch_image.save(buf, format="PNG")
            sketch_bytes = buf.getvalue()

            api_key = get_api_key()
            if not api_key or api_key == "your_key_here":
                st.error("Add your STABILITY_API_KEY to the .env file.")
            else:
                with st.status("Generating...", expanded=True) as status:
                    st.write("Uploading sketch...")
                    time.sleep(0.3)
                    st.write("Analyzing geometry...")

                    form_data = {
                        "prompt": (None, full_prompt),
                        "control_strength": (None, str(control_strength)),
                        "output_format": (None, output_format),
                        "image": ("sketch.png", sketch_bytes, "image/png"),
                    }
                    if negative_prompt:
                        form_data["negative_prompt"] = (None, negative_prompt)
                    if seed > 0:
                        form_data["seed"] = (None, str(seed))

                    try:
                        st.write("Rendering materials & lighting...")
                        with httpx.Client(timeout=60.0) as client:
                            response = client.post(
                                "https://api.stability.ai/v2beta/stable-image/control/sketch",
                                headers={
                                    "authorization": f"Bearer {api_key}",
                                    "accept": "image/*",
                                },
                                files=form_data,
                            )

                        if response.status_code == 200:
                            status.update(label="Complete", state="complete")
                            rendered_img = Image.open(io.BytesIO(response.content))
                            st.session_state.rendered_image = rendered_img
                            st.session_state.history.insert(0, {
                                "image": rendered_img,
                                "sketch": st.session_state.sketch_image,
                                "prompt": full_prompt,
                            })
                            st.session_state.history = st.session_state.history[:10]
                        else:
                            status.update(label="Failed", state="error")
                            try:
                                err = response.json()
                            except Exception:
                                err = response.text
                            st.error(f"API error ({response.status_code}): {err}")

                    except httpx.TimeoutException:
                        status.update(label="Timeout", state="error")
                        st.error("Timed out — please try again.")
                    except Exception as e:
                        status.update(label="Error", state="error")
                        st.error(f"{e}")

    # Display
    if st.session_state.rendered_image is not None:
        view = st.radio(
            "view", ["Render", "Compare", "Sketch"],
            horizontal=True, label_visibility="collapsed",
        )

        if view == "Compare" and st.session_state.sketch_image:
            c1, c2 = st.columns(2)
            with c1:
                st.image(st.session_state.sketch_image, caption="Sketch", use_container_width=True)
            with c2:
                st.image(st.session_state.rendered_image, caption="Render", use_container_width=True)
        elif view == "Sketch" and st.session_state.sketch_image:
            st.image(st.session_state.sketch_image, caption="Sketch", use_container_width=True)
        else:
            st.image(st.session_state.rendered_image, use_container_width=True)

        st.markdown("")
        dl_buf = io.BytesIO()
        st.session_state.rendered_image.save(dl_buf, format="PNG")
        st.download_button(
            label="Download",
            data=dl_buf.getvalue(),
            file_name=f"imnotadesigner-{int(time.time())}.png",
            mime="image/png",
            use_container_width=True,
        )
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="pencil">✏️</div>
            <p>Your render will appear here</p>
            <p>It's okay if your sketch is bad. That's the point.</p>
            <p class="steps">sketch → prompt → generate</p>
        </div>
        """, unsafe_allow_html=True)
