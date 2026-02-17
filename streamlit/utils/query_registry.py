"""
Query Registry for PCB Defect Detection Dashboard

All SQL queries must be registered here for:
1. Independent testability via ./run.sh test
2. Fail-fast error handling
3. Centralized query management
"""

from typing import Dict, Optional
import pandas as pd

# Global registry of all queries
_QUERY_REGISTRY: Dict[str, dict] = {}


def register_query(
    name: str,
    sql: str,
    description: str,
    min_rows: int = 0
) -> str:
    """
    Register a SQL query for testing and execution.
    
    Args:
        name: Unique identifier for the query
        sql: SQL query string
        description: Human-readable description
        min_rows: Minimum expected rows (0 = no minimum)
    
    Returns:
        The SQL query string (for inline use)
    """
    _QUERY_REGISTRY[name] = {
        'sql': sql,
        'description': description,
        'min_rows': min_rows
    }
    return sql


def get_all_queries() -> Dict[str, dict]:
    """Return all registered queries."""
    return _QUERY_REGISTRY.copy()


def execute_query(session, query: str, name: str = "query") -> pd.DataFrame:
    """
    Execute a SQL query with fail-fast error handling.
    
    Args:
        session: Snowflake Snowpark session
        query: SQL query string
        name: Descriptive name for error messages
    
    Returns:
        DataFrame with query results
    
    Raises:
        RuntimeError: If query fails or returns None
    """
    try:
        result = session.sql(query).to_pandas()
        if result is None:
            raise RuntimeError(f"Query '{name}' returned None")
        return result
    except Exception as e:
        raise RuntimeError(f"Query '{name}' failed: {e}") from e


# =============================================================================
# REGISTERED QUERIES
# =============================================================================

# Defect Summary by Class
DEFECT_SUMMARY_SQL = register_query(
    "defect_summary",
    """
    SELECT 
        DETECTED_CLASS,
        COUNT(*) AS DEFECT_COUNT,
        AVG(CONFIDENCE_SCORE) AS AVG_CONFIDENCE,
        MIN(INFERENCE_TIMESTAMP) AS FIRST_DETECTED,
        MAX(INFERENCE_TIMESTAMP) AS LAST_DETECTED
    FROM DEFECT_LOGS
    GROUP BY DETECTED_CLASS
    ORDER BY DEFECT_COUNT DESC
    """,
    "Defect counts by class",
    min_rows=0
)

# Daily Defect Trends
DAILY_TRENDS_SQL = register_query(
    "daily_trends",
    """
    SELECT 
        DATE_TRUNC('DAY', INFERENCE_TIMESTAMP) AS DETECTION_DATE,
        DETECTED_CLASS,
        COUNT(*) AS DEFECT_COUNT,
        AVG(CONFIDENCE_SCORE) AS AVG_CONFIDENCE
    FROM DEFECT_LOGS
    GROUP BY DATE_TRUNC('DAY', INFERENCE_TIMESTAMP), DETECTED_CLASS
    ORDER BY DETECTION_DATE DESC
    LIMIT 100
    """,
    "Daily defect trends",
    min_rows=0
)

# Factory Line Performance
FACTORY_LINE_SQL = register_query(
    "factory_line_defects",
    """
    SELECT 
        COALESCE(m.FACTORY_LINE_ID, 'UNKNOWN') AS FACTORY_LINE_ID,
        d.DETECTED_CLASS,
        COUNT(*) AS DEFECT_COUNT,
        AVG(d.CONFIDENCE_SCORE) AS AVG_CONFIDENCE
    FROM DEFECT_LOGS d
    LEFT JOIN PCB_METADATA m ON d.BOARD_ID = m.BOARD_ID
    GROUP BY COALESCE(m.FACTORY_LINE_ID, 'UNKNOWN'), d.DETECTED_CLASS
    ORDER BY DEFECT_COUNT DESC
    """,
    "Defects by factory line",
    min_rows=0
)

# Total Defect Count
TOTAL_DEFECTS_SQL = register_query(
    "total_defects",
    """
    SELECT COUNT(*) AS TOTAL_DEFECTS FROM DEFECT_LOGS
    """,
    "Total defect count",
    min_rows=1
)

