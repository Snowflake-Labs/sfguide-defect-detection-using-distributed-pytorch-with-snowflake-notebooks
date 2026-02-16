
-- ============================================================================
-- PCB Defect Detection with YOLOv12 - Setup Script
-- ============================================================================
USE ROLE ACCOUNTADMIN;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;

-- Set query tag for tracking
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"pcb_defect_detection","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ============================================================================
-- 1. Create Role and Grant Account-Level Permissions
-- ============================================================================
CREATE OR REPLACE ROLE PCB_CV_ROLE;
GRANT ROLE PCB_CV_ROLE TO ROLE ACCOUNTADMIN;
GRANT ROLE PCB_CV_ROLE TO USER identifier($USERNAME);

GRANT CREATE DATABASE ON ACCOUNT TO ROLE PCB_CV_ROLE;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE PCB_CV_ROLE;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE PCB_CV_ROLE;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE PCB_CV_ROLE;
GRANT CREATE INTEGRATION ON ACCOUNT TO ROLE PCB_CV_ROLE;

-- ============================================================================
-- 2. Create Database, Warehouse, and Schema
-- ============================================================================
CREATE OR REPLACE WAREHOUSE PCB_CV_WH
    WAREHOUSE_SIZE = MEDIUM
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

CREATE OR REPLACE DATABASE PCB_CV;
CREATE OR REPLACE SCHEMA PCB_CV.PUBLIC;

-- ============================================================================
-- 3. Create Network Rule (DO THIS BEFORE TRANSFERRING OWNERSHIP)
-- ============================================================================
-- This must be done while ACCOUNTADMIN still owns the PUBLIC schema
-- Network rule: 0.0.0.0 wildcards allow all outbound traffic on ports 443/80
CREATE OR REPLACE NETWORK RULE PCB_CV.PUBLIC.allow_all_rule
    TYPE = 'HOST_PORT'
    MODE = 'EGRESS'
    VALUE_LIST = ('0.0.0.0:443', '0.0.0.0:80')
    COMMENT = 'Allow all outbound HTTPS/HTTP traffic for external package installs';

-- ============================================================================
-- 4. Grant Privileges and Transfer Ownership
-- ============================================================================
-- Warehouse grants and ownership
GRANT USAGE ON WAREHOUSE PCB_CV_WH TO ROLE PCB_CV_ROLE;
GRANT OWNERSHIP ON WAREHOUSE PCB_CV_WH TO ROLE PCB_CV_ROLE COPY CURRENT GRANTS;

-- Database grants (but NOT ownership yet - need to grant on schema first)
GRANT ALL PRIVILEGES ON DATABASE PCB_CV TO ROLE PCB_CV_ROLE;

-- Schema grants (BEFORE any ownership transfer)
GRANT ALL PRIVILEGES ON SCHEMA PCB_CV.PUBLIC TO ROLE PCB_CV_ROLE;



-- ============================================================================
-- 5. Create Integrations 
-- ============================================================================
-- External Access Integration 
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION allow_all_integration
    ALLOWED_NETWORK_RULES = (PCB_CV.PUBLIC.allow_all_rule)
    ENABLED = true;

GRANT USAGE ON INTEGRATION allow_all_integration TO ROLE PCB_CV_ROLE;

-- Git API Integration (public repo - no authentication needed)
CREATE OR REPLACE API INTEGRATION GITHUB_INTEGRATION_PCB_CV
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/')
    ENABLED = TRUE;

GRANT USAGE ON INTEGRATION GITHUB_INTEGRATION_PCB_CV TO ROLE PCB_CV_ROLE;

-- ============================================================================
-- 6. Transfer Ownership 
-- ============================================================================
GRANT OWNERSHIP ON SCHEMA PCB_CV.PUBLIC TO ROLE PCB_CV_ROLE COPY CURRENT GRANTS;
GRANT OWNERSHIP ON DATABASE PCB_CV TO ROLE PCB_CV_ROLE COPY CURRENT GRANTS;

-- Grant privileges to ACCOUNTADMIN 
GRANT USAGE ON DATABASE PCB_CV TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON DATABASE PCB_CV TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE PCB_CV TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE PCB_CV TO ROLE ACCOUNTADMIN;

-- ============================================================================
-- 7. Switch to PCB_CV_ROLE and Create Remaining Objects
-- ============================================================================
USE ROLE PCB_CV_ROLE;
USE WAREHOUSE PCB_CV_WH;
USE DATABASE PCB_CV;
USE SCHEMA PUBLIC;

