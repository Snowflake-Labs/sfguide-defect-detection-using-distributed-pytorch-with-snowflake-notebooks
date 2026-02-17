"""
PCB Defect Detection - Vision Lab

Interactive YOLOv12 inference interface with ground truth comparison.
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session
from PIL import Image, ImageDraw
import io
import pandas as pd

from utils import render_svg
from utils.data_loader import load_recent_defects, list_stage_images, load_stage_image, load_images_with_defects, resolve_image_path
from utils.query_registry import execute_query, get_image_defects_sql, get_ground_truth_sql

# =============================================================================
# CONSTANTS
# =============================================================================

CLASS_NAMES = {
    0: 'open',
    1: 'short',
    2: 'mousebite',
    3: 'spur',
    4: 'copper',
    5: 'pin-hole'
}

DEFECT_COLORS = {
    "open": "#dc2626",
    "short": "#ea580c",
    "mousebite": "#ca8a04",
    "spur": "#16a34a",
    "copper": "#2563eb",
    "pin-hole": "#7c3aed"
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_yolo_labels(label_text: str) -> list:
    """
    Parse YOLO format labels into list of tuples.
    
    Args:
        label_text: String with YOLO format labels (one per line)
                   Format: class_id x_center y_center width height
    
    Returns:
        List of tuples: [(class_id, x_center, y_center, width, height), ...]
    """
    labels = []
    if not label_text or not label_text.strip():
        return labels
    
    for line in label_text.strip().split('\n'):
        parts = line.strip().split()
        if len(parts) >= 5:
            try:
                class_id = int(parts[0])
                cx = float(parts[1])
                cy = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
                labels.append((class_id, cx, cy, w, h))
            except (ValueError, IndexError):
                continue
    return labels


def draw_ground_truth(image: Image.Image, labels: list) -> Image.Image:
    """
    Draw ground truth bounding boxes on image with dashed-style appearance.
    
    Args:
        image: PIL Image to annotate
        labels: List of tuples (class_id, cx, cy, w, h) in normalized coords
    
    Returns:
        Annotated PIL Image with ground truth boxes
    """
    img_copy = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img_copy)
    img_w, img_h = img_copy.size
    
    for class_id, cx, cy, w, h in labels:
        # Convert normalized to pixel coordinates
        px_cx = cx * img_w
        px_cy = cy * img_h
        px_w = w * img_w
        px_h = h * img_h
        
        x1, y1 = px_cx - px_w/2, px_cy - px_h/2
        x2, y2 = px_cx + px_w/2, px_cy + px_h/2
        
        class_name = CLASS_NAMES.get(class_id, 'unknown')
        color = DEFECT_COLORS.get(class_name, "#ffffff")
        
        # Draw rectangle (ground truth uses thinner line)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        
        # Draw label with "GT:" prefix
        label = f"GT: {class_name}"
        draw.text((x1, max(0, y1 - 15)), label, fill=color)
    
    return img_copy


def draw_comparison(image: Image.Image, ground_truth: list, inference_df: pd.DataFrame, confidence_threshold: float = 0.0) -> Image.Image:
    """
    Draw both ground truth and inference results on the same image.
    
    Ground truth: thin boxes with "GT:" prefix
    Inference: thick boxes with confidence score
    
    Args:
        image: PIL Image to annotate
        ground_truth: List of tuples (class_id, cx, cy, w, h)
        inference_df: DataFrame with inference results
        confidence_threshold: Minimum confidence score to display (default 0.0)
    
    Returns:
        Annotated PIL Image
    """
    img_copy = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img_copy)
    img_w, img_h = img_copy.size
    
    # Draw ground truth boxes (thinner, darker)
    for class_id, cx, cy, w, h in ground_truth:
        px_cx = cx * img_w
        px_cy = cy * img_h
        px_w = w * img_w
        px_h = h * img_h
        
        x1, y1 = px_cx - px_w/2, px_cy - px_h/2
        x2, y2 = px_cx + px_w/2, px_cy + px_h/2
        
        class_name = CLASS_NAMES.get(class_id, 'unknown')
        # Use a muted version of the color for ground truth
        color = "#6b7280"  # Gray for ground truth outline
        
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        draw.text((x1, max(0, y2 + 2)), f"GT: {class_name}", fill=color)
    
    # Draw inference boxes (thicker, brighter)
    if inference_df is not None and not inference_df.empty:
        # Filter locally if needed, though caller should usually filter
        filtered_df = inference_df[inference_df['CONFIDENCE_SCORE'] >= confidence_threshold]
        
        for _, row in filtered_df.iterrows():
            if pd.isna(row.get('BBOX_X_CENTER')) or pd.isna(row.get('BBOX_Y_CENTER')):
                continue
            
            cx = row['BBOX_X_CENTER'] * img_w
            cy = row['BBOX_Y_CENTER'] * img_h
            w = row['BBOX_WIDTH'] * img_w
            h = row['BBOX_HEIGHT'] * img_h
            
            x1, y1 = cx - w/2, cy - h/2
            x2, y2 = cx + w/2, cy + h/2
            
            defect_class = row['DETECTED_CLASS'].lower()
            color = DEFECT_COLORS.get(defect_class, "#ffffff")
            
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label = f"{row['DETECTED_CLASS']} ({row['CONFIDENCE_SCORE']:.2f})"
            draw.text((x1, max(0, y1 - 15)), label, fill=color)
    
    return img_copy


def draw_detections(image: Image.Image, defects_df: pd.DataFrame, confidence_threshold: float = 0.0) -> Image.Image:
    """
    Draw bounding boxes on image for detected defects.
    
    Args:
        image: PIL Image to annotate
        defects_df: DataFrame with BBOX_X_CENTER, BBOX_Y_CENTER, BBOX_WIDTH, 
                    BBOX_HEIGHT (normalized 0-1) and DETECTED_CLASS columns
        confidence_threshold: Minimum confidence score to display (default 0.0)
    
    Returns:
        Annotated PIL Image with bounding boxes drawn
    """
    # Color mapping for defect types (matching CSS badge colors)
    colors = {
        "open": "#dc2626",
        "short": "#ea580c",
        "mousebite": "#ca8a04",
        "spur": "#16a34a",
        "copper": "#2563eb",
        "pin-hole": "#7c3aed"
    }
    
    # Work on a copy to preserve original
    img_copy = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img_copy)
    img_w, img_h = img_copy.size
    
    # Filter locally
    filtered_df = defects_df[defects_df['CONFIDENCE_SCORE'] >= confidence_threshold]
    
    for _, row in filtered_df.iterrows():
        # Skip rows with missing bbox data
        if pd.isna(row.get('BBOX_X_CENTER')) or pd.isna(row.get('BBOX_Y_CENTER')):
            continue
            
        # Convert YOLO normalized coords (center x, center y, width, height) to pixel corners
        cx = row['BBOX_X_CENTER'] * img_w
        cy = row['BBOX_Y_CENTER'] * img_h
        w = row['BBOX_WIDTH'] * img_w
        h = row['BBOX_HEIGHT'] * img_h
        
        x1, y1 = cx - w/2, cy - h/2
        x2, y2 = cx + w/2, cy + h/2
        
        # Get color for this defect class
        defect_class = row['DETECTED_CLASS'].lower()
        color = colors.get(defect_class, "#ffffff")
        
        # Draw rectangle with thick outline
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # Draw label above the box
        label = f"{row['DETECTED_CLASS']} ({row['CONFIDENCE_SCORE']:.2f})"
        draw.text((x1, max(0, y1 - 15)), label, fill=color)
    
    return img_copy

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Vision Lab | PCB Defect Detection",
    layout="wide"
)

# Dark theme styling with improved text visibility
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
    }
    /* Global text visibility */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        color: #f1f5f9 !important;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #f8fafc !important;
    }
    .stMarkdown, .stMarkdown p, .stText {
        color: #e2e8f0 !important;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    [data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    /* Captions and smaller text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #cbd5e1 !important;
    }
    /* Subheaders */
    .stSubheader, [data-testid="stSubheader"] {
        color: #f8fafc !important;
    }
    .detection-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .defect-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .defect-open { background-color: #dc2626; color: white; }
    .defect-short { background-color: #ea580c; color: white; }
    .defect-mousebite { background-color: #ca8a04; color: white; }
    .defect-spur { background-color: #16a34a; color: white; }
    .defect-copper { background-color: #2563eb; color: white; }
    .defect-pin-hole { background-color: #7c3aed; color: white; }
    .chat-message {
        background: rgba(59, 130, 246, 0.08);
        border-left: 3px solid #3b82f6;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        border-radius: 0 8px 8px 0;
        color: #f1f5f9 !important;
    }
    /* Code blocks - dark theme */
    pre, code, .stCodeBlock, [data-testid="stCodeBlock"] {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    pre code, .stCodeBlock code {
        color: #e2e8f0 !important;
    }
    p code, li code {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        padding: 0.125rem 0.375rem;
        border-radius: 4px;
    }
    /* File uploader styling for dark theme */
    [data-testid="stFileUploader"] {
        background-color: #1e293b !important;
        border-radius: 8px;
        padding: 0.5rem;
    }
    [data-testid="stFileUploader"] section {
        background-color: #1e293b !important;
    }
    [data-testid="stFileUploader"] section > div {
        background-color: #1e293b !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
    }
    [data-testid="stFileUploader"] small {
        color: #94a3b8 !important;
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
    
    st.markdown("---")
    st.markdown("### Model Info")
    st.markdown("**Model**: YOLOv12n")
    st.markdown("**Classes**: 6 defect types")
    st.markdown("**Input Size**: 640x640")

# =============================================================================
# HEADER
# =============================================================================

st.title("Vision Lab")
st.markdown("*Interactive PCB defect detection with AI-powered guidance*")

# =============================================================================
# MAIN CONTENT
# =============================================================================

session = get_active_session()

# Split layout
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Image Analysis")
    
    # Image source selection
    image_source = st.radio(
        "Image Source",
        ["Browse Stage", "Upload New"],
        horizontal=True,
        help="Browse images from Snowflake stage or upload a new image"
    )
    
    # Variable to hold the loaded image
    image = None
    image_caption = None
    
    if image_source == "Browse Stage":
        # Load images with defect information for smart picker
        import os
        
        try:
            images_with_defects = load_images_with_defects(session)
            has_defect_data = not images_with_defects.empty
        except Exception:
            images_with_defects = pd.DataFrame()
            has_defect_data = False
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            show_defects_only = st.checkbox("Show images with defects only", value=True, 
                                            help="Filter to show only images where defects were detected")
        with col_filter2:
            if has_defect_data:
                defect_types = ['All'] + sorted(set(
                    d.strip() for row in images_with_defects['DEFECT_TYPES'].dropna() 
                    for d in row.split(',')
                ))
                selected_defect_type = st.selectbox("Filter by defect type", defect_types)
            else:
                selected_defect_type = 'All'
        
        # Build the image list based on filters
        if has_defect_data and show_defects_only:
            # Use images from defect logs
            filtered_images = images_with_defects.copy()
            
            if selected_defect_type != 'All':
                filtered_images = filtered_images[
                    filtered_images['DEFECT_TYPES'].str.contains(selected_defect_type, case=False, na=False)
                ]
            
            if not filtered_images.empty:
                # Create display names with defect info
                image_options = []
                for _, row in filtered_images.iterrows():
                    path = row['IMAGE_PATH']
                    filename = os.path.basename(path.replace('@MODEL_STAGE/', ''))
                    defect_count = row['DEFECT_COUNT']
                    defect_types = row['DEFECT_TYPES']
                    display = f"{filename} ({defect_count} defects: {defect_types})"
                    # Resolve the actual stage path using the mapping
                    stage_path = resolve_image_path(session, path)
                    image_options.append((display, stage_path, filename))
                
                selected_idx = st.selectbox(
                    "Select a PCB image",
                    range(len(image_options)),
                    format_func=lambda i: image_options[i][0],
                    help=f"Showing {len(image_options)} images with detected defects"
                )
                
                selected_display, selected_stage_path, selected_filename = image_options[selected_idx]
            else:
                st.info("No images match the selected filter criteria.")
                selected_stage_path = None
                selected_filename = None
        else:
            # Fall back to listing all stage images
            stage_images = list_stage_images(session, limit=100)
            
            if stage_images:
                display_names = [os.path.basename(p) for p in stage_images]
                
                selected_idx = st.selectbox(
                    "Select a PCB image from stage",
                    range(len(stage_images)),
                    format_func=lambda i: display_names[i],
                    help=f"Found {len(stage_images)} images in @MODEL_STAGE/raw/deeppcb/"
                )
                
                selected_stage_path = stage_images[selected_idx]
                selected_filename = display_names[selected_idx]
            else:
                st.info("No images found in stage. Run the notebook first to download the Deep PCB dataset.")
                selected_stage_path = None
                selected_filename = None
        
        # Load button
        if selected_stage_path:
            if st.button("Load Image", type="secondary"):
                with st.spinner("Downloading image from stage..."):
                    try:
                        local_path = load_stage_image(session, selected_stage_path)
                        image = Image.open(local_path)
                        image_caption = f"Stage: {selected_filename}"
                        st.session_state['loaded_image'] = image
                        st.session_state['loaded_caption'] = image_caption
                        st.session_state['loaded_filename'] = selected_filename
                    except Exception as e:
                        st.error(f"Failed to load image: {e}")
            
            # Check if we have a previously loaded image in session state
            if 'loaded_image' in st.session_state:
                image = st.session_state['loaded_image']
                image_caption = st.session_state.get('loaded_caption', 'PCB Image')
    
    else:
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload a PCB image for defect analysis",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a PCB image to run YOLOv12 inference"
        )
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            image_caption = f"Uploaded: {uploaded_file.name}"
    
    # Display and analyze the image (common for both sources)
    if image is not None:
        # Store original image for display (will be replaced with annotated version after detection)
        display_image = image
        
        # Get the filename for querying
        if image_caption:
            # Extract filename from caption (e.g., "Stage: 00041001_temp.jpg")
            image_filename = image_caption.split(": ")[-1] if ": " in image_caption else image_caption
        else:
            image_filename = st.session_state.get('loaded_filename', None)
        
        # Display options
        st.markdown("**Display Options:**")
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            show_ground_truth = st.checkbox("Show Ground Truth", value=True,
                                           help="Display training data labels (gray boxes)")
        with col_opt2:
            show_inference = st.checkbox("Show Inference Results", value=True,
                                        help="Display YOLOv12 predictions (colored boxes)")
        
        # Confidence threshold slider
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.75,
            step=0.05,
            help="Only show detections with confidence score above this threshold"
        )
        
        # Analyze button - fetch data
        if st.button("Analyze Image", type="primary"):
            with st.spinner("Analyzing image..."):
                # Reset previous analysis
                ground_truth_labels = []
                defects_df = pd.DataFrame()
                
                # Fetch Ground Truth
                if image_filename:
                    try:
                        gt_sql = get_ground_truth_sql(image_filename)
                        gt_result = execute_query(session, gt_sql, "ground_truth")
                        if not gt_result.empty:
                            label_text = gt_result['LABEL_TEXT'].iloc[0]
                            ground_truth_labels = parse_yolo_labels(label_text)
                    except Exception:
                        pass

                # Fetch Inference Results
                if image_filename:
                    try:
                        defects_sql = get_image_defects_sql(image_filename)
                        defects_df = execute_query(session, defects_sql, "image_defects")
                    except Exception:
                        pass
                
                # Store in session state
                st.session_state['current_analysis'] = {
                    'filename': image_filename,
                    'ground_truth': ground_truth_labels,
                    'inference': defects_df,
                    'analyzed': True
                }
        
        # Display Logic
        analysis_data = st.session_state.get('current_analysis', {})
        
        # Check if we have analysis data for the CURRENT loaded image
        is_analyzed = analysis_data.get('analyzed', False) and analysis_data.get('filename') == image_filename
        
        if is_analyzed:
            ground_truth_labels = analysis_data['ground_truth']
            defects_df = analysis_data['inference']
            
            # Filter inference by confidence
            filtered_defects = pd.DataFrame()
            if not defects_df.empty:
                filtered_defects = defects_df[defects_df['CONFIDENCE_SCORE'] >= confidence_threshold]
            
            # Determine what to draw
            has_gt = bool(ground_truth_labels)
            has_inference = not filtered_defects.empty
            
            # Draw
            if (show_ground_truth and has_gt) or (show_inference and has_inference):
                if show_ground_truth and show_inference:
                     display_image = draw_comparison(image, ground_truth_labels if show_ground_truth else [], filtered_defects if show_inference else None, confidence_threshold)
                elif show_ground_truth and has_gt:
                     display_image = draw_ground_truth(image, ground_truth_labels)
                elif show_inference and has_inference:
                     display_image = draw_detections(image, filtered_defects, confidence_threshold)
            else:
                 display_image = image # No annotations needed based on filters
            
            st.image(display_image, caption=image_caption)
            
            # Results Card
            gt_count = len(ground_truth_labels)
            inf_count = len(filtered_defects)
            inf_total = len(defects_df) if not defects_df.empty else 0
            
            st.markdown(f"""
            <div class="detection-card">
                <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">Analysis Results</h4>
                <div style="display: flex; gap: 2rem; margin-top: 0.5rem;">
                    <div>
                        <span style="color: #6b7280; font-size: 0.85rem;">Ground Truth</span><br/>
                        <span style="color: #e2e8f0; font-size: 1.5rem; font-weight: 600;">{gt_count}</span>
                        <span style="color: #cbd5e1;"> defects</span>
                    </div>
                    <div>
                        <span style="color: #64D2FF; font-size: 0.85rem;">Model Inference</span><br/>
                        <span style="color: #e2e8f0; font-size: 1.5rem; font-weight: 600;">{inf_count}</span>
                        <span style="color: #cbd5e1;"> / {inf_total} detected</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show ground truth defect types
            if show_ground_truth and has_gt:
                gt_classes = [CLASS_NAMES.get(label[0], 'unknown') for label in ground_truth_labels]
                st.markdown("**Ground Truth Labels:** " + ", ".join(gt_classes))
            
            # Show inference defect badges (filtered by threshold)
            if show_inference and has_inference:
                st.markdown("**Model Predictions:**")
                badges_html = ""
                for _, row in filtered_defects.iterrows():
                    defect_class = row['DETECTED_CLASS'].lower().replace('-', '')
                    confidence = row['CONFIDENCE_SCORE']
                    badges_html += f'<span class="defect-badge defect-{defect_class}">{row["DETECTED_CLASS"]} ({confidence:.2f})</span>\n'
                st.markdown(badges_html, unsafe_allow_html=True)
                
                # Show detailed table
                with st.expander("Detailed Detection Data"):
                    display_df_cols = filtered_defects[['DETECTED_CLASS', 'CONFIDENCE_SCORE', 'BOARD_ID']].copy()
                    display_df_cols.columns = ['Defect Type', 'Confidence', 'Board ID']
                    st.dataframe(display_df_cols, use_container_width=True)
            
            # If nothing found/filtered
            if not has_gt and not has_inference:
                 st.markdown("""
                <div class="detection-card">
                    <h4 style="color: #e2e8f0; margin-bottom: 0.5rem;">No Data Visible</h4>
                    <p style="color: #cbd5e1;">
                        No ground truth or inference data matches the current filters.
                    </p>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.image(image, caption=image_caption)
    else:
        # Show sample from recent detections
        st.info("Select an image from the stage above or upload a new image.")
        
        try:
            recent_df = load_recent_defects(session)
            if not recent_df.empty:
                st.markdown("### Recent Detections")
                
                for _, row in recent_df.head(5).iterrows():
                    defect_class = row['DETECTED_CLASS'].lower().replace('-', '')
                    confidence = row['CONFIDENCE_SCORE']
                    
                    st.markdown(f"""
                    <div class="detection-card">
                        <span class="defect-badge defect-{defect_class}">{row['DETECTED_CLASS']} ({confidence:.2f})</span>
                        <br/>
                        <small style="color: #cbd5e1;">
                            Board: {row['BOARD_ID']} | Image: {row['IMAGE_PATH']}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.info("No recent detections available. Run the notebook to generate inference data.")

with col_right:
    # Quick reference
    st.markdown("### Defect Reference")
    
    defect_info = {
        "open": ("Critical", "Broken trace causing circuit discontinuity"),
        "short": ("Critical", "Unintended connection between traces"),
        "mousebite": ("Minor", "Irregular edge from depanelization"),
        "spur": ("Major", "Unwanted copper protrusion"),
        "copper": ("Major", "Exposed copper area"),
        "pin-hole": ("Minor", "Small void in copper plating")
    }
    
    for defect, (severity, desc) in defect_info.items():
        severity_color = "#dc2626" if severity == "Critical" else "#ca8a04" if severity == "Major" else "#16a34a"
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span class="defect-badge defect-{defect}">{defect}</span>
            <span style="color: {severity_color}; font-size: 0.75rem; margin-right: 0.5rem;">[{severity}]</span>
            <span style="color: #e2e8f0; font-size: 0.875rem;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("Vision Lab • YOLOv12 Inference • Ground Truth Comparison")
