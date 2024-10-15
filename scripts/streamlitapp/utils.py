import streamlit as st
import snowflake.snowpark.functions as F
import json
import logging ,sys ,os 
from pathlib import Path
from page_helper import get_image
import altair as alt
import pandas as pd
import time
import base64
import io
from io import BytesIO
from PIL import Image

logger = logging.getLogger('app')

session = st.session_state['snf_session']

# Import the commonly defined utility scripts using
# dynamic path include
import sys


def load_sample_and_display_table(p_table: str ,p_sample_rowcount :int):
    '''
    Utility function to display sample records 
    '''
    st.write(f'sampling target table {p_table} ...')
    tbl_df = (session
        .table(p_table)
        .sample(n=p_sample_rowcount)
        .to_pandas())

    st.dataframe(tbl_df ,use_container_width=True)
    st.write(f'')


def list_stage(p_stage :str):
    '''
    Utility function to display contents of a stage
    '''
    rows = session.sql(f''' list @{p_stage}; ''').collect()
    data = []
    for r in rows:
        data.append({
            'name': r['name']
            ,'size': r['size']
            ,'last_modified': r['last_modified']
        })

    df = pd.json_normalize(data)
    return df

def exec_python_script(p_pyscript: str ,p_cache_id) -> bool:
    '''
        Executes a python script and writes the output to a textbox.
    '''
    script_executed = False
    logger.info(f'Executing python script: {p_pyscript} ...')
    # Capture script output.
    script_output = []
    process = subprocess.Popen(
        ['python'
        ,p_pyscript]
        ,stdout=subprocess.PIPE
        ,universal_newlines=True)

    while True:
        output = process.stdout.readline()
        script_output.append(output)
        return_code = process.poll()
        
        if return_code is not None:
            script_output.append(f'RETURN CODE: {return_code} \n')
            script_executed = True

            # Process has finished, read rest of the output 
            for output in process.stdout.readlines():
                script_output.append(output)

            break

    script_output.append('\n --- Finished executing script ---')
    st.session_state[p_cache_id] = script_output

    return script_executed