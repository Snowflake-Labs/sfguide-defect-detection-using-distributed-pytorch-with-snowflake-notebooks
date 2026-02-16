"""
PCB Defect Detection - About Page

Comprehensive documentation for dual audiences:
- Executive Overview: Business context, outcomes, value
- Technical Deep-Dive: Architecture, algorithms, implementation
"""

import streamlit as st
from utils import render_svg

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="About | PCB Defect Detection",
    layout="wide"
)

# Dark theme styling
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
    }
    /* Global text visibility */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp li {
        color: #f1f5f9 !important;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #f8fafc !important;
    }
    .stMarkdown, .stMarkdown p, .stText {
        color: #e2e8f0 !important;
    }
    /* Links */
    a, .stMarkdown a {
        color: #64D2FF !important;
    }
    /* Bold/Strong text */
    strong, b {
        color: #f8fafc !important;
    }
    /* Italic/Emphasis */
    em, i {
        color: #e2e8f0 !important;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    /* Dividers */
    hr, [data-testid="stDivider"] {
        border-color: #334155 !important;
        background-color: #334155 !important;
    }
    /* Tables */
    table {
        background-color: #1e293b !important;
        border-collapse: collapse;
    }
    th {
        background-color: #334155 !important;
        color: #f8fafc !important;
        padding: 0.5rem !important;
        border: 1px solid #475569 !important;
    }
    td {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        padding: 0.5rem !important;
        border: 1px solid #475569 !important;
    }
    /* Streamlit dataframe/table */
    [data-testid="stTable"] th {
        background-color: #334155 !important;
        color: #f8fafc !important;
    }
    [data-testid="stTable"] td {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #4ade80 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #f8fafc !important;
    }
    [data-testid="stMetricDelta"] {
        color: #94a3b8 !important;
    }
    /* Code blocks */
    pre, code, .stCodeBlock, [data-testid="stCodeBlock"] {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    p code, li code {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        padding: 0.125rem 0.375rem;
        border-radius: 4px;
    }
    .tech-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
        background-color: #1e40af;
        color: white !important;
    }
    .tech-badge-external {
        background-color: #b45309;
    }
    .tech-badge-model {
        background-color: #166534;
    }
    .tech-badge-stage {
        background-color: #7c3aed;
    }
    .arch-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .arch-card h4, .arch-card p, .arch-card strong {
        color: #e2e8f0 !important;
    }
    .value-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #22c55e;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .value-card h2, .value-card p {
        color: #f8fafc !important;
    }
    .problem-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 1rem;
    }
    .problem-card h4 {
        color: #f87171 !important;
    }
    .problem-card p {
        color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    render_svg("images/logo.svg", width=150)
    st.title("PCB Defect Detection")
    st.markdown("---")
    st.markdown("""
    **Quick Links**
    - [Overview](#overview)
    - [Data Architecture](#data-architecture)
    - [Executive Overview](#executive-overview)
    - [Technical Deep-Dive](#technical-deep-dive)
    - [Technology Stack](#technology-stack)
    """)

# =============================================================================
# HEADER
# =============================================================================

st.title("About This Application")
st.markdown("*AI-powered PCB defect detection using YOLOv12 on Snowflake Container Runtime*")

st.divider()

# =============================================================================
# OVERVIEW SECTION (Problem + Solution)
# =============================================================================

st.header("Overview")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("The Problem")
    st.markdown("""
    Electronics manufacturers face a critical quality control challenge: **legacy AOI (Automated Optical 
    Inspection) systems generate excessive false positives**, flagging 15-25% of boards as defective when 
    they're actually fine.
    
    This creates a cascade of problems:
    - **Expensive manual re-inspection** slows production and inflates labor costs
    - **Data silos** prevent ML teams from accessing factory floor images to train better models
    - **Security policies** block modern open-source AI from running inside the corporate firewall
    - **Reactive quality control** catches defects too late, after boards have moved through expensive downstream operations
    
    **The cost?** Poor quality costs electronics manufacturers 2-4% of annual revenue—that's $200-400M 
    for a $10B operation (McKinsey).
    """)

with col2:
    st.subheader("The Solution")
    st.markdown("""
    **Train custom YOLOv12 models directly inside Snowflake** using GPU compute—keeping sensitive 
    factory images secure while leveraging state-of-the-art computer vision.
    
    **Key Capabilities:**
    - GPU-accelerated training in Snowflake Notebooks
    - 6 defect class detection (open, short, mousebite, spur, copper, pin-hole)
    - Ground truth vs. inference comparison
    - Interactive Vision Lab for image analysis
    - Live analytics dashboard with confidence metrics
    """)

st.divider()

# =============================================================================
# DATA ARCHITECTURE
# =============================================================================

st.header("Data Architecture")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">Internal Data</h4>
        <span class="tech-badge">PCB_METADATA</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            Board identification, manufacturing date, factory line, product type.<br/>
            <strong>~1M records</strong> | <strong>Refresh:</strong> Real-time
        </p>
        <span class="tech-badge">DEFECT_LOGS</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            Inference results with class, confidence, bounding box coordinates.<br/>
            <strong>~30K records</strong> | <strong>Refresh:</strong> Per-inference
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">External Data</h4>
        <span class="tech-badge tech-badge-external">Deep PCB Dataset</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            Open-source PCB defect dataset with 1,500 image pairs and 6 defect classes.<br/>
            <strong>MIT License</strong> | <strong>Source:</strong> Tang et al. 2019
        </p>
        <span class="tech-badge tech-badge-external">PCB_LABELED_DATA</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            Ground truth labels in YOLO format for training validation and comparison.<br/>
            <strong>Format:</strong> class_id x_center y_center width height
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">Model Outputs</h4>
        <span class="tech-badge tech-badge-model">Model Registry</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            YOLO_PCB_DEFECT_DETECTOR logged for versioning and SQL inference.<br/>
            <strong>~15MB</strong> | <strong>Target:</strong> SPCS
        </p>
        <span class="tech-badge tech-badge-stage">MODEL_STAGE</span><br/>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem;">
            Backup weights at @MODEL_STAGE/models/yolov12_pcb/yolo_best.pt<br/>
            <strong>~500MB total</strong> | <strong>Location:</strong> @MODEL_STAGE/
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# EXECUTIVE OVERVIEW
# =============================================================================

st.header("Executive Overview")

st.markdown("### Why Traditional Approaches Fall Short")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="problem-card">
        <h4 style="color: #f87171;">Legacy AOI Systems</h4>
        <p style="color: #94a3b8;">
        Rigid rule-based inspection that cannot adapt to new products or learn from production reality.
        Results in 15-25% false positive rates.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="problem-card">
        <h4 style="color: #f87171;">Data Silos</h4>
        <p style="color: #94a3b8;">
        Factory images trapped in legacy systems. Data scientists cannot access the data needed to 
        train modern AI models.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="problem-card">
        <h4 style="color: #f87171;">Security Barriers</h4>
        <p style="color: #94a3b8;">
        Corporate policies block GPU infrastructure and open-source ML frameworks from running 
        inside the firewall.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("### How This Solution Works")
st.markdown("""
Think of this solution as **bringing the AI to the data, not the data to the AI**.

Instead of moving sensitive factory images to external cloud ML platforms, we train custom 
detection models directly inside Snowflake—where your data already lives, governed by your 
existing security policies.

**The AI learns what defects really look like** on your production boards, not generic samples. 
The Vision Lab lets you compare model predictions against ground truth labels to validate 
detection accuracy before deployment.

**What you get:**
- A model trained specifically on YOUR production data
- Detection accuracy that improves as you add more examples
- Real-time visibility into quality across all production lines
- Interactive analysis with confidence thresholds and ground truth comparison
""")

st.markdown("### Business Value")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="value-card">
        <h2 style="color: #4ade80; margin: 0;">25%</h2>
        <p style="color: #f8fafc; margin: 0.5rem 0 0 0; font-weight: 600;">Fewer False Positives</p>
        <p style="color: #94a3b8; margin: 0; font-size: 0.8rem;">Custom models vs. legacy AOI</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="value-card">
        <h2 style="color: #4ade80; margin: 0;">15%</h2>
        <p style="color: #f8fafc; margin: 0.5rem 0 0 0; font-weight: 600;">Scrap Reduction</p>
        <p style="color: #94a3b8; margin: 0; font-size: 0.8rem;">Earlier, more accurate detection</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="value-card">
        <h2 style="color: #4ade80; margin: 0;">&lt;2s</h2>
        <p style="color: #f8fafc; margin: 0.5rem 0 0 0; font-weight: 600;">Inference Time</p>
        <p style="color: #94a3b8; margin: 0; font-size: 0.8rem;">Real-time defect detection</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="value-card">
        <h2 style="color: #4ade80; margin: 0;">$1.1M</h2>
        <p style="color: #f8fafc; margin: 0.5rem 0 0 0; font-weight: 600;">Annual Value</p>
        <p style="color: #94a3b8; margin: 0; font-size: 0.8rem;">For 1M boards/year operation</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# TECHNICAL DEEP-DIVE
# =============================================================================

st.header("Technical Deep-Dive")

st.markdown("### Architecture Overview")

st.markdown("""
The solution follows a **data-centric architecture** where sensitive manufacturing images never 
leave the Snowflake security perimeter. The pipeline has four main stages:

1. **Data Ingestion**: PCB images from the Deep PCB dataset are cached in `@MODEL_STAGE/raw/deeppcb/` 
   for training and inference. In production, this would be replaced with factory floor image feeds.

2. **Model Training**: A Snowflake Notebook running on Container Runtime with GPU compute 
   (GPU_NV_M pool) trains YOLOv12 directly on the staged images. External access integrations 
   enable PyPI, GitHub, and HuggingFace connectivity for package installation.

3. **Artifact Storage**: Trained model weights (`best.pt`) are persisted to `@MODEL_STAGE/models/`, 
   while inference results are written to the `DEFECT_LOGS` table with bounding box coordinates 
   and confidence scores.

4. **Visualization Layer**: This Streamlit dashboard queries `DEFECT_LOGS` and `PCB_METADATA` 
   tables to render real-time analytics, while the Vision Lab provides interactive image analysis.
""")

# Display architecture diagram
render_svg("images/architecture.svg", caption="Solution Architecture", border=True)

st.markdown("### Model Architecture: YOLOv12")

st.markdown("""
We use **YOLOv12** (You Only Look Once v12), an attention-centric real-time object detector 
that achieves state-of-the-art accuracy while maintaining fast inference.

**Key architectural innovations:**
- **Area Attention Module**: Efficient attention mechanism for capturing global context
- **R-ELAN Block**: Reparameterized ELAN for improved gradient flow
- **Anchor-free Detection**: No predefined anchor boxes, enabling better generalization
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Training Configuration:**
    | Parameter | Value |
    |-----------|-------|
    | Model | YOLOv12n (nano) |
    | Input Size | 640 x 640 |
    | Epochs | 10 (demo) / 50+ (prod) |
    | Batch Size | 16 |
    | Optimizer | SGD |
    | Learning Rate | 0.01 |
    | Compute | GPU_NV_M |
    """)

with col2:
    st.markdown("""
    **Defect Classes:**
    | Class ID | Defect Type |
    |----------|-------------|
    | 0 | Open (broken trace) |
    | 1 | Short (unintended connection) |
    | 2 | Mousebite (irregular edge) |
    | 3 | Spur (unwanted protrusion) |
    | 4 | Copper (excess copper) |
    | 5 | Pin-hole (small void) |
    """)

st.markdown("### Data Pipeline")

st.markdown("""
The notebook implements a **hybrid data loading** strategy with stage caching:

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  Check Stage Cache   │ ──► │  Download from Stage │ ──► │  Process to YOLO     │
│  @MODEL_STAGE/raw/   │     │  (if cached)         │     │  Format              │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
         │ (empty)                                                  │
         ▼                                                          ▼
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│  Git Sparse Clone    │ ──► │  Cache to Stage      │ ──► │  PCB_LABELED_DATA    │
│  from GitHub         │     │  for future runs     │     │  Table (base64 imgs) │
└──────────────────────┘     └──────────────────────┘     └──────────────────────┘
```

**Data Format Conversion (Deep PCB → YOLO):**
- **Deep PCB format**: `x1 y1 x2 y2 class_id` (absolute pixel coordinates)
- **YOLO format**: `class_id x_center y_center width height` (normalized 0-1)

**Normalization Formulas:**
```
x_center = (x1 + x2) / (2 * image_width)
y_center = (y1 + y2) / (2 * image_height)
width = (x2 - x1) / image_width
height = (y2 - y1) / image_height
```
""")

st.markdown("### Distributed Training")

st.markdown("""
Training uses Snowflake's **PyTorchDistributor** for GPU-accelerated model training:

```python
distributor = PyTorchDistributor(
    train_func=train_func_yolo,
    scaling_config=PyTorchScalingConfig(
        num_nodes=1,
        num_workers_per_node=1,
        resource_requirements_per_worker=WorkerResourceConfig(
            num_cpus=0, 
            num_gpus=1
        ),
    )
)
distributor.run(dataset_map={"train": ShardedDataConnector.from_dataframe(train_df)})
```

**Key Components:**
- **ShardedDataConnector**: Distributes data across workers for parallel processing
- **GPU_NV_M Compute Pool**: NVIDIA Tesla T4 or equivalent GPU acceleration
- **Pre-downloaded Weights**: `@MODEL_STAGE/weights/yolo12n.pt` avoids GitHub access during training
""")

st.markdown("### Snowflake Components")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Container Runtime:**
    - Python 3.11+ with pip flexibility
    - GPU_NV_M compute pool (Tesla T4 or equivalent)
    - External Access Integration for GitHub dataset download
    
    **Network Configuration:**
    ```sql
    CREATE NETWORK RULE github_egress_rule
      TYPE = HOST_PORT
      MODE = EGRESS
      VALUE_LIST = (
        'github.com:443',
        'raw.githubusercontent.com:443',
        'objects.githubusercontent.com:443',
        'codeload.github.com:443'
      );
    ```
    """)

with col2:
    st.markdown("""
    **Stage Structure:**
    ```
    @MODEL_STAGE/
    ├── raw/
    │   └── deeppcb/       # Training images
    │       └── group*/    # Nested by group/board
    ├── models/
    │   └── yolov12_pcb/   # Trained model
    │       └── yolo_best.pt
    └── runs/              # Training logs
    ```
    
    **Key Tables:**
    ```sql
    -- DEFECT_LOGS: Inference results
    inference_id, board_id, detected_class,
    confidence_score, bbox_*, image_path
    
    -- PCB_LABELED_DATA: Ground truth
    filename, label_text (YOLO format)
    
    -- PCB_METADATA: Board info
    board_id, factory_line_id, product_type
    ```
    """)

st.markdown("### Evaluation & Diagnostics")

st.markdown("""
The notebook includes automated convergence analysis and per-class performance evaluation:

**Convergence Analysis:**
- Monitors mAP@50 and mAP@50-95 metrics during training
- Provides automated recommendations based on final metrics:
  - mAP50 > 0.80: Production-ready
  - mAP50 > 0.60: Acceptable
  - mAP50 < 0.50: Needs improvement

**Per-Class Performance:**
- Detection count breakdown by defect type
- Average confidence scores per class
- Identifies classes needing additional training data

**Confidence Distribution:**
- Histogram of prediction confidences
- Threshold selection guidance for production deployment
- Box plots by class to identify prediction certainty patterns
""")

st.markdown("### Performance Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Training Time", "~30 min", "50 epochs on GPU_NV_M")

with col2:
    st.metric("Model Size", "~15 MB", "YOLOv12n weights")

with col3:
    st.metric("Inference Latency", "<2 sec", "Per image including I/O")

st.markdown("""
**Known Limitations:**
- YOLOv12 requires CUDA-compatible GPU (handled by GPU compute pool)
- `flash-attn` compilation may take 15-20 minutes on first run
- Model trained on Deep PCB dataset; production deployment requires retraining on customer data
""")

st.divider()

# =============================================================================
# APPLICATION PAGES
# =============================================================================

st.header("Application Pages")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">Executive Overview</h4>
        <p style="color: #94a3b8;">
        High-level dashboard with defect Pareto analysis, factory line heatmap, and confidence distribution.
        Designed for VP of Operations and quality leadership.
        </p>
        <p style="color: #64748b; font-size: 0.85rem;">
        <strong>Key metrics:</strong> Total defects, images inspected, defects per observation, defect types detected
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">Vision Lab</h4>
        <p style="color: #94a3b8;">
        Interactive analysis tool for browsing stage images or uploading PCB images, viewing 
        YOLOv12 detection results with bounding box overlays, and comparing against ground truth.
        </p>
        <p style="color: #64748b; font-size: 0.85rem;">
        <strong>Features:</strong> Stage browsing, image upload, ground truth comparison, confidence filtering
        </p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# TECHNOLOGY STACK
# =============================================================================

st.header("Technology Stack")

st.markdown("""
<span class="tech-badge">Snowflake Notebooks</span>
<span class="tech-badge">Container Runtime</span>
<span class="tech-badge">GPU Compute Pool</span>
<span class="tech-badge">Model Registry</span>
<span class="tech-badge">Streamlit in Snowflake</span>
<span class="tech-badge tech-badge-model">YOLOv12</span>
<span class="tech-badge tech-badge-model">PyTorch</span>
<span class="tech-badge tech-badge-model">Ultralytics</span>
<span class="tech-badge tech-badge-external">External Access Integration</span>
""", unsafe_allow_html=True)

st.divider()

# =============================================================================
# LICENSES & ATTRIBUTIONS
# =============================================================================

st.header("Licenses & Attributions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">YOLOv12</h4>
        <span class="tech-badge tech-badge-model">AGPL-3.0</span>
        <p style="color: #94a3b8; margin-top: 0.5rem;">
            Attention-centric real-time object detector by University at Buffalo 
            and University of Chinese Academy of Sciences.
        </p>
        <p style="color: #94a3b8; font-size: 0.75rem;">
            <strong>Authors:</strong> Tian, Yunjie; Ye, Qixiang; Doermann, David<br/>
            <strong>Paper:</strong> <a href="https://arxiv.org/abs/2502.12524" style="color: #64D2FF;">arXiv:2502.12524</a><br/>
            <strong>Repository:</strong> <a href="https://github.com/sunsmarterjie/yolov12" style="color: #64D2FF;">github.com/sunsmarterjie/yolov12</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="arch-card">
        <h4 style="color: #e2e8f0;">Deep PCB Dataset</h4>
        <span class="tech-badge tech-badge-external">MIT License</span>
        <p style="color: #94a3b8; margin-top: 0.5rem;">
            PCB defect detection dataset with 1,500 image pairs and 6 defect classes.
        </p>
        <p style="color: #94a3b8; font-size: 0.75rem;">
            <strong>Authors:</strong> Tang, Sanli; He, Fan; Huang, Xiaolin; Yang, Jie<br/>
            <strong>Paper:</strong> <a href="https://arxiv.org/abs/1902.06197" style="color: #64D2FF;">arXiv:1902.06197</a><br/>
            <strong>Repository:</strong> <a href="https://github.com/tangsanli5201/DeepPCB" style="color: #64D2FF;">github.com/tangsanli5201/DeepPCB</a>
        </p>
    </div>
""", unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **PCB Defect Detection Demo**  
    AI-powered quality control using YOLOv12 on Snowflake Container Runtime with GPU compute.
    """)

with col2:
    st.markdown("""
    **Resources**  
    - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
    - [Container Runtime](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
    - [YOLOv12 Docs](https://docs.ultralytics.com/models/yolo12/)
    """)
