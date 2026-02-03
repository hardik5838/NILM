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
