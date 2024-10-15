import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.ml.registry import Registry
from page_helper import get_image
import snowflake.snowpark.functions as F
import json
import altair as alt
import pandas as pd
import time
import base64
import io
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import threading
import zipfile
import fcntl
import numpy as np

session = get_active_session()

# Configure Streamlit layout
st.set_page_config(layout="wide")

st.image(get_image("snowflakelogo/logo-sno-blue.png"), width=100)
st.title(":blue[Computer Vision based Defect Detection and Classification]")
st.markdown("---")

image_filename = 'pcb.png'

# Create table for image landing in Snowflake 
session.sql(f"""
    CREATE TABLE IF NOT EXISTS IMAGES_LANDING (
        IMAGE_NAME VARCHAR(16777216),
        BASE64BYTES VARCHAR(16777216)
    )
""").collect()

# Display an image
mime_type = image_filename.split('.')[-1].lower()
with open(image_filename, "rb") as f:
    content_bytes = f.read()
content_b64encoded = base64.b64encode(content_bytes).decode()
image_string = f'data:image/{mime_type};base64,{content_b64encoded}'
st.image(image_string, width=500)

# Ensure the session state exists
if 'images_loaded' not in st.session_state:
    parent_directory = os.getcwd()
    zip_file_path = os.path.join(parent_directory, "detect.zip")
    extracted = os.path.join(parent_directory, "detect")

    class FileLock:
        def __enter__(self):
            self._lock = threading.Lock()
            self._lock.acquire()
            self._fd = open('/tmp/lockfile.LOCK', 'w+')
            fcntl.lockf(self._fd, fcntl.LOCK_EX)

        def __exit__(self, type, value, traceback):
            self._fd.close()
            self._lock.release()

    # Truncate the IMAGES_LANDING table
    session.sql(f"TRUNCATE TABLE IMAGES_LANDING").collect()

    # Extract the zip file containing images
    with FileLock():
        if not os.path.isdir(extracted):
            with zipfile.ZipFile(zip_file_path, 'r') as myzip:
                myzip.extractall(parent_directory)

    # Change to the extracted directory and process image files
    os.chdir(extracted)
    extracted_files = os.listdir()
    st.session_state.image_data = []  # Initialize image data storage

    for filename in extracted_files:
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            image_path = os.path.join(extracted, filename)
            with open(image_path, "rb") as image_file:
                image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                
            # Create a DataFrame and upload image data to Snowflake
            pdf_base64 = pd.DataFrame({
                'IMAGE_NAME': [filename],  
                'BASE64BYTES': [image_b64]
            })
            session.write_pandas(pdf_base64, 'IMAGES_LANDING', quote_identifiers=False, auto_create_table=True, overwrite=False)

            # Store image names and their base64 representations
            st.session_state.image_data.append({
                'IMAGE_NAME': filename,
                'BASE64BYTES': image_b64
            })

    # Clean up: Remove extracted files and directories
    for filename in extracted_files:
        os.remove(filename)
    os.rmdir(extracted)
    os.chdir(parent_directory)

    st.session_state.images_loaded = True  # Mark images as loaded

st.markdown("---")

st.markdown(":green[Choose an image file from the dropdown]")
image_df = pd.DataFrame(st.session_state.image_data)

if image_df.empty:
    st.write("No images available. Ingest data first")
else:
    imagesrc = st.selectbox("Image Name", image_df['IMAGE_NAME'], 0)
    
    filtered_row = image_df[image_df['IMAGE_NAME'] == imagesrc]
    selected_image_name = imagesrc
    if filtered_row.empty:
        st.write("Selected image not found.")
    else:
        selected_image = filtered_row.iloc[0]['BASE64BYTES']
        
        st.markdown("---")

        st.write(
            """
            Image Base64 encoding is a way to represent image data as a text string that can be easily stored and transmitted. 
            In this encoding, the binary image data is converted into a sequence of characters using a specific character set, which typically includes alphanumeric characters, plus a few special characters such as '+', '/', and '='.
            It's also used for data transmission in protocols like HTTP (for inline images) and in data URI schemes.
            """
        )
        
        img = f'data:image/jpg;base64,{selected_image}'
        st.markdown(":green[Raw Image]")
        st.image(img, width=500)