-- Create Git Repository
CREATE OR REPLACE GIT REPOSITORY PCB_CV_REPO
    API_INTEGRATION = GITHUB_INTEGRATION_PCB_CV
    ORIGIN = 'https://github.com/sfc-gh-dshemsi/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks.git';

ALTER GIT REPOSITORY PCB_CV_REPO FETCH;

-- Grant Git repository access to ACCOUNTADMIN for pipeline compatibility
USE ROLE ACCOUNTADMIN;
GRANT READ ON GIT REPOSITORY PCB_CV.PUBLIC.PCB_CV_REPO TO ROLE ACCOUNTADMIN;
USE ROLE PCB_CV_ROLE;

-- Stage for YOLOv12 model and raw images
CREATE OR REPLACE STAGE MODEL_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Stage for YOLOv12 models, weights, and raw PCB images';

-- ============================================================================
-- 8. Create Compute Pool
-- ============================================================================
-- GPU compute pool for YOLOv12 training
CREATE COMPUTE POOL IF NOT EXISTS PCB_CV_COMPUTEPOOL
    MIN_NODES = 3
    MAX_NODES = 3
    INSTANCE_FAMILY = GPU_NV_M
    AUTO_SUSPEND_SECS = 600
    COMMENT = 'GPU compute pool for YOLOv12 PCB defect detection training';

USE ROLE ACCOUNTADMIN;
GRANT OWNERSHIP ON COMPUTE POOL PCB_CV_COMPUTEPOOL TO ROLE PCB_CV_ROLE COPY CURRENT GRANTS;
GRANT USAGE, MONITOR ON COMPUTE POOL PCB_CV_COMPUTEPOOL TO ROLE ACCOUNTADMIN;
USE ROLE PCB_CV_ROLE;

-- ============================================================================
-- 9. Create Tables
-- ============================================================================
-- PCB Metadata: Tracks individual PCB boards (for dashboard)
CREATE OR REPLACE TABLE PCB_METADATA (
    BOARD_ID VARCHAR(50) NOT NULL,
    MANUFACTURING_DATE TIMESTAMP_NTZ,
    FACTORY_LINE_ID VARCHAR(50),
    PRODUCT_TYPE VARCHAR(100),
    IMAGE_PATH VARCHAR(500),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_PCB_METADATA PRIMARY KEY (BOARD_ID)
) COMMENT = 'Metadata for PCB boards processed through defect detection';

-- Defect Logs: Stores inference results from YOLOv12
CREATE OR REPLACE TABLE DEFECT_LOGS (
    INFERENCE_ID VARCHAR(36) NOT NULL,
    BOARD_ID VARCHAR(50),
    INFERENCE_TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    DETECTED_CLASS VARCHAR(50) NOT NULL,
    CONFIDENCE_SCORE FLOAT,
    BBOX_X_CENTER FLOAT,
    BBOX_Y_CENTER FLOAT,
    BBOX_WIDTH FLOAT,
    BBOX_HEIGHT FLOAT,
    IMAGE_PATH VARCHAR(500),
    MODEL_VERSION VARCHAR(50),
    CONSTRAINT PK_DEFECT_LOGS PRIMARY KEY (INFERENCE_ID)
) COMMENT = 'Inference results from YOLOv12 defect detection model';

-- Create clustering for common query patterns
ALTER TABLE DEFECT_LOGS CLUSTER BY (DETECTED_CLASS, INFERENCE_TIMESTAMP);

-- Grant all objects to ACCOUNTADMIN for pipeline/deploying user access
USE ROLE ACCOUNTADMIN;
GRANT ALL ON ALL TABLES IN SCHEMA PCB_CV.PUBLIC TO ROLE ACCOUNTADMIN;
GRANT ALL ON ALL VIEWS IN SCHEMA PCB_CV.PUBLIC TO ROLE ACCOUNTADMIN;
GRANT ALL ON ALL STAGES IN SCHEMA PCB_CV.PUBLIC TO ROLE ACCOUNTADMIN;
GRANT ALL ON FUTURE TABLES IN SCHEMA PCB_CV.PUBLIC TO ROLE ACCOUNTADMIN;
GRANT ALL ON FUTURE VIEWS IN SCHEMA PCB_CV.PUBLIC TO ROLE ACCOUNTADMIN;
USE ROLE PCB_CV_ROLE;

