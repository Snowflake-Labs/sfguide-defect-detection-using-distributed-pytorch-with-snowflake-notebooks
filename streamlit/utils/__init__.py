# PCB Defect Detection Dashboard - Utilities

import os
import base64
import streamlit as st


def render_svg(svg_path: str, width: int = None, caption: str = None, border: bool = False) -> None:
    """
    Render an SVG file inline using st.markdown with base64 encoding.
    
    Streamlit in Snowflake doesn't support st.image() with file paths.
    This function reads the SVG content and embeds it as a base64 image.
    
    Args:
        svg_path: Path to the SVG file (relative to the streamlit app root)
        width: Optional width in pixels (default: uses SVG's native width)
        caption: Optional caption to display below the image
        border: Add a visible border around the SVG
    """
    paths_to_try = [
        svg_path,
        os.path.join("/tmp/appRoot", svg_path),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), svg_path),
    ]
    
    svg_content = None
    for path in paths_to_try:
        try:
            with open(path, 'r') as f:
                svg_content = f.read()
            break
        except (FileNotFoundError, IOError):
            continue
    
    if svg_content is None:
        st.warning(f"SVG file not found: {svg_path}")
        return
    
    b64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    
    width_style = f'width: {width}px;' if width else 'width: 100%;'
    border_style = "border: 1px solid #334155; border-radius: 12px; padding: 1rem; background-color: #0f172a;" if border else ""
    
    html = f'''
    <div style="{border_style}">
        <img src="data:image/svg+xml;base64,{b64}" style="{width_style}" />
    </div>
    '''
    
    if caption:
        html += f'<p style="text-align: center; color: #e2e8f0; font-size: 0.875rem; margin-top: 0.5rem;">{caption}</p>'
    
    st.markdown(html, unsafe_allow_html=True)
