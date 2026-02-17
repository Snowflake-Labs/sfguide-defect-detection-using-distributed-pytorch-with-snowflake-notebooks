[![Snowflake - Certified](https://img.shields.io/badge/Snowflake-Certified-2ea44f?style=for-the-badge&logo=snowflake)](https://developers.snowflake.com/solutions/)

# PCB Defect Detection for Electronics Manufacturing: Achieve Zero-Defect Quality with Snowflake

## Overview

This guide demonstrates end-to-end computer vision for manufacturing quality control using **YOLOv12** object detection on **Snowflake Container Runtime with GPU**. Train a state-of-the-art defect detection model using GPU-accelerated PyTorch on Snowflake's Container Runtime, log models to the Snowflake Model Registry, and visualize results in an interactive Streamlit dashboard—all within Snowflake.

**Use Case:** Detect and classify 6 types of PCB (Printed Circuit Board) defects: open circuits, shorts, mousebite, spur, copper defects, and pin-holes.

**Dataset:** [Deep PCB Dataset](https://github.com/tangsanli5201/DeepPCB) - 1,500 image pairs (template + defect images) with bounding box annotations.

## What You'll Learn

- **GPU-Accelerated Training**: Use `PyTorchDistributor` with Snowflake Container Runtime for GPU-accelerated YOLOv12 training
- **Model Registry**: Log trained models to Snowflake Model Registry for versioning and SQL-based inference
- **Computer Vision Pipeline**: Convert datasets to YOLO format, train with data augmentation, and perform batch inference
- **Streamlit Dashboards**: Build production-ready analytics dashboards with real-time quality metrics
- **Snowflake ML Ops**: Manage the full ML lifecycle (data → training → inference → visualization) in one platform

## What You'll Build

1. **GPU-Accelerated Training Pipeline**: YOLOv12 training notebook running on Snowflake Container Runtime with GPU compute
2. **Defect Detection Model**: Fine-tuned YOLOv12 model registered in Snowflake Model Registry
3. **Data Warehouse**: Structured tables (`DEFECT_LOGS`, `PCB_METADATA`) for tracking defects and board metadata
4. **Executive Dashboard**: Interactive Streamlit app with:
   - Real-time quality metrics (yield rate, defect rate, false positive rate)
   - Defect Pareto analysis and factory line performance heatmaps
   - Model confidence distribution charts
   - Recent detection timeline

## Repository Structure

```
.
├── scripts/
│   ├── setup.sql              # Infrastructure setup (database, compute pool, tables)
│   └── teardown.sql           # Cleanup script
├── notebooks/
│   └── 0_pcb_defect_detection_yolo.ipynb  # Training & inference notebook
├── streamlit/
│   ├── Executive_Overview.py  # Main dashboard page
│   ├── pages/
│   │   ├── 1_Vision_Lab.py    # Interactive defect analysis
│   │   └── 2_About.py         # Project documentation
│   └── utils/
│       ├── data_loader.py     # Data fetching utilities
│       └── query_registry.py  # SQL query registry
├── README.md
└── LEGAL.md
```

## Prerequisites

### Snowflake Requirements
- **Account Edition**: Enterprise or higher
- **Region**: AWS, Azure, or GCP with GPU support
- **Privileges**: `ACCOUNTADMIN` role or equivalent with:
  - `CREATE DATABASE`, `CREATE WAREHOUSE`, `CREATE COMPUTE POOL`
  - `CREATE INTEGRATION` (for external access and git)
  - `BIND SERVICE ENDPOINT`

## Step-by-Step Guide

### Step 1: Deploy Infrastructure

**1.1 Create a SQL Worksheet:**
- Navigate to **Projects > Workspaces** in Snowsight
- Click the **+** sign (top right)
- Select **Add File > SQL File**

**1.2 Copy the Setup Script:**
- Open [`scripts/setup.sql`](https://github.com/Snowflake-Labs/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks/blob/main/scripts/setup.sql)
- Copy the entire contents
- Paste into your new SQL worksheet

**1.3 Execute:**
- Click **Run All** button

**What this creates:**
- Database: `PCB_CV`
- Warehouse: `PCB_CV_WH` (MEDIUM, auto-suspend 5 min)
- Role: `PCB_CV_ROLE`
- Compute Pool: `PCB_CV_COMPUTEPOOL` (3x GPU_NV_M nodes)
- Git Repository: Connected to this GitHub repo
- Network Rules: External access for downloading datasets/packages
- Tables: `PCB_METADATA`, `DEFECT_LOGS`
- Stage: `MODEL_STAGE` for storing models and images
- Pretrained Weights: Downloads `yolo12n.pt` to stage

### Step 2: Run the Training Notebook

Navigate to: **Projects > Notebooks > PCB_DEFECT_DETECTION**

Click **"Run All"** or execute cells sequentially.

**What the Notebook Does:**

This notebook provides an end-to-end workflow for training and deploying a YOLOv12 defect detection model on Snowflake's Container Runtime:

- **Data Preparation**: Downloads the Deep PCB dataset (~600 MB) and converts annotations from template-based format to YOLO format with normalized bounding boxes
- **GPU-Accelerated Training**: Trains YOLOv12 on Snowflake's Container Runtime using PyTorchDistributor for GPU compute, with configurable epochs, batch size, and data augmentation
- **Model Persistence**: Saves trained weights to Snowflake stages and registers the model in Snowflake Model Registry for versioning and governance
- **Inference Pipeline**: Runs batch predictions on test images and writes structured results (defect class, confidence, bounding boxes) to the DEFECT_LOGS table for dashboard analytics

**Key Output:**
- Trained model: `@MODEL_STAGE/runs/detect/train/weights/best.pt`
- Model Registry: `PCB_CV.PUBLIC.YOLO_PCB_DETECTOR` (version 1)
- Inference logs: 100+ rows in `DEFECT_LOGS` table

### Step 3: Open the Streamlit Dashboard

Navigate to: **Projects > Streamlit > PCB_DEFECT_DETECTION_APP**

**Dashboard Pages:**

**Executive Overview**
- Yield Rate, Defect Rate, False Positive Rate KPIs
- Defect Pareto Analysis (which defects occur most)
- Factory Line Performance heatmap
- Recent detections timeline

**Vision Lab**
- Upload PCB images for real-time inference
- Interactive bounding box visualization
- Confidence score analysis
- Defect type filtering

**About**
- Project architecture diagram
- Model performance metrics
- Dataset information

## Key Features

### GPU Training with PyTorchDistributor

The notebook uses Snowflake's `PyTorchDistributor` for GPU-accelerated training:

```python
from snowflake.ml.modeling.pytorch import PyTorchDistributor

distributor = PyTorchDistributor(
    num_nodes=1,
    instance_family="GPU_NV_M"
)

# GPU-accelerated training on Snowflake Container Runtime
results = distributor.fit(train_function, args=[model_config])
```

**Benefits:**
- **No manual cluster setup**: Snowflake handles GPU infrastructure
- **Auto-scaling**: Compute pool manages GPU resources automatically
- **Fault tolerance**: Failed jobs are automatically retried
- **Cost efficiency**: Pay-per-second billing with auto-suspend

### Model Registry Integration

Log models to Snowflake Model Registry for versioning and governance:

```python
from snowflake.ml.registry import Registry

registry = Registry(session=session)

registry.log_model(
    model=yolo_model,
    model_name="YOLO_PCB_DETECTOR",
    version_name="v1",
    conda_dependencies=["ultralytics==8.3.0"],
    sample_input_data=sample_image
)
```

**Access the model:**
```python
model = registry.get_model("YOLO_PCB_DETECTOR").version("v1")
predictions = model.run(new_images)
```

## Cleanup

To remove all resources created by this guide, execute [`scripts/teardown.sql`](https://github.com/Snowflake-Labs/sfguide-defect-detection-using-distributed-pytorch-with-snowflake-notebooks/blob/main/scripts/teardown.sql). This will drop the database, warehouse, compute pool, role, and all integrations.

## Conclusion

You've built a production-ready computer vision pipeline for manufacturing quality control entirely in Snowflake:

- **GPU-accelerated training** - Trained YOLOv12 on Snowflake's Container Runtime with GPU compute  
- **Model versioning** - Logged models to Snowflake Model Registry  
- **Data warehouse** - Structured defect logs for analytics  
- **Executive dashboard** - Real-time quality metrics in Streamlit  
- **End-to-end ML Ops** - Data → Training → Inference → Visualization in one platform  

**Next Steps:**
- Customize the model for your manufacturing use case
- Integrate with your production line systems via Snowflake APIs
- Scale to multiple factories using Snowflake's data sharing

## Additional Resources

- [Snowflake ML Overview](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- [Snowflake Model Registry Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-ml/model-registry/overview)
- [Snowflake Container Runtime](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [YOLOv12 Documentation](https://docs.ultralytics.com/)
- [Deep PCB Dataset Paper](https://arxiv.org/abs/1902.06197)

---

**Built with:** Snowflake ML, YOLOv12, PyTorch, Streamlit

## License

Copyright (c) Snowflake Inc. All rights reserved.

The code in this repository is licensed under the Apache 2.0 License.
