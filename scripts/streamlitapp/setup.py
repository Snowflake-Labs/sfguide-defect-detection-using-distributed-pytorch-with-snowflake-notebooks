import streamlit as st
import snowflake.snowpark.functions as F
import json
from page_helper import get_image
import altair as alt
import pandas as pd
import time
import base64
import io
from io import BytesIO
from PIL import Image

session = st.session_state['snf_session']

connection_parameters = {
    "account": session.get_current_account(),    
    "role": session.get_current_role(),
    "warehouse": session.get_current_warehouse(),
    "database": session.get_current_database(),
    "schema": session.get_current_schema(),
} 
st.write(connection_parameters)

st.image(get_image("logo-sno-blue.png"), width=100)
st.title(":blue[Manufacturing - PCB Defect Detection and Classification - Setup]")

st.markdown("---")
image_filename = 'pcb.png'
mime_type = image_filename.split('.')[-1:][0].lower()        
with open(image_filename, "rb") as f:
    content_bytes = f.read()
content_b64encoded = base64.b64encode(content_bytes).decode()
image_string = f'data:image/{mime_type};base64,{content_b64encoded}'
st.image(image_string, width=500)

def display_connection_info():
    with st.expander("Snowflake Connection Information", expanded=True):
        c1, s1, c2, s2, c3, s3, c4, s4, c5 = st.columns([1, 0.1, 2.5, 0.1, 2.5, 0.1, 1, 0.1, 1])
        

        account = connection_parameters.get("account")
        with c1:            
            st.metric("Account", f"{account}")
        
        database = connection_parameters.get("database")
        
        with c2:
            st.metric("Database", f"{database}")

        schema = connection_parameters.get("schema")
        with c3:
            st.metric("Schema", f"{schema}")

        warehouse = connection_parameters.get("warehouse")
        with c4:
            st.metric("Warehouse", f"{warehouse}")

        role = connection_parameters.get("role")
        with c5:
            st.metric("Role", f"{role}")
    

display_connection_info()
st.markdown("---")

st.write("The demo uses the following functionality: Snowpark Container Services")

df_imgsrc = session.table("IMAGES_LANDING")
snf_df = df_imgsrc.select("IMAGE_NAME", "BASE64BYTES").distinct()
df = snf_df.to_pandas()
