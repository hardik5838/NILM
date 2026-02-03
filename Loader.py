import streamlit as st
import pandas as pd
import requests
import plotly
from io import StringIO

# --- CONFIGURATION ---
GITHUB_REPO_URL = "https://raw.githubusercontent.com/hardik5838/NILM/tree/main/data/"

def load_from_github(file_name):
    base_url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/data/"
    full_url = base_url + file_name
    response = requests.get(full_url)
    if response.status_code == 200:
        data = StringIO(response.text)
        df = pd.read_csv(data)
        return df
    else:
        st.error("Could not find the file on GitHub!")
        return None
    pass



def load_from_local(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error reading local file: {e}")
        return None
    pass



def clean_and_process_data(df):
    """
    CORE MATH TASK:
    1. Convert 'time' column to datetime.
    2. Filter for the 3-year range.
    3. Handle missing values (NaNs).
    4. Return the cleaned dataframe.
    """
    # Your logic goes here
    return df
