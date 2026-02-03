import streamlit as st
import pandas as pd
import requests
import plotly
from io import StringIO

# --- CONFIGURATION ---
GITHUB_REPO_URL = "https://raw.githubusercontent.com/hardik5838/NILM/main/data/"
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



def load_from_local(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error reading local file: {e}")
        return None


def clean_and_process_data(df):
    df['time'] = pd.to_datetime(df['time'], errors='coerce') 
    # This fills gaps using interpolation 
    df = df.sort_values('time')
    df['energy consumption'] = df['energy consumption'].interpolate(method='linear')
    df['temprature'] = df['temprature'].interpolate(method='linear')
    return df