st.title(":blue[Defect Detection and Classification]")
if st.button("Click button to ingest images and carry inference using custom trained RCNN Object Detection PyTorch Model"):
    with st.spinner("Load custom trained model from Snowflake Model Registry"):            
        reg = Registry(session=session)
        m = reg.get_model("DEFECTDETECTIONMODEL")
        mv = m.version("GENTLE_DONKEY_4")

        filtered_row = image_df[image_df['IMAGE_NAME'] == imagesrc]
        base64_image = filtered_row.iloc[0]['BASE64BYTES']
        image_data_df = pd.DataFrame({'IMAGE_DATA': [base64_image]})

        remote_prediction = mv.run(image_data_df, function_name="predict")

        st.write(
            """
            The classes of defects are following :
            class_mapping = {
            0: "open",
            1: "short",
            2: "mousebite",
            3: "spur",
            4: "copper",
            5: "pin-hole"
            }
            """
        )

        classes_la = {
            0: "open",
            1: "short",
            2: "mousebite",
            3: "spur",
            4: "copper",
            5: "pin-hole"
        }

        # Combine the image data and remote prediction DataFrames
        combined_df = pd.concat([image_data_df, remote_prediction], axis=1)
        
        # Create a list to store data that will be written to a final DataFrame
        rows = []
        
        # Iterate through each row in the combined DataFrame
        for index, row in combined_df.iterrows():
            # Convert the 'output' column JSON string into a dictionary
            output_data = json.loads(row['output'])  # Convert JSON string to dict
        
            # Extract the boxes, labels, and scores from the JSON data
            if 'boxes' in output_data and 'labels' in output_data and 'scores' in output_data:
                boxes = output_data['boxes']
                labels = output_data['labels']
                scores = output_data['scores']
        
                # Decode the image data
                image_data = base64.b64decode(row['IMAGE_DATA'])
                image = Image.open(io.BytesIO(image_data)).convert("RGB")  # Convert to RGB
        
                # Limit to top 5 classes based on scores
                if len(scores) > 0:
                    # Create a DataFrame to manage boxes, labels, and scores
                    data = pd.DataFrame({
                        'box': boxes,
                        'label': labels,
                        'score': scores
                    })
        
                    # Get the top 5 entries based on scores
                    top_classes = data.nlargest(5, 'score')
        
                    # Extract the corresponding boxes, labels, and scores
                    top_boxes = top_classes['box'].tolist()
                    top_labels = top_classes['label'].tolist()
                    top_scores = top_classes['score'].tolist()
        
                    # Store each of the top 5 predictions as a separate row
                    for i in range(len(top_boxes)):
                        rows.append({ 
                            'filename':imagesrc,
                            'image_data': row['IMAGE_DATA'],  # Same image data for all 5 rows
                            'output': row['output'],  # JSON output from the model
                            'label': top_labels[i],  # Label for the specific box
                            'box': top_boxes[i],  # Bounding box coordinates
                            'score': top_scores[i]  # Score of the specific box
                        })
        
                    # Display the image with bounding boxes and labels
                    
                    img = image.convert("RGB")
                    img_np = np.array(img)
                
                    # Setup the plot
                    fig, ax = plt.subplots(figsize=(4, 4))
                    ax.imshow(img_np)
                
                    # Plot each bounding box with its corresponding label and score
                    for label, box, score in zip(top_labels, top_boxes, top_scores):
                        
                        xmin, ymin, xmax, ymax = box
                        
                        # Class label for the bounding box
                        class_label = classes_la[label]
                
                        # Create a Rectangle patch
                        rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, linewidth=2, edgecolor='r', facecolor='none')
                        ax.text(xmin, ymin, f"{class_label}: {score:.2f}", verticalalignment='top', color='red', fontsize=13, weight='bold')
                        ax.add_patch(rect)
                
                    plt.axis('off')  # Hide axis
                    st.pyplot(fig)
        
                else:
                    print("No scores available to limit to top 5.")
            else:
                print("Missing keys 'boxes', 'labels', or 'scores' in the output data.")
        
        # Create the final DataFrame with the collected rows (one row per label/box/score)
        final_df = pd.DataFrame(rows)
        
        # Write the DataFrame to the Snowflake table
        combined_spdf = session.create_dataframe(final_df)
       
        combined_spdf.write.save_as_table("DETECTION_OUTPUTS",mode="overwrite")
        s = session.sql(f""" create TABLE if not exists DETECTIONS (
        filename VARCHAR(16777216),
image_data VARCHAR(16777216),
output VARCHAR(16777216),
label NUMBER(38,0),
box VARIANT,
score FLOAT
); """).collect()
        a = session.sql(f""" INSERT INTO DETECTIONS (filename,image_data, output, label,box,score)
SELECT "filename","image_data", "output", "label","box","score"
FROM DETECTION_OUTPUTS WHERE "filename" = '{imagesrc}' """).collect()
        

            
        st.markdown("---")
        pd_df=session.table("DETECTIONS").to_pandas()
        st.write(pd_df)