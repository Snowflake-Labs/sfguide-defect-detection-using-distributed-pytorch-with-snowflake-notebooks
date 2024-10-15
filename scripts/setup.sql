/*
Initial Setup - Run the following SQL commands  to create Snowflake objects (database, schema, tables).
*/
use role ACCOUNTADMIN;


create database PCB_DATASET;
create warehouse BUILD_WH WAREHOUSE_SIZE=SMALL;

use database PCB_DATASET;
use schema PUBLIC;
use warehouse BUILD_WH;

create compute pool NOTEBOOK_POOL
min_nodes = 1
max_nodes = 2
instance_family = GPU_NV_S
auto_suspend_secs = 7200;

create stage DATA_STAGE;

/*
Be sure to review and comply with the licensing terms and usage guidelines before utilizing the PCB dataset. Load the PCB Images from the external location into the Snowflake stage data_stage for training

- **Load Data into Snowflake**. -
The next step is to load the PCB dataset into a Snowflake stage.  The dataset can be accessed from [this](https://github.com/Charmve/Surface-Defect-Detection) link. 
*/

create or replace TABLE PCB_DATASET.PUBLIC.TRAIN_IMAGES_LABELS (
	FILENAME NUMBER(38,0),
	IMAGE_DATA VARCHAR(16777216),
	CLASS NUMBER(38,0),
	XMIN FLOAT,
	YMIN FLOAT,
	XMAX FLOAT,
	YMAX FLOAT
    );

-- End -- Follow Quickstart for rest of the instructions