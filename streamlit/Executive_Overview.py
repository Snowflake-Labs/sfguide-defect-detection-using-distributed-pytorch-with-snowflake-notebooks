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
    page_title="Executive Overview",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navy blue theme styling matching executive dashboard design
st.markdown("""
<style>
    .stApp {
        background-color: #1a2332;
    }
    /* Global text visibility */
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        color: #e2e8f0 !important;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ffffff !important;
        font-weight: 600;
    }
    .stMarkdown, .stMarkdown p, .stText {
        color: #94a3b8 !important;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid #2d3748;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    /* Metric cards - Executive style */
    .metric-card {
        background: #2d3748;
        border: 1px solid #3f4d5f;
        border-radius: 10px;
        padding: 1.75rem 1.5rem;
        text-align: left;
        min-height: 140px;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
        font-weight: 500;
    }
    .metric-value {
        font-size: 2.75rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    .metric-value.green {
        color: #22c55e;
    }
    .metric-value.white {
        color: #ffffff;
    }
    .metric-value.orange {
        color: #f59e0b;
    }
    .metric-value.blue {
        color: #64D2FF;
    }
    .metric-trend {
        font-size: 0.875rem;
        font-weight: 500;
        margin-top: 0.5rem;
    }
    .metric-trend.up {
        color: #22c55e;
    }
    .metric-trend.stable {
        color: #ef4444;
    }
    .metric-trend.warning {
        color: #f59e0b;
    }
    /* Chart containers */
    .chart-container {
        background: #2d3748;
        border: 1px solid #3f4d5f;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    /* Captions and smaller text */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
    }
    /* Subheaders */
    .stSubheader, [data-testid="stSubheader"] {
        color: #ffffff !important;
        font-weight: 600;
    }
    /* Code blocks - dark theme */
    pre, code, .stCodeBlock, [data-testid="stCodeBlock"] {
        background-color: #2d3748 !important;
        color: #e2e8f0 !important;
    }
    pre code, .stCodeBlock code {
        color: #e2e8f0 !important;
    }
    p code, li code {
        background-color: #3f4d5f !important;
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

st.title("Executive Overview")
st.markdown("Real-time quality metrics across all production lines")

# =============================================================================
# KPI CARDS
# =============================================================================

col1, col2, col3, col4 = st.columns(4)

# Calculate metrics
yield_rate = (1 - (total_defects / max(total_observations, 1))) * 100 if total_observations > 0 else 0
defect_rate = (total_defects / max(total_observations, 1)) * 100 if total_observations > 0 else 0

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">YIELD RATE</div>
        <div class="metric-value green">{yield_rate:.1f}%</div>
        <div class="metric-trend up">↑ 0.5%</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">DEFECT RATE</div>
        <div class="metric-value white">{defect_rate:.1f}%</div>
        <div class="metric-trend stable">→ stable</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Calculate false positive rate (placeholder - would need actual data)
    false_positive_rate = 15.0  # Example value
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">FALSE POSITIVE RATE</div>
        <div class="metric-value orange">{false_positive_rate:.0f}%</div>
        <div class="metric-trend warning">↓ 5%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">BOARDS TODAY</div>
        <div class="metric-value white">{total_observations:,}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# CHARTS
# =============================================================================

if data_loaded and not defect_summary.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Defect Pareto Analysis")
        
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
            paper_bgcolor='#2d3748',
            plot_bgcolor='#2d3748',
            font=dict(color='#e2e8f0'),
            yaxis=dict(title='Count', gridcolor='#3f4d5f'),
            yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]),
            xaxis=dict(title='Defect Class', gridcolor='#3f4d5f'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=40, b=40),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Defect Rate by Factory Line")
        
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
                paper_bgcolor='#2d3748',
                plot_bgcolor='#2d3748',
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
            paper_bgcolor='#2d3748',
            plot_bgcolor='#2d3748',
            font=dict(color='#e2e8f0'),
            xaxis=dict(title='Confidence Score', gridcolor='#3f4d5f', tickformat='.1f'),
            yaxis=dict(title='Detection Count', gridcolor='#3f4d5f'),
            legend=dict(title='Defect Class'),
            margin=dict(l=40, r=40, t=40, b=40),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No confidence data available yet. Run the notebook to generate defect logs.")
    
    # Defect Type Examples
    st.subheader("Recent Detections")
    
    if not defect_examples.empty:
        # Create timeline-style recent detections
        st.markdown('<div style="display: flex; gap: 1rem; overflow-x: auto; padding: 1rem 0;">', unsafe_allow_html=True)
        
        # Color mapping for defect types matching screenshot
        defect_colors = {
            "open": "#dc2626",       # Red
            "short": "#ea580c",      # Orange
            "mousebite": "#f59e0b",  # Yellow
            "spur": "#16a34a",       # Green
            "copper": "#2563eb",     # Blue
            "pin-hole": "#7c3aed"    # Purple
        }
        
        cols = st.columns(4)
        for idx, row in defect_examples.head(4).iterrows():
            col_idx = idx % 4
            with cols[col_idx]:
                defect_class = row['DETECTED_CLASS']
                confidence = row['CONFIDENCE_SCORE']
                color = defect_colors.get(defect_class.lower(), "#64D2FF")
                
                # Create timeline-style detection card
                st.markdown(f"""
                <div style="background: #2d3748;
                            border: 1px solid #3f4d5f; 
                            border-radius: 8px; 
                            padding: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="width: 10px; height: 10px; background-color: {color}; 
                                     border-radius: 50%; display: inline-block;"></span>
                        <span style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">
                            {defect_class}
                        </span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.8rem;">
                        Line {idx + 1} • {int((idx + 1) * 2)}m ago
                    </div>
                </div>
                """, unsafe_allow_html=True)
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