-- ============================================================================
-- 11. Insert Sample PCB Metadata (for demo dashboard)
-- ============================================================================
INSERT INTO PCB_METADATA (BOARD_ID, MANUFACTURING_DATE, FACTORY_LINE_ID, PRODUCT_TYPE)
SELECT 
    'PCB_' || SEQ4() AS BOARD_ID,
    DATEADD('HOUR', -UNIFORM(0, 720, RANDOM()), CURRENT_TIMESTAMP()) AS MANUFACTURING_DATE,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'SHANGHAI_L1'
        WHEN 2 THEN 'SHANGHAI_L2'
        WHEN 3 THEN 'SHENZHEN_L1'
        ELSE 'AUSTIN_L1'
    END AS FACTORY_LINE_ID,
    CASE UNIFORM(1, 3, RANDOM())
        WHEN 1 THEN 'CONSUMER_ELECTRONICS'
        WHEN 2 THEN 'AUTOMOTIVE'
        ELSE 'INDUSTRIAL'
    END AS PRODUCT_TYPE
FROM TABLE(GENERATOR(ROWCOUNT => 100));

-- ============================================================================
-- 12. Download Pretrained YOLO Weights to Stage
-- ============================================================================
-- Stored procedure to download yolo12n.pt from Ultralytics releases

CREATE OR REPLACE PROCEDURE DOWNLOAD_YOLO_WEIGHTS()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('snowflake-snowpark-python', 'requests')
EXTERNAL_ACCESS_INTEGRATIONS = (allow_all_integration)
HANDLER = 'main'
AS
$$
import requests
import os

def main(session):
    # YOLOv12n weights URL from Ultralytics releases
    url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo12n.pt"
    local_path = "/tmp/yolo12n.pt"
    
    # Download weights
    print(f"Downloading yolo12n.pt from {url}...")
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    file_size = os.path.getsize(local_path)
    print(f"Downloaded {file_size / 1e6:.1f} MB")
    
    # Upload to stage
    session.file.put(local_path, "@MODEL_STAGE/weights/", auto_compress=False, overwrite=True)
    
    return f"Uploaded yolo12n.pt ({file_size / 1e6:.1f} MB) to @MODEL_STAGE/weights/"
$$;

-- Download and cache the pretrained weights
CALL DOWNLOAD_YOLO_WEIGHTS();

-- ============================================================================
-- 14. Create Notebook from Git Repository
-- ============================================================================
CREATE OR REPLACE NOTEBOOK PCB_DEFECT_DETECTION
    FROM '@PCB_CV_REPO/branches/main'
    MAIN_FILE = 'notebooks/pcb_defect_detection.ipynb'
    QUERY_WAREHOUSE = PCB_CV_WH
    COMPUTE_POOL = PCB_CV_COMPUTEPOOL
    RUNTIME_NAME = 'SYSTEM$GPU_RUNTIME'
    IDLE_AUTO_SHUTDOWN_TIME_SECONDS = 3600
    COMMENT = '{"origin":"sf_sit-is", "name":"pcb_defect_detection", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"notebook"}}';

ALTER NOTEBOOK PCB_DEFECT_DETECTION ADD LIVE VERSION FROM LAST;
ALTER NOTEBOOK PCB_DEFECT_DETECTION SET EXTERNAL_ACCESS_INTEGRATIONS = ('allow_all_integration');

-- ============================================================================
-- 15. Create Streamlit App from Git Repository
-- ============================================================================
CREATE OR REPLACE STREAMLIT PCB_DEFECT_DETECTION_APP
    FROM '@PCB_CV_REPO/branches/main/streamlit'
    MAIN_FILE = 'app.py'
    QUERY_WAREHOUSE = PCB_CV_WH
    TITLE = 'PCB Defect Detection'
    COMMENT = '{"origin":"sf_sit-is", "name":"pcb_defect_detection", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"streamlit"}}';

ALTER STREAMLIT PCB_DEFECT_DETECTION_APP ADD LIVE VERSION FROM LAST;
ALTER STREAMLIT PCB_DEFECT_DETECTION_APP SET EXTERNAL_ACCESS_INTEGRATIONS = ('allow_all_integration');

-- Grant usage on the Streamlit app
GRANT USAGE ON STREAMLIT PCB_DEFECT_DETECTION_APP TO ROLE PCB_CV_ROLE;

-- Grant streamlit access to ACCOUNTADMIN
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON STREAMLIT PCB_CV.PUBLIC.PCB_DEFECT_DETECTION_APP TO ROLE ACCOUNTADMIN;

SELECT 'Setup Complete' AS STATUS;