# Defect detection using Distributed PyTorch with Snowflake Notebooks

## Overview

In this guide, we will perform  multiclass defect detection on PCB images using distributed PyTorch training across multiple nodes and workers within a Snowflake Notebook. This guide utilizes a pre-trained Faster R-CNN model with ResNet50 as the backbone from PyTorch, fine-tuned for the task. The trained model is logged in the Snowpark Model Registry for future use. Additionally, a Streamlit app is developed to enable real-time defect detection on new images, making inference accessible and user-friendly

## Step-By-Step Guide

For prerequisites, environment setup, step-by-step guide and instructions, please refer to the [QuickStart Guide]().