# Recent Defects
RECENT_DEFECTS_SQL = register_query(
    "recent_defects",
    """
    SELECT 
        INFERENCE_ID,
        BOARD_ID,
        DETECTED_CLASS,
        CONFIDENCE_SCORE,
        IMAGE_PATH,
        INFERENCE_TIMESTAMP
    FROM DEFECT_LOGS
    ORDER BY INFERENCE_TIMESTAMP DESC
    LIMIT 50
    """,
    "Recent defect detections",
    min_rows=0
)

# PCB Metadata Count
PCB_COUNT_SQL = register_query(
    "pcb_count",
    """
    SELECT COUNT(*) AS TOTAL_PCBS FROM PCB_METADATA
    """,
    "Total PCB count",
    min_rows=1
)

# Observation Count (unique images inspected)
OBSERVATION_COUNT_SQL = register_query(
    "observation_count",
    """
    SELECT 
        COUNT(DISTINCT IMAGE_PATH) AS TOTAL_OBSERVATIONS,
        COUNT(DISTINCT BOARD_ID) AS UNIQUE_BOARDS
    FROM DEFECT_LOGS
    """,
    "Count of unique observations (images) with defects",
    min_rows=1
)


# Sample Image per Defect Class (for examples)
DEFECT_EXAMPLES_SQL = register_query(
    "defect_examples",
    """
    SELECT DETECTED_CLASS, IMAGE_PATH, CONFIDENCE_SCORE,
           BBOX_X_CENTER, BBOX_Y_CENTER, BBOX_WIDTH, BBOX_HEIGHT
    FROM (
        SELECT DETECTED_CLASS, IMAGE_PATH, CONFIDENCE_SCORE,
               BBOX_X_CENTER, BBOX_Y_CENTER, BBOX_WIDTH, BBOX_HEIGHT,
               ROW_NUMBER() OVER (PARTITION BY DETECTED_CLASS ORDER BY CONFIDENCE_SCORE DESC) as rn
        FROM DEFECT_LOGS
    )
    WHERE rn = 1
    ORDER BY DETECTED_CLASS
    """,
    "One sample image per defect class with highest confidence",
    min_rows=0
)

# Confidence Score Distribution
CONFIDENCE_DISTRIBUTION_SQL = register_query(
    "confidence_distribution",
    """
    SELECT 
        DETECTED_CLASS,
        FLOOR(CONFIDENCE_SCORE * 10) / 10 AS CONF_BUCKET,
        COUNT(*) AS COUNT
    FROM DEFECT_LOGS
    GROUP BY DETECTED_CLASS, FLOOR(CONFIDENCE_SCORE * 10) / 10
    ORDER BY DETECTED_CLASS, CONF_BUCKET
    """,
    "Confidence score distribution by defect class",
    min_rows=0
)

# Images with Defect Summary (for smart picker)
IMAGES_WITH_DEFECTS_SQL = register_query(
    "images_with_defects",
    """
    SELECT 
        IMAGE_PATH,
        COUNT(*) AS DEFECT_COUNT,
        LISTAGG(DISTINCT DETECTED_CLASS, ', ') WITHIN GROUP (ORDER BY DETECTED_CLASS) AS DEFECT_TYPES,
        AVG(CONFIDENCE_SCORE) AS AVG_CONFIDENCE
    FROM DEFECT_LOGS
    GROUP BY IMAGE_PATH
    ORDER BY DEFECT_COUNT DESC
    """,
    "Images grouped by defect count and types",
    min_rows=0
)


def get_image_defects_sql(image_filename: str) -> str:
    """
    Generate SQL to query defects for a specific image.
    
    Args:
        image_filename: The filename (e.g., '00041001_temp.jpg')
    
    Returns:
        SQL query string
    """
    return f"""
    SELECT 
        DETECTED_CLASS,
        CONFIDENCE_SCORE,
        BBOX_X_CENTER,
        BBOX_Y_CENTER,
        BBOX_WIDTH,
        BBOX_HEIGHT,
        BOARD_ID,
        INFERENCE_TIMESTAMP
    FROM DEFECT_LOGS
    WHERE IMAGE_PATH LIKE '%{image_filename}'
    ORDER BY CONFIDENCE_SCORE DESC
    """


def get_ground_truth_sql(image_filename: str) -> str:
    """
    Generate SQL to query ground truth labels for a specific image.
    
    Args:
        image_filename: The filename (e.g., '00041001_temp.jpg')
    
    Returns:
        SQL query string
    """
    return f"""
    SELECT FILENAME, LABEL_TEXT
    FROM PCB_LABELED_DATA
    WHERE FILENAME = '{image_filename}'
    """

