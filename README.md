[![Snowflake - Certified](https://img.shields.io/badge/Snowflake-Certified-2ea44f?style=for-the-badge&logo=snowflake)](https://developers.snowflake.com/solutions/)

# Defect detection using Distributed PyTorch with Snowflake Notebooks

## Overview

In this guide, we will perform multiclass defect detection on PCB images using distributed PyTorch training across multiple GPU nodes within a Snowflake Notebook. This guide utilizes YOLOv12, a state-of-the-art object detection model, fine-tuned on the Deep PCB dataset to detect 6 defect types (open, short, mousebite, spur, copper, pin-hole). The trained model is logged in the Snowflake Model Registry for SQL-based inference. Additionally, a Streamlit app provides an interactive dashboard for defect analytics and image analysis with bounding box visualization.

## Step-By-Step Guide

For prerequisites, environment setup, step-by-step guide and instructions, please refer to the [Developers Guide]().
