import streamlit as st
import pandas as pd
import os
import sys
import signal
from PIL import Image

LIST_OF_VIEWS = ['SAX', '2ch', '3ch', '4ch', 'RVOT', 'LVOT', '2ch-RT', 'RVOT-T', 'SAX-atria', 'OTHER', 'Excluded']

if len(sys.argv) < 4:
    st.error("Input arguments missing")
    st.stop()

patient = sys.argv[1]
dst = sys.argv[2]
csv_path = sys.argv[3]

st.set_page_config(layout="wide", page_title="View Correction GUI", initial_sidebar_state="collapsed")

# CSS to reduce title spacing and hide Streamlit topbar
st.markdown(
    """
    <style>
    .title-container {margin-top: 6px; margin-bottom: 6px;}
    .title-container h3 {margin: 0; font-size: 1.5rem; font-weight:600;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Layout settings
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(f"<div class='title-container'><h3>View Correction GUI: {patient}</h3></div>", unsafe_allow_html=True)
with col2:
    st.write("")
    if st.button("SAVE VIEW PREDICTIONS", type="primary", use_container_width=True):
        # Save corrected views in csv
        st.session_state['df'].to_csv(csv_path, index=False)
        st.success("Corrected views saved. You can close this browser tab.")
        
        # Terminate the streamlit server after saving to resume pipeline
        os.kill(os.getpid(), signal.SIGTERM)

st.divider()

# Load csv in session state
if 'df' not in st.session_state:
    st.session_state['df'] = pd.read_csv(csv_path)

df = st.session_state['df']

unsorted_img_dir = os.path.join(dst, 'view-classification', 'unsorted')
all_imgs = [f for f in os.listdir(unsorted_img_dir) if f.endswith('_0.png')]

# Get list of all pngs
all_imgs = os.listdir(unsorted_img_dir)
# Format as full paths
all_imgs = [os.path.join(unsorted_img_dir, i) for i in all_imgs if i.endswith('_0.png')]

# Creating grid
num_cols = 8 
cols = st.columns(num_cols)

for index, img_path in enumerate(all_imgs):
    series = list(os.path.basename(img_path).split('_'))
    series = int(series[0])  # Get the series number from the filename
    # Find dataframe row
    row_matches = df.index[df['Series Number'] == series].tolist()
    if not row_matches:
        continue
    row_idx = row_matches[0]

    # Extract all original metadata
    current_view = df.at[row_idx, 'Predicted View']
    confidence = df.at[row_idx, 'Confidence']
    description = df.at[row_idx, 'Series Description']
    location = df.at[row_idx, 'Slice Location']
    frames = df.at[row_idx, 'Frames Per Slice']

    if confidence < 0.66:
        color = 'red'
    else:
        color = 'green'

    with cols[index % num_cols]:
        # Show image in grid
        img = Image.open(img_path)
        st.image(img, width="stretch")

        #Hovertip
        tooltip_text = f"Series {series}&#10;Confidence: {confidence:.2f}&#10;Description: {description}&#10;Location: {location:.2f}&#10;Frames: {frames}"
        
        st.markdown(f"""
        <div style='font-size:0.85em; line-height:1.2; margin-bottom:5px;'>
            <b>Series: {series}</b> | <span style='color:{color}'>Conf: {confidence:.2f}</span><br>
            <span title="{tooltip_text}" style='color:gray; cursor:help; border-bottom: 1px dotted gray;'>
                Info Slice (Hover)
            </span>
        </div>
        """, unsafe_allow_html=True)

        default_index = LIST_OF_VIEWS.index(current_view) if current_view in LIST_OF_VIEWS else 0

        # Callback to update csv in session state
        def update_df(r_idx, widget_key):
            st.session_state['df'].at[r_idx, 'Predicted View'] = st.session_state[widget_key]

        widget_key = f"select_{series}"
        st.selectbox(
            "View",
            options=LIST_OF_VIEWS,
            index=default_index,
            key=widget_key,
            label_visibility="collapsed",
            on_change=update_df,
            args=(row_idx, widget_key)
        )
        st.write("---")