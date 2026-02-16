"""
Data Loader for PCB Defect Detection Dashboard

Provides parallel query execution and caching utilities.
"""

from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import streamlit as st

from utils.query_registry import execute_query


def run_queries_parallel(
    session,
    queries: Dict[str, str],
    max_workers: int = 4
) -> Dict[str, pd.DataFrame]:
    """
    Execute multiple queries in parallel.
    
    Args:
        session: Snowflake Snowpark session
        queries: Dict mapping result keys to SQL strings
        max_workers: Maximum parallel threads
    
    Returns:
        Dict mapping keys to result DataFrames
    
    Raises:
        RuntimeError: If any query fails
    """
    results = {}
    errors = []
    
    def run_single_query(key: str, sql: str):
        try:
            return key, execute_query(session, sql, key)
        except Exception as e:
            return key, e
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_query, key, sql): key
            for key, sql in queries.items()
        }
        
        for future in as_completed(futures):
            key, result = future.result()
            if isinstance(result, Exception):
                errors.append(f"{key}: {result}")
            else:
                results[key] = result
    
    if errors:
        raise RuntimeError(f"Query errors: {'; '.join(errors)}")
    
    return results


@st.cache_data(ttl=60)
def load_defect_summary(_session) -> pd.DataFrame:
    """Load defect summary with caching."""
    from utils.query_registry import DEFECT_SUMMARY_SQL
    return execute_query(_session, DEFECT_SUMMARY_SQL, "defect_summary")


@st.cache_data(ttl=60)
def load_daily_trends(_session) -> pd.DataFrame:
    """Load daily trends with caching."""
    from utils.query_registry import DAILY_TRENDS_SQL
    return execute_query(_session, DAILY_TRENDS_SQL, "daily_trends")


@st.cache_data(ttl=60)
def load_factory_line_data(_session) -> pd.DataFrame:
    """Load factory line data with caching."""
    from utils.query_registry import FACTORY_LINE_SQL
    return execute_query(_session, FACTORY_LINE_SQL, "factory_line_defects")


@st.cache_data(ttl=60)
def load_recent_defects(_session) -> pd.DataFrame:
    """Load recent defects with caching."""
    from utils.query_registry import RECENT_DEFECTS_SQL
    return execute_query(_session, RECENT_DEFECTS_SQL, "recent_defects")


@st.cache_data(ttl=60)
def load_defect_examples(_session) -> pd.DataFrame:
    """Load one sample image per defect class with highest confidence."""
    from utils.query_registry import DEFECT_EXAMPLES_SQL
    return execute_query(_session, DEFECT_EXAMPLES_SQL, "defect_examples")


@st.cache_data(ttl=60)
def load_confidence_distribution(_session) -> pd.DataFrame:
    """Load confidence score distribution by defect class."""
    from utils.query_registry import CONFIDENCE_DISTRIBUTION_SQL
    return execute_query(_session, CONFIDENCE_DISTRIBUTION_SQL, "confidence_distribution")


@st.cache_data(ttl=60)
def load_images_with_defects(_session) -> pd.DataFrame:
    """Load images grouped by defect count and types for smart picker."""
    from utils.query_registry import IMAGES_WITH_DEFECTS_SQL
    return execute_query(_session, IMAGES_WITH_DEFECTS_SQL, "images_with_defects")


@st.cache_data(ttl=300)
def list_stage_images(_session, limit: int = 100) -> List[str]:
    """
    List PCB images available in the MODEL_STAGE.
    
    Args:
        _session: Snowflake Snowpark session
        limit: Maximum number of images to return
    
    Returns:
        List of stage file paths
    """
    try:
        # LIST command returns file metadata
        result = _session.sql(
            "LIST @MODEL_STAGE/raw/deeppcb/ PATTERN='.*\\.jpg'"
        ).collect()
        
        # Extract file paths from the result
        file_paths = []
        for row in result[:limit]:
            # The 'name' column contains the full stage path
            file_path = row['name'] if 'name' in row.asDict() else str(row[0])
            file_paths.append(file_path)
        
        return file_paths
    except Exception as e:
        # Return empty list if stage doesn't exist or has no images
        return []


@st.cache_data(ttl=300)
def get_stage_path_mapping(_session) -> Dict[str, str]:
    """
    Build a mapping from filename to full stage path.
    
    The stage has nested directories (group*/subdir/) but DEFECT_LOGS stores
    simplified paths with just the filename. This mapping allows us to resolve
    the actual stage path from a filename.
    
    Returns:
        Dict mapping filename (e.g., '20085122_test.jpg') to 
        full stage path (e.g., 'model_stage/raw/deeppcb/group20085/20085/20085122_test.jpg')
    """
    import os
    stage_images = list_stage_images(_session, limit=10000)
    return {os.path.basename(path): path for path in stage_images}


def resolve_image_path(_session, image_path: str) -> str:
    """
    Resolve an IMAGE_PATH from DEFECT_LOGS to the actual stage path.
    
    DEFECT_LOGS stores paths like '@MODEL_STAGE/raw/deeppcb/file.jpg' but the
    actual stage has nested directories. This function resolves the filename
    to the correct full path.
    
    Args:
        _session: Snowflake Snowpark session
        image_path: Path from DEFECT_LOGS (e.g., '@MODEL_STAGE/raw/deeppcb/file.jpg')
    
    Returns:
        Actual stage path that can be downloaded (e.g., 'model_stage/raw/deeppcb/group.../file.jpg')
    """
    import os
    
    # Extract just the filename from the path
    filename = os.path.basename(image_path.replace('@MODEL_STAGE/', '').replace('model_stage/', ''))
    
    # Look up the full path in our mapping
    mapping = get_stage_path_mapping(_session)
    
    if filename in mapping:
        return mapping[filename]
    
    # Fallback: try the original path conversion
    if image_path.startswith('@MODEL_STAGE/'):
        return image_path.replace('@MODEL_STAGE/', 'model_stage/')
    
    return image_path


def load_stage_image(_session, stage_path: str, local_dir: str = "/tmp/pcb_images") -> str:
    """
    Download an image from Snowflake stage to local filesystem.
    
    Args:
        _session: Snowflake Snowpark session
        stage_path: Full stage path (e.g., 'model_stage/raw/deeppcb/group00041/...')
        local_dir: Local directory to download to
    
    Returns:
        Local file path of downloaded image
    """
    import os
    
    os.makedirs(local_dir, exist_ok=True)
    
    # Extract just the stage reference part
    # stage_path format: "model_stage/raw/deeppcb/group00041/00041/00041001_temp.jpg"
    # We need: "@MODEL_STAGE/raw/deeppcb/group00041/00041/00041001_temp.jpg"
    if stage_path.startswith("model_stage/"):
        stage_ref = "@MODEL_STAGE/" + stage_path[len("model_stage/"):]
    else:
        stage_ref = stage_path
    
    # Download the file
    _session.file.get(stage_ref, local_dir)
    
    # Return the local path
    filename = os.path.basename(stage_path)
    return os.path.join(local_dir, filename)

