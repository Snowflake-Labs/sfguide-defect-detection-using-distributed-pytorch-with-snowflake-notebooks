"""
PCB Defect Detection Dashboard - Executive Overview

Main entry point for the Streamlit application.
Displays KPIs, defect distribution, and trends.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session
from PIL import Image, ImageDraw
import os

from utils import render_svg
from utils.data_loader import (
    load_defect_summary,
    load_factory_line_data,
    load_defect_examples,
    load_confidence_distribution,
    load_stage_image,
    resolve_image_path
)
from utils.query_registry import (
    execute_query,
    TOTAL_DEFECTS_SQL,
    PCB_COUNT_SQL,
    OBSERVATION_COUNT_SQL
)

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="PCB Defect Detection",
    layout="wide",
    initial_sidebar_state="expanded"
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
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #64D2FF;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    /* Captions and smaller text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #cbd5e1 !important;
    }
    /* Subheaders */
    .stSubheader, [data-testid="stSubheader"] {
        color: #f8fafc !important;
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
    st.markdown("### Quick Stats")

# =============================================================================
# DATA LOADING
# =============================================================================

session = get_active_session()

try:
    # Load data
    defect_summary = load_defect_summary(session)
    factory_data = load_factory_line_data(session)
    defect_examples = load_defect_examples(session)
    confidence_dist = load_confidence_distribution(session)
    
    # Get total counts
    total_df = execute_query(session, TOTAL_DEFECTS_SQL, "total_defects")
    pcb_df = execute_query(session, PCB_COUNT_SQL, "pcb_count")
    obs_df = execute_query(session, OBSERVATION_COUNT_SQL, "observation_count")
    
    total_defects = int(total_df['TOTAL_DEFECTS'].iloc[0]) if not total_df.empty else 0
    total_pcbs = int(pcb_df['TOTAL_PCBS'].iloc[0]) if not pcb_df.empty else 0
    total_observations = int(obs_df['TOTAL_OBSERVATIONS'].iloc[0]) if not obs_df.empty else 0
    
    data_loaded = True
except Exception as e:
    st.error(f"Error loading data: {e}")
    data_loaded = False
    total_defects = 0
    total_pcbs = 0
    total_observations = 0

# =============================================================================
# HEADER
# =============================================================================

st.title("PCB Defect Detection Dashboard")
st.markdown("*Real-time defect analytics powered by YOLOv12 on Snowflake*")

# =============================================================================
# KPI CARDS
# =============================================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_defects:,}</div>
        <div class="metric-label">Total Defects</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total_observations:,}</div>
        <div class="metric-label">Images Inspected</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Defects per observation (each image counted once)
    defects_per_obs = total_defects / max(total_observations, 1)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{defects_per_obs:.1f}</div>
        <div class="metric-label">Defects / Observation</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    num_classes = len(defect_summary) if data_loaded and not defect_summary.empty else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{num_classes}</div>
        <div class="metric-label">Defect Types</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# CHARTS
# =============================================================================

if data_loaded and not defect_summary.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Defect Distribution (Pareto)")
        
        # Sort by count for Pareto
        df_sorted = defect_summary.sort_values('DEFECT_COUNT', ascending=False)
        
        fig = go.Figure()
        
        # Bar chart
        fig.add_trace(go.Bar(
            x=df_sorted['DETECTED_CLASS'],
            y=df_sorted['DEFECT_COUNT'],
            name='Count',
            marker_color='#64D2FF'
        ))
        
        # Cumulative line
        df_sorted['CUMULATIVE_PCT'] = df_sorted['DEFECT_COUNT'].cumsum() / df_sorted['DEFECT_COUNT'].sum() * 100
        fig.add_trace(go.Scatter(
            x=df_sorted['DETECTED_CLASS'],
            y=df_sorted['CUMULATIVE_PCT'],
            name='Cumulative %',
            yaxis='y2',
            line=dict(color='#FF9F0A', width=2),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            font=dict(color='#e2e8f0'),
            yaxis=dict(title='Count', gridcolor='#334155'),
            yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]),
            xaxis=dict(title='Defect Class', gridcolor='#334155'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Factory Line Performance")
        
        if not factory_data.empty:
            # Pivot for heatmap
            pivot_df = factory_data.pivot_table(
                index='FACTORY_LINE_ID',
                columns='DETECTED_CLASS',
                values='DEFECT_COUNT',
                fill_value=0
            )
            
            fig = px.imshow(
                pivot_df.values,
                labels=dict(x="Defect Type", y="Factory Line", color="Count"),
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                paper_bgcolor='#0f172a',
                plot_bgcolor='#0f172a',
                font=dict(color='#e2e8f0'),
                margin=dict(l=40, r=40, t=40, b=40),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No factory line data available")

    # Confidence Distribution Chart
    st.subheader("Model Confidence Distribution")
    
    if not confidence_dist.empty:
        fig = px.bar(
            confidence_dist,
            x='CONF_BUCKET',
            y='COUNT',
            color='DETECTED_CLASS',
            barmode='group',
            labels={'CONF_BUCKET': 'Confidence Score', 'COUNT': 'Detection Count', 'DETECTED_CLASS': 'Defect Class'}
        )
        
        fig.update_layout(
            paper_bgcolor='#0f172a',
            plot_bgcolor='#0f172a',
            font=dict(color='#e2e8f0'),
            xaxis=dict(title='Confidence Score', gridcolor='#334155', tickformat='.1f'),
            yaxis=dict(title='Detection Count', gridcolor='#334155'),
            legend=dict(title='Defect Class'),
            margin=dict(l=40, r=40, t=40, b=40),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confidence data available yet. Run the notebook to generate defect logs.")
    
    # Defect Type Examples
    st.subheader("Defect Type Examples")
    st.markdown("*Sample images showing each detected defect type with highest confidence*")
    
    if not defect_examples.empty:
        # Create columns for defect examples (3 per row)
        defect_classes = defect_examples['DETECTED_CLASS'].unique()
        
        # Color mapping for defect types
        defect_colors = {
            "open": "#dc2626",
            "short": "#ea580c",
            "mousebite": "#ca8a04",
            "spur": "#16a34a",
            "copper": "#2563eb",
            "pin-hole": "#7c3aed"
        }
        
        cols = st.columns(3)
        for idx, row in defect_examples.iterrows():
            col_idx = idx % 3
            with cols[col_idx]:
                defect_class = row['DETECTED_CLASS']
                confidence = row['CONFIDENCE_SCORE']
                color = defect_colors.get(defect_class.lower(), "#64D2FF")
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                            border: 2px solid {color}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: {color}; font-weight: 700; font-size: 1.1rem; text-transform: uppercase;">{defect_class}</span>
                        <span style="color: #e2e8f0; font-size: 0.85rem;">Conf: {confidence:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Try to load and display the sample image
                try:
                    image_path = row['IMAGE_PATH']
                    # Extract filename from stage path
                    filename = os.path.basename(image_path.replace('@MODEL_STAGE/', ''))
                    
                    # Resolve the actual stage path using the mapping
                    stage_path = resolve_image_path(session, image_path)
                    local_path = load_stage_image(session, stage_path)
                    
                    if os.path.exists(local_path):
                        img = Image.open(local_path)
                        
                        # Draw the bounding box on the image
                        img_draw = img.copy().convert("RGB")
                        draw = ImageDraw.Draw(img_draw)
                        img_w, img_h = img_draw.size
                        
                        cx = row['BBOX_X_CENTER'] * img_w
                        cy = row['BBOX_Y_CENTER'] * img_h
                        w = row['BBOX_WIDTH'] * img_w
                        h = row['BBOX_HEIGHT'] * img_h
                        x1, y1 = cx - w/2, cy - h/2
                        x2, y2 = cx + w/2, cy + h/2
                        
                        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                        
                        st.image(img_draw, caption=f"{defect_class} example", use_container_width=True)
                except Exception as e:
                    st.caption(f"Image: {row['IMAGE_PATH']}")
    else:
        st.info("No defect examples available yet. Run the notebook to generate inference data.")

else:
    st.info("No defect data available. Run the YOLOv12 training notebook to generate inference results.")
    
    st.markdown("""
    ### Getting Started
    
    1. **Deploy the infrastructure**: Run `./deploy.sh` to set up Snowflake resources
    2. **Execute the notebook**: Run `./run.sh main` to train YOLOv12 and generate defect logs
    3. **Refresh this dashboard**: Data will appear automatically after inference runs
    """)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("Powered by Snowflake Notebooks (Container Runtime) with GPU • YOLOv12 Object Detection")

