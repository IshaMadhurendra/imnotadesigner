import io
import os
import time
import httpx
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from streamlit_drawable_canvas import st_canvas

load_dotenv()

MAX_PIXELS = 9_000_000


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
    try:
        return st.secrets["STABILITY_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("STABILITY_API_KEY", "")


DEFAULT_NEGATIVE = "human, person, model, mannequin, body, face, hands, fingers, people, figure, torso, legs, arms, extra fabric, extended design, additional elements beyond the sketch"


def call_stability_api(sketch_bytes: bytes, prompt: str, control_strength: float,
                       output_format: str, negative_prompt: str, seed: int, api_key: str):
    """Call Stability AI sketch endpoint. Returns (Image, None) or (None, error_str)."""
    # Always enforce: only render what's in the sketch
    full_prompt = prompt + ", isolated product only, render exactly what is shown in the sketch, nothing more, no background scene, no human model"

    # Combine user negative prompt with defaults
    full_negative = DEFAULT_NEGATIVE
    if negative_prompt:
        full_negative = negative_prompt + ", " + DEFAULT_NEGATIVE

    form_data = {
        "prompt": (None, full_prompt),
        "control_strength": (None, str(control_strength)),
        "output_format": (None, output_format),
        "image": ("sketch.png", sketch_bytes, "image/png"),
        "negative_prompt": (None, full_negative),
    }
    if seed > 0:
        form_data["seed"] = (None, str(seed))

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
        return Image.open(io.BytesIO(response.content)), None
    else:
        try:
            err = response.json()
        except Exception:
            err = response.text
        return None, f"API error ({response.status_code}): {err}"


# --- Page Config ---
st.set_page_config(
    page_title="i'mnotadesigner",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #fafaf8;
}
#MainMenu, footer, header, .stDeployButton {display: none !important; visibility: hidden !important;}

.app-header {
    padding: 2.5rem 0 1.5rem;
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
}
.divider {
    width: 40px;
    height: 2px;
    background: #e0ddd5;
    margin: 1.2rem auto 0;
    border-radius: 1px;
}

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

.stButton > button[kind="primary"] {
    background: #1a1a1a !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: #333 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}

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

.stCheckbox label {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    color: #555 !important;
}
.stSlider label { font-size: 0.8rem !important; color: #777 !important; }
.stRadio label { font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; }

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

.stImage > img {
    border-radius: 8px;
    border: 1px solid #e8e6e0;
}
.stStatus {
    border: 1px solid #e8e6e0 !important;
    border-radius: 10px !important;
    background: #fff !important;
}
.canvas-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e0ddd5;
    background: #fff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stNumberInput input {
    background: #fff !important;
    border: 1px solid #e0ddd5 !important;
    border-radius: 6px !important;
    color: #1a1a1a !important;
}
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
.empty-state .pencil { font-size: 2rem; margin-bottom: 1rem; opacity: 0.4; }
.empty-state p { color: #aaa; font-size: 0.85rem; margin: 0.15rem 0; }
.empty-state .steps {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #ccc;
    margin-top: 1rem;
}
.stCaption { font-size: 0.75rem !important; color: #999 !important; }
[data-testid="stHorizontalBlock"] { gap: 1.5rem; }

/* Variation grid */
.var-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #999;
    text-align: center;
    margin-top: 0.3rem;
}
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
if "rendered_variations" not in st.session_state:
    st.session_state.rendered_variations = None
if "sketch_image" not in st.session_state:
    st.session_state.sketch_image = None

# --- Material Presets (Industrial Design focused) ---
MATERIAL_PRESETS = {
    "Matte Black": ", matte black finish, soft-touch coating, no reflections",
    "Brushed Aluminum": ", brushed aluminum surface, subtle metallic grain, industrial",
    "Anodized Metal": ", anodized aluminum, vibrant color finish, smooth surface",
    "Injection Molded": ", injection-molded plastic, subtle parting lines, mass-produced look",
    "Carbon Fiber": ", carbon fiber weave pattern, lightweight aerospace material",
    "Polished Chrome": ", mirror-polished chrome, highly reflective, premium",
    "Natural Wood": ", natural wood grain, warm walnut or oak, organic",
    "Leather": ", premium leather, fine stitching, tactile texture",
    "Frosted Glass": ", frosted translucent glass, diffused light, elegant",
    "Concrete": ", raw concrete, brutalist, industrial texture",
    "Ceramic": ", glazed white ceramic, smooth, minimalist",
    "Fabric/Mesh": ", woven fabric mesh, breathable textile, soft",
}

LIGHTING_PRESETS = {
    "Studio": ", professional studio lighting, soft diffused shadows, neutral background",
    "Dramatic": ", dramatic side lighting, deep shadows, moody atmosphere",
    "Natural": ", warm natural daylight, golden hour, outdoor setting",
    "Product Shot": ", product photography, pure white background, commercial grade",
    "Environment": ", in-context lifestyle setting, real-world environment",
    "Blueprint": ", technical rendering, orthographic view, engineering style",
}



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
            truncated = item['prompt'][:40] + ("..." if len(item['prompt']) > 40 else "")
            if st.button(f"{truncated}", key=f"hist_{i}"):
                st.session_state.rendered_image = item["image"]
                st.session_state.sketch_image = item["sketch"]
                st.session_state.rendered_variations = None

# --- Main Layout ---
left_col, right_col = st.columns([1.15, 1], gap="large")

with left_col:
    st.markdown('<p class="section-label">Sketch</p>', unsafe_allow_html=True)

    input_mode = st.radio("mode", ["Draw", "Upload"], horizontal=True, label_visibility="collapsed")

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
            # Composite onto white (the template is just a guide)
            white_bg = Image.new("RGB", sketch_img.size, "white")
            white_bg.paste(sketch_img, mask=sketch_img.split()[3])
            st.session_state.sketch_image = resize_for_api(white_bg)
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
        placeholder="What should this become?\ne.g. 'wireless over-ear headphones, premium consumer electronics product'",
        label_visibility="collapsed",
        height=80,
    )

    # --- Material Presets ---
    st.markdown('<p class="section-label">Material</p>', unsafe_allow_html=True)
    mat_cols = st.columns(4)
    selected_materials = []
    for i, (name, suffix) in enumerate(MATERIAL_PRESETS.items()):
        with mat_cols[i % 4]:
            if st.checkbox(name, key=f"mat_{name}"):
                selected_materials.append(suffix)

    # --- Lighting Presets ---
    st.markdown('<p class="section-label">Lighting & Context</p>', unsafe_allow_html=True)
    light_cols = st.columns(3)
    selected_lighting = []
    for i, (name, suffix) in enumerate(LIGHTING_PRESETS.items()):
        with light_cols[i % 3]:
            if st.checkbox(name, key=f"light_{name}"):
                selected_lighting.append(suffix)

    # --- Render Buttons ---
    st.markdown("")
    btn_cols = st.columns([2, 1])
    with btn_cols[0]:
        render_clicked = st.button("Generate", type="primary", use_container_width=True)
    with btn_cols[1]:
        variations_clicked = st.button("4 Variations", use_container_width=True,
                                       help="Generate 4 different material/lighting combos")


with right_col:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)

    # Single render
    if render_clicked:
        if not prompt.strip():
            st.info("Add a prompt describing what you'd like the sketch to become.")
        elif st.session_state.sketch_image is None:
            st.info("Draw or upload a sketch first.")
        else:
            full_prompt = prompt.strip() + "".join(selected_materials) + "".join(selected_lighting)

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
                    st.write("Rendering materials & lighting...")

                    img, err = call_stability_api(
                        sketch_bytes, full_prompt, control_strength,
                        output_format, negative_prompt, seed, api_key
                    )

                    if img:
                        status.update(label="Complete", state="complete")
                        st.session_state.rendered_image = img
                        st.session_state.rendered_variations = None
                        st.session_state.history.insert(0, {
                            "image": img,
                            "sketch": st.session_state.sketch_image,
                            "prompt": full_prompt,
                        })
                        st.session_state.history = st.session_state.history[:10]
                    else:
                        status.update(label="Failed", state="error")
                        st.error(err)

    # Batch variations
    if variations_clicked:
        if not prompt.strip():
            st.info("Add a prompt first.")
        elif st.session_state.sketch_image is None:
            st.info("Draw or upload a sketch first.")
        else:
            api_key = get_api_key()
            if not api_key or api_key == "your_key_here":
                st.error("Add your STABILITY_API_KEY to the .env file.")
            else:
                buf = io.BytesIO()
                st.session_state.sketch_image.save(buf, format="PNG")
                sketch_bytes = buf.getvalue()

                # 4 different material/lighting combos
                variation_prompts = [
                    (prompt.strip() + ", matte black finish, studio lighting, soft shadows", "Matte + Studio"),
                    (prompt.strip() + ", brushed aluminum, natural daylight, warm tones", "Aluminum + Natural"),
                    (prompt.strip() + ", glossy white ceramic, product photography, white background", "Ceramic + Product"),
                    (prompt.strip() + ", carbon fiber weave, dramatic side lighting, dark background", "Carbon + Dramatic"),
                ]

                with st.status("Generating 4 variations...", expanded=True) as status:
                    results = []
                    for i, (var_prompt, label) in enumerate(variation_prompts):
                        st.write(f"Rendering variation {i+1}/4: {label}...")
                        img, err = call_stability_api(
                            sketch_bytes, var_prompt, control_strength,
                            output_format, negative_prompt, 0, api_key
                        )
                        results.append((img, label, err))

                    successful = [(img, label) for img, label, err in results if img is not None]
                    if successful:
                        status.update(label=f"{len(successful)}/4 complete", state="complete")
                        st.session_state.rendered_variations = successful
                        st.session_state.rendered_image = successful[0][0]
                    else:
                        status.update(label="Failed", state="error")
                        st.error("All variations failed. Check your prompt or API key.")

    # Display results
    if st.session_state.rendered_variations:
        st.markdown('<p class="section-label">Variations</p>', unsafe_allow_html=True)
        var_cols = st.columns(2)
        for i, (img, label) in enumerate(st.session_state.rendered_variations):
            with var_cols[i % 2]:
                st.image(img, use_container_width=True)
                st.markdown(f'<p class="var-label">{label}</p>', unsafe_allow_html=True)
                if st.button(f"Use this", key=f"var_{i}"):
                    st.session_state.rendered_image = img
                    st.session_state.rendered_variations = None

    elif st.session_state.rendered_image is not None:
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
