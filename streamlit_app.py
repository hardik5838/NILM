import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
import requests
from datetime import datetime, timedelta

import streamlit as st
from loader import load_from_github, load_from_local, clean_and_process_data

# 1. The Selection Button
source = st.sidebar.radio("Data Source", ["GitHub", "Local Disk"])

raw_data = None

# 2. The Dynamic Button
if source == "GitHub":
    files = ["data1.csv", "data2.csv", "data3.csv"]
    selected = st.sidebar.selectbox("Select File", files)
    if st.sidebar.button("Fetch from GitHub"):
        raw_data = load_from_github(selected)
else:
    uploaded = st.sidebar.file_uploader("Upload CSV", type="csv")
    if uploaded:
        raw_data = load_from_local(uploaded)

# 3. The Execution
if raw_data is not None:
    st.session_state['my_data'] = clean_and_process_data(raw_data)
    st.success("Data ready for analysis!")


# 1. Import the function from your analysis file
from analysis_file import run_analysis

# 2. Call it and capture the two things it returns
if 'my_data' in st.session_state:
    stats_df, hourly_curves = run_analysis()
    
    # 3. Display the results
    st.subheader("Monthly R-Values")
    st.write(stats_df)
    
    st.subheader("Energy Curves (Weekday vs Weekend)")
    st.line_chart(hourly_curves)
