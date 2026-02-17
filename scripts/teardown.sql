-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- ============================================================================
-- PCB Defect Detection with YOLOv12 - Teardown Script
-- ============================================================================
-- Run this script to clean up all objects created by the setup script.
-- WARNING: This will permanently delete all data and objects!
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. Drop Streamlit App
-- ============================================================================
DROP STREAMLIT IF EXISTS PCB_CV.PUBLIC.PCB_DEFECT_DETECTION_APP;

-- ============================================================================
-- 2. Drop Notebook
-- ============================================================================
DROP NOTEBOOK IF EXISTS PCB_CV.PUBLIC.PCB_DEFECT_DETECTION_YOLO;

-- ============================================================================
-- 3. Drop Git Repository
-- ============================================================================
DROP GIT REPOSITORY IF EXISTS PCB_CV.PUBLIC.PCB_CV_REPO;

-- ============================================================================
-- 4. Drop Secret
-- ============================================================================
DROP SECRET IF EXISTS PCB_CV.PUBLIC.GITHUB_SECRET;

-- ============================================================================
-- 5. Drop Compute Pool
-- ============================================================================
DROP COMPUTE POOL IF EXISTS PCB_CV_COMPUTEPOOL;

-- ============================================================================
-- 6. Drop Database (includes all schemas, tables, stages, views, network rules)
-- ============================================================================
DROP DATABASE IF EXISTS PCB_CV;

-- ============================================================================
-- 7. Drop Warehouse
-- ============================================================================
DROP WAREHOUSE IF EXISTS PCB_CV_WH;

-- ============================================================================
-- 8. Drop Integrations
-- ============================================================================
DROP INTEGRATION IF EXISTS GITHUB_INTEGRATION_PCB_CV;
DROP INTEGRATION IF EXISTS allow_all_integration;

-- ============================================================================
-- 9. Drop Role
-- ============================================================================
DROP ROLE IF EXISTS PCB_CV_ROLE;

-- ============================================================================
-- Teardown Complete
-- ============================================================================
SELECT 'Teardown complete! All PCB CV objects have been removed.' AS STATUS;
