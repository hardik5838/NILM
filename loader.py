import streamlit as st
import pandas as pd
import requests
import plotly
from io import StringIO
import os 

# --- CONFIGURATION ---
GITHUB_API_URL = "https://api.github.com/repos/hardik5838/NILM/contents/data"
GITHUB_REPO_URL = "https://raw.githubusercontent.com/hardik5838/NILM/main/data/"

def get_github_file_list():
    response = requests.get(GITHUB_API_URL)
    if response.status_code == 200:
        # Filter for files ending in .csv
        return [item['name'] for item in response.json() if item['name'].endswith('.csv')]
    return []

def load_from_github(file_name):
    if not file_name or not isinstance(file_name, str):
        st.error("Invalid file selection.")
        return None
    full_url = GITHUB_REPO_URL + file_name
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
    if df is None: # Safety check
        return None
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce') 
    # This fills gaps using interpolation 
    df = df.sort_values('Fecha')
    df['kWh'] = df['kWh'].interpolate(method='linear')
    df['Temp'] = df['Temp'].interpolate(method='linear')
    return df
